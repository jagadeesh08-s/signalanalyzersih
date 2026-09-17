"""Tests for demodulator functions."""
import numpy as np
import pytest

from app.demodulation.demodulator import (
    demodulate_bpsk,
    demodulate_qpsk,
    demodulate_fsk,
    demodulate,
    bits_to_bytes,
    bytes_to_hex,
    bytes_to_ascii,
)


class TestDemodulator:
    """Test demodulation functions."""

    def setup_method(self):
        """Generate test signals."""
        np.random.seed(42)
        self.sample_rate = 1_000_000
        self.symbol_rate = 100_000
        self.sps = int(self.sample_rate / self.symbol_rate)  # 10 samples per symbol

    def generate_bpsk(self, n_symbols=1000, snr_db=20):
        """Generate BPSK signal."""
        symbols = np.random.choice([-1, 1], n_symbols)
        signal = np.repeat(symbols, self.sps)
        signal = signal + 1j * np.zeros_like(signal)
        
        # Add noise
        signal_power = np.mean(np.abs(signal) ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.sqrt(noise_power / 2) * (np.random.randn(len(signal)) + 1j * np.random.randn(len(signal)))
        
        return signal + noise

    def generate_qpsk(self, n_symbols=1000, snr_db=20):
        """Generate QPSK signal."""
        symbols = np.random.choice([1+1j, -1+1j, -1-1j, 1-1j], n_symbols) / np.sqrt(2)
        signal = np.repeat(symbols, self.sps)
        
        # Add noise
        signal_power = np.mean(np.abs(signal) ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.sqrt(noise_power / 2) * (np.random.randn(len(signal)) + 1j * np.random.randn(len(signal)))
        
        return signal + noise

    def test_demodulate_bpsk(self):
        """Test BPSK demodulation."""
        signal = self.generate_bpsk(500, snr_db=20)
        result = demodulate_bpsk(signal, self.symbol_rate, self.sample_rate)
        
        assert 'bits' in result
        assert 'success' in result
        assert len(result['bits']) > 0

    def test_demodulate_qpsk(self):
        """Test QPSK demodulation."""
        signal = self.generate_qpsk(500, snr_db=20)
        result = demodulate_qpsk(signal, self.symbol_rate, self.sample_rate)
        
        assert 'bits' in result
        assert 'success' in result
        assert len(result['bits']) > 0

    def test_demodulate_fsk(self):
        """Test FSK demodulation."""
        # Generate simple FSK
        n_symbols = 200
        freq_sep = 50_000
        f1 = self.symbol_rate / 2 - freq_sep / 2
        f2 = self.symbol_rate / 2 + freq_sep / 2
        
        symbols = np.random.choice([0, 1], n_symbols)
        signal = np.zeros(n_symbols * self.sps, dtype=complex)
        
        for i, sym in enumerate(symbols):
            t = np.arange(self.sps) / self.sample_rate
            if sym == 0:
                signal[i*self.sps:(i+1)*self.sps] = np.exp(2j * np.pi * f1 * t)
            else:
                signal[i*self.sps:(i+1)*self.sps] = np.exp(2j * np.pi * f2 * t)
        
        # Add noise
        noise = 0.05 * (np.random.randn(len(signal)) + 1j * np.random.randn(len(signal)))
        signal = signal + noise
        
        result = demodulate_fsk(signal, self.symbol_rate, self.sample_rate)
        
        assert 'bits' in result
        assert 'success' in result

    def test_demodulate_main(self):
        """Test main demodulate function."""
        signal = self.generate_bpsk(200, snr_db=20)
        result = demodulate(signal, "BPSK", self.symbol_rate, self.sample_rate)
        
        assert 'success' in result
        assert 'modulation' in result
        assert 'bits' in result
        assert result['modulation'] == "BPSK"

    def test_bits_to_bytes(self):
        """Test bits to bytes conversion."""
        bits = [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0]
        bytes_data = bits_to_bytes(bits)
        
        assert len(bytes_data) == 2
        assert bytes_data[0] == 0xAA
        assert bytes_data[1] == 0xCC

    def test_bytes_to_hex(self):
        """Test bytes to hex conversion."""
        bytes_data = bytes([0xAA, 0xCC, 0x0F])
        hex_str = bytes_to_hex(bytes_data)
        
        assert hex_str == "AA CC 0F"

    def test_bytes_to_ascii(self):
        """Test bytes to ASCII conversion."""
        bytes_data = bytes([0x48, 0x65, 0x6C, 0x6C, 0x6F])  # "Hello"
        ascii_str = bytes_to_ascii(bytes_data)
        
        assert ascii_str == "Hello"

    def test_bytes_to_ascii_non_printable(self):
        """Test bytes to ASCII with non-printable chars."""
        bytes_data = bytes([0x01, 0x41, 0x02, 0x42])  # Non-printable + A + B
        ascii_str = bytes_to_ascii(bytes_data)
        
        assert ascii_str == ".A.B"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])