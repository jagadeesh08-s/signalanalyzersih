"""Tests for correlation analyzer."""
import numpy as np
import pytest

from app.correlation.analyzer import (
    cross_correlation,
    normalized_cross_correlation,
    compare_signals,
    find_signal_in_noise,
    auto_correlation,
    compute_coherence,
)


class TestCorrelation:
    """Test correlation analysis functions."""

    def setup_method(self):
        """Generate test signals."""
        np.random.seed(42)
        self.sample_rate = 1_000_000
        n = 10000
        self.signal1 = np.random.randn(n) + 1j * np.random.randn(n)

    def test_cross_correlation(self):
        """Test cross-correlation."""
        # Create signal2 as delayed version of signal1
        delay = 100
        signal2 = np.roll(self.signal1, delay)
        
        corr = cross_correlation(self.signal1, signal2)
        
        assert len(corr) == len(self.signal1)
        # Peak should be near the delay
        peak_idx = np.argmax(np.abs(corr))
        assert abs(peak_idx - delay) < 5 or abs(peak_idx - (len(corr) - delay)) < 5

    def test_normalized_cross_correlation(self):
        """Test normalized cross-correlation."""
        signal2 = np.roll(self.signal1, 50)
        
        corr = normalized_cross_correlation(self.signal1, signal2)
        
        assert len(corr) == len(self.signal1)
        assert np.max(np.abs(corr)) <= 1.0 + 1e-6

    def test_compare_signals(self):
        """Test signal comparison."""
        signal2 = np.roll(self.signal1, 25) + 0.1 * np.random.randn(len(self.signal1)) + 1j * 0.1 * np.random.randn(len(self.signal1))
        
        result = compare_signals(self.signal1, signal2, self.sample_rate)
        
        assert "similarity_score" in result
        assert "peak_correlation" in result
        assert "peak_lag" in result
        assert "time_offset_seconds" in result
        assert "mse" in result
        assert "spectral_similarity" in result
        
        assert 0 <= result["similarity_score"] <= 1
        assert result["mse"] >= 0

    def test_find_signal_in_noise(self):
        """Test finding signal in noise."""
        # Embed known signal in noise
        template = np.sin(2 * np.pi * 100_000 * np.arange(1000) / self.sample_rate)
        template = template + 1j * np.zeros_like(template)
        
        noise = 0.5 * (np.random.randn(10000) + 1j * np.random.randn(10000))
        signal = noise.copy()
        signal[2000:3000] += template
        
        result = find_signal_in_noise(signal, template, self.sample_rate)
        
        assert "found" in result
        assert "position" in result
        assert "correlation" in result

    def test_auto_correlation(self):
        """Test auto-correlation."""
        result = auto_correlation(self.signal1, max_lag=100)
        
        assert "correlation" in result
        assert "lags" in result
        assert len(result["correlation"]) == len(result["lags"])
        assert result["lags"][0] == 0

    def test_compute_coherence(self):
        """Test coherence computation."""
        # Create two related signals
        t = np.arange(10000) / self.sample_rate
        signal1 = np.sin(2 * np.pi * 100_000 * t) + 0.1 * np.random.randn(len(t))
        signal2 = np.sin(2 * np.pi * 100_000 * t + 0.5) + 0.1 * np.random.randn(len(t))
        
        signal1 = signal1 + 1j * np.zeros_like(signal1)
        signal2 = signal2 + 1j * np.zeros_like(signal2)
        
        result = compute_coherence(signal1, signal2, self.sample_rate)
        
        assert "coherence" in result
        assert "frequencies" in result
        assert len(result["coherence"]) == len(result["frequencies"])
        assert np.all(result["coherence"] >= 0)
        assert np.all(result["coherence"] <= 1.0 + 1e-6)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])