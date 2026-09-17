"""Tests for pipeline service."""
import numpy as np
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.services.pipeline import AnalysisPipeline


class TestAnalysisPipeline:
    """Test analysis pipeline."""

    def setup_method(self):
        """Create pipeline instance."""
        self.pipeline = AnalysisPipeline()

    def test_parse_file_iq(self):
        """Test parsing IQ file."""
        import tempfile
        import os
        
        # Create temporary IQ file
        n = 1000
        data = np.random.randn(n).astype(np.int16) + 1j * np.random.randn(n).astype(np.int16)
        # Interleave I/Q as int16
        iq_data = np.empty(2 * n, dtype=np.int16)
        iq_data[0::2] = np.real(data).astype(np.int16)
        iq_data[1::2] = np.imag(data).astype(np.int16)
        
        with tempfile.NamedTemporaryFile(suffix='.iq', delete=False) as f:
            f.write(iq_data.tobytes())
            temp_path = f.name
        
        try:
            iq_config = {
                "dtype": "int16",
                "iq_order": "IQ",
                "endianness": "little",
                "sample_rate": 1_000_000,
                "center_frequency": 0,
                "scale_factor": 1.0,
            }
            iq_result, metadata = self.pipeline._parse_file(temp_path, iq_config)
            
            assert len(iq_result) > 0
            assert metadata["sample_rate"] == 1_000_000
        finally:
            os.unlink(temp_path)

    def test_preprocess(self):
        """Test preprocessing."""
        iq_data = np.random.randn(1000) + 1j * np.random.randn(1000)
        iq_data = iq_data + 5 + 3j  # Add DC
        
        metadata = {"sample_rate": 1_000_000}
        config = {"dc_removal": True, "normalize": True}
        
        result = self.pipeline._preprocess(iq_data, metadata, config)
        
        # Check DC removed
        assert abs(np.mean(np.real(result))) < 0.1
        assert abs(np.mean(np.imag(result))) < 0.1
        
        # Check normalized
        rms = np.sqrt(np.mean(np.abs(result) ** 2))
        assert abs(rms - 1.0) < 0.1

    def test_extract_parameters(self):
        """Test parameter extraction."""
        iq_data = np.random.randn(10000) + 1j * np.random.randn(10000)
        metadata = {"sample_rate": 1_000_000, "center_frequency": 2.4e9}
        
        params = self.pipeline._extract_parameters(iq_data, metadata)
        
        assert len(params) > 0
        param_names = [p["parameter_name"] for p in params]
        assert "Sample Rate" in param_names
        assert "SNR" in param_names
        assert "Estimated Bandwidth (-3dB)" in param_names

    def test_classify_modulation(self):
        """Test modulation classification."""
        # Simple BPSK-like signal
        n = 5000
        symbols = np.random.choice([-1, 1], n)
        iq_data = symbols + 1j * np.zeros(n)
        iq_data = iq_data + 0.1 * (np.random.randn(n) + 1j * np.random.randn(n))
        
        metadata = {"sample_rate": 1_000_000}
        
        result = self.pipeline._classify_modulation(iq_data, metadata)
        
        assert "modulation" in result
        assert "confidence" in result
        assert "probabilities" in result
        assert "features" in result
        assert "method" in result

    def test_demodulate(self):
        """Test demodulation."""
        # Simple BPSK
        n_symbols = 200
        sps = 10
        symbols = np.random.choice([-1, 1], n_symbols)
        iq_data = np.repeat(symbols, sps) + 1j * np.zeros(n_symbols * sps)
        
        metadata = {"sample_rate": 1_000_000, "symbol_rate": 100_000}
        classification = {"modulation": "BPSK", "confidence": 0.9}
        
        result = self.pipeline._demodulate(iq_data, metadata, classification)
        
        assert "success" in result
        assert "bits" in result
        assert "modulation" in result

    def test_get_job_summary(self):
        """Test job summary generation."""
        # Set up pipeline with mock data
        self.pipeline.metadata = {
            "sample_rate": 1_000_000,
            "center_frequency": 2.4e9,
            "duration": 1.0,
            "num_samples": 1_000_000,
            "num_channels": 1,
            "dtype": "int16",
        }
        self.pipeline.classification = {
            "modulation": "QPSK",
            "confidence": 0.9,
            "probabilities": {"QPSK": 0.9, "BPSK": 0.1},
        }
        self.pipeline.parameters = [
            {"parameter_name": "SNR", "value": 15.0},
            {"parameter_name": "Estimated Bandwidth (-3dB)", "value": 100_000},
            {"parameter_name": "Estimated Symbol Rate", "value": 100_000},
            {"parameter_name": "Frequency Offset", "value": 1000},
        ]
        self.pipeline.demod_result = {
            "success": True,
            "bits": [1, 0] * 1000,
        }
        self.pipeline.iq_data = np.random.randn(1000) + 1j * np.random.randn(1000)
        
        summary = self.pipeline.get_job_summary()
        
        assert summary["detected_modulation"] == "QPSK"
        assert summary["modulation_confidence"] == 0.9
        assert summary["snr"] == 15.0
        assert summary["bandwidth"] == 100_000
        assert summary["symbol_rate"] == 100_000
        assert summary["demodulated"] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])