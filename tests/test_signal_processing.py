"""Tests for signal processing functions."""
import numpy as np
import pytest

from app.dsp.signal_processing import (
    parse_iq_file,
    parse_wav_file,
    auto_detect_format,
    remove_dc,
    normalize_signal,
    bandpass_filter,
    lowpass_filter,
    resample_signal,
    compute_snr,
    compute_bandwidth,
    estimate_symbol_rate,
    compute_psd,
    compute_spectrogram,
    downsample_for_visualization,
    extract_constellation_points,
)


class TestSignalProcessing:
    """Test DSP signal processing functions."""

    def setup_method(self):
        """Generate test signals."""
        np.random.seed(42)
        self.sample_rate = 1_000_000
        n = 10000
        self.iq_data = np.random.randn(n) + 1j * np.random.randn(n)

    def test_remove_dc(self):
        """Test DC removal."""
        data_with_dc = self.iq_data + 10 + 5j
        result = remove_dc(data_with_dc)
        
        assert abs(np.mean(np.real(result))) < 1e-10
        assert abs(np.mean(np.imag(result))) < 1e-10

    def test_normalize_signal(self):
        """Test signal normalization."""
        result = normalize_signal(self.iq_data, target_rms=1.0)
        
        rms = np.sqrt(np.mean(np.abs(result) ** 2))
        assert abs(rms - 1.0) < 1e-6

    def test_bandpass_filter(self):
        """Test bandpass filter."""
        # Create signal with known frequency components
        t = np.arange(10000) / self.sample_rate
        signal = np.sin(2 * np.pi * 100_000 * t) + 0.5 * np.sin(2 * np.pi * 300_000 * t)
        signal = signal + 1j * np.zeros_like(signal)
        
        result = bandpass_filter(signal, self.sample_rate, 50_000, 200_000)
        
        # Check that 100 kHz component is preserved, 300 kHz is attenuated
        assert len(result) == len(signal)

    def test_lowpass_filter(self):
        """Test lowpass filter."""
        result = lowpass_filter(self.iq_data, self.sample_rate, 200_000)
        assert len(result) == len(self.iq_data)

    def test_resample_signal(self):
        """Test resampling."""
        target_rate = 500_000
        result = resample_signal(self.iq_data, self.sample_rate, target_rate)
        
        expected_len = int(len(self.iq_data) * target_rate / self.sample_rate)
        assert abs(len(result) - expected_len) <= 1

    def test_compute_snr(self):
        """Test SNR computation."""
        snr = compute_snr(self.iq_data, self.sample_rate)
        
        assert isinstance(snr, float)
        assert -20 <= snr <= 60

    def test_compute_bandwidth(self):
        """Test bandwidth computation."""
        bw, low, high = compute_bandwidth(self.iq_data, self.sample_rate)
        
        assert isinstance(bw, float)
        assert bw >= 0
        assert low <= high

    def test_estimate_symbol_rate(self):
        """Test symbol rate estimation."""
        # Create signal with known symbol rate
        symbol_rate = 100_000
        sps = 10
        n_symbols = 1000
        t = np.arange(n_symbols * sps) / self.sample_rate
        symbols = np.repeat(np.random.choice([-1, 1], n_symbols), sps)
        signal = symbols + 1j * np.zeros_like(symbols)
        
        rate, conf = estimate_symbol_rate(signal, self.sample_rate, max_symbol_rate=200_000)
        
        assert isinstance(rate, float)
        assert 0 <= conf <= 1

    def test_compute_psd(self):
        """Test PSD computation."""
        freqs, psd_db = compute_psd(self.iq_data, self.sample_rate, nfft=1024)
        
        assert len(freqs) == len(psd_db)
        assert len(freqs) == 1024

    def test_compute_spectrogram(self):
        """Test spectrogram computation."""
        times, freqs, spec = compute_spectrogram(self.iq_data, self.sample_rate, nfft=256, hop=64)
        
        assert len(times) > 0
        assert len(freqs) == 256
        assert spec.shape == (256, len(times))

    def test_downsample_for_visualization(self):
        """Test downsampling for visualization."""
        long_signal = np.random.randn(50000) + 1j * np.random.randn(50000)
        result, info = downsample_for_visualization(long_signal, max_points=1000)
        
        assert len(result) <= 1000
        assert info['downsampled'] is True
        assert info['factor'] > 1

    def test_extract_constellation_points(self):
        """Test constellation point extraction."""
        # Create QPSK signal
        n_symbols = 500
        sps = 10
        symbols = np.random.choice([1+1j, -1+1j, -1-1j, 1-1j], n_symbols) / np.sqrt(2)
        signal = np.repeat(symbols, sps)
        signal = signal + 0.05 * (np.random.randn(len(signal)) + 1j * np.random.randn(len(signal)))
        
        result = extract_constellation_points(signal, samples_per_symbol=sps, num_symbols=1000)
        
        assert len(result) > 0
        assert len(result) <= 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])