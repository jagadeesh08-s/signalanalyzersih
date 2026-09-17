"""Tests for modulation classifier."""
import numpy as np
import pytest

from app.modulation.classifier import (
    extract_features,
    classify_modulation_hoc,
    classify_modulation,
    compute_occupied_bandwidth,
    estimate_symbol_rate,
    compute_snr,
    get_reference_constellation,
    normalize_constellation,
    MODULATION_CLASSES,
)


class TestClassifier:
    """Test modulation classification functions."""

    def setup_method(self):
        """Generate test signals."""
        np.random.seed(42)
        self.sample_rate = 1_000_000
        # Generate BPSK-like signal
        n = 10000
        symbols = np.random.choice([-1, 1], n)
        self.bpsk_signal = symbols + 1j * np.zeros(n)
        self.bpsk_signal = self.bpsk_signal + 0.1 * (np.random.randn(n) + 1j * np.random.randn(n))

    def test_extract_features(self):
        """Test feature extraction."""
        features = extract_features(self.bpsk_signal, self.sample_rate)
        
        assert isinstance(features, dict)
        assert 'mean_magnitude' in features
        assert 'cumulant_40' in features
        assert 'cumulant_42' in features
        assert 'snr' in features
        assert 'estimated_symbol_rate' in features
        assert 'spectral_centroid' in features

    def test_classify_modulation_hoc(self):
        """Test HoC classification."""
        features = extract_features(self.bpsk_signal, self.sample_rate)
        mod, confidence, probs = classify_modulation_hoc(features)
        
        assert mod in MODULATION_CLASSES
        assert 0 <= confidence <= 1
        assert set(probs.keys()) == set(MODULATION_CLASSES)
        assert abs(sum(probs.values()) - 1.0) < 1e-6

    def test_classify_modulation(self):
        """Test main classification entry point."""
        result = classify_modulation(self.bpsk_signal, self.sample_rate)
        
        assert 'modulation' in result
        assert 'confidence' in result
        assert 'probabilities' in result
        assert 'features' in result
        assert 'method' in result
        assert result['modulation'] in MODULATION_CLASSES

    def test_compute_occupied_bandwidth(self):
        """Test bandwidth computation."""
        bw, low, high = compute_occupied_bandwidth(self.bpsk_signal, self.sample_rate, -20)
        
        assert isinstance(bw, float)
        assert bw >= 0
        assert isinstance(low, float)
        assert isinstance(high, float)

    def test_estimate_symbol_rate(self):
        """Test symbol rate estimation."""
        rate, conf = estimate_symbol_rate(self.bpsk_signal, self.sample_rate)
        
        assert isinstance(rate, float)
        assert rate >= 0
        assert 0 <= conf <= 1

    def test_compute_snr(self):
        """Test SNR computation."""
        snr = compute_snr(self.bpsk_signal, self.sample_rate)
        
        assert isinstance(snr, float)
        assert -20 <= snr <= 60

    def test_get_reference_constellation(self):
        """Test reference constellation retrieval."""
        for mod in MODULATION_CLASSES:
            const = get_reference_constellation(mod)
            if mod in ['BPSK', 'QPSK', '8PSK', '16QAM', '64QAM']:
                assert len(const) > 0
            else:
                assert len(const) == 0

    def test_normalize_constellation(self):
        """Test constellation normalization."""
        const = get_reference_constellation('QPSK')
        norm_const = normalize_constellation(const)
        
        avg_energy = np.mean(np.abs(norm_const) ** 2)
        assert abs(avg_energy - 1.0) < 1e-6

    def test_empty_constellation(self):
        """Test normalization of empty constellation."""
        empty = np.array([])
        result = normalize_constellation(empty)
        assert len(result) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])