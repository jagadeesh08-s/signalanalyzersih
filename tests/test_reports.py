"""Tests for reports generator."""
import json
import pytest
import numpy as np

from app.reports.generator import generate_report, SignalReportGenerator


class TestReportsGenerator:
    """Test report generation."""

    def setup_method(self):
        """Create sample job data."""
        self.job_data = {
            "id": 1,
            "filename": "test_signal.iq",
            "file_type": "iq",
            "file_size": 1024000,
            "sample_rate": 1_000_000,
            "center_frequency": 2.4e9,
            "duration": 1.0,
            "num_samples": 1_000_000,
            "num_channels": 1,
            "data_type": "int16",
            "detected_modulation": "QPSK",
            "modulation_confidence": 0.92,
            "modulation_probabilities": {
                "QPSK": 0.92, "BPSK": 0.04, "8PSK": 0.02,
                "16QAM": 0.01, "64QAM": 0.005, "FSK": 0.003,
                "AM": 0.001, "FM": 0.001, "ASK": 0.001
            },
            "snr": 18.5,
            "bandwidth": 125_000,
            "symbol_rate": 100_000,
            "frequency_offset": 1_234,
            "parameters": [
                {"parameter_name": "SNR", "value": 18.5, "unit": "dB", "confidence": 0.8, "source": "ESTIMATED", "notes": ""},
                {"parameter_name": "Bandwidth", "value": 125000, "unit": "Hz", "confidence": 0.75, "source": "ESTIMATED", "notes": "-3dB"},
            ],
            "demodulation_result": {
                "success": True,
                "modulation": "QPSK",
                "num_symbols": 100_000,
                "bits": [1, 0] * 50000,
                "evm_db": -22.3,
                "quality": 0.98,
            },
        }

    def test_generate_json_report(self):
        """Test JSON report generation."""
        path = generate_report(self.job_data, format="json")
        
        assert path.endswith(".json")
        
        with open(path, 'r') as f:
            report = json.load(f)
        
        assert "report_info" in report
        assert "file_information" in report
        assert "signal_overview" in report
        assert "extracted_parameters" in report
        assert "demodulation_result" in report
        
        assert report["file_information"]["filename"] == "test_signal.iq"
        assert report["signal_overview"]["detected_modulation"] == "QPSK"

    def test_generate_csv_report(self):
        """Test CSV report generation."""
        path = generate_report(self.job_data, format="csv")
        
        assert path.endswith(".csv")

    def test_generate_pdf_report(self):
        """Test PDF report generation (falls back to JSON if fpdf not available)."""
        path = generate_report(self.job_data, format="pdf")
        
        # Should generate either PDF or fallback to JSON
        assert path.endswith((".pdf", ".json"))

    def test_invalid_format(self):
        """Test invalid format raises error."""
        with pytest.raises(ValueError):
            generate_report(self.job_data, format="invalid")

    def test_bitstream_summary(self):
        """Test bitstream summary creation."""
        generator = SignalReportGenerator()
        
        # With demod result
        demod = {"bits": [1, 0] * 1000}
        summary = generator._create_bitstream_summary(demod)
        
        assert summary["available"] is True
        assert summary["total_bits"] == 2000
        assert summary["total_bytes"] == 250

        # Without demod result
        summary = generator._create_bitstream_summary({})
        assert summary["available"] is False

        summary = generator._create_bitstream_summary(None)
        assert summary["available"] is False

    def test_confidence_assessment(self):
        """Test confidence assessment."""
        generator = SignalReportGenerator()
        
        assessments = generator._assess_confidence(self.job_data)
        
        assert isinstance(assessments, list)
        assert len(assessments) > 0

    def test_limitations(self):
        """Test limitations identification."""
        generator = SignalReportGenerator()
        
        limitations = generator._identify_limitations(self.job_data)
        
        assert isinstance(limitations, list)
        assert len(limitations) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])