import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import base64
from io import BytesIO

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class SignalReportGenerator:
    """Generate signal analysis reports in multiple formats."""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        job_data: Dict[str, Any],
        format: str = "pdf",
    ) -> str:
        """Generate report in specified format."""
        if format == "pdf":
            return self._generate_pdf(job_data)
        elif format == "json":
            return self._generate_json(job_data)
        elif format == "csv":
            return self._generate_csv(job_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_json(self, job_data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        report = {
            "report_info": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "generator": "SIH26147 Signal Analyzer",
            },
            "file_information": {
                "filename": job_data.get("filename"),
                "file_type": job_data.get("file_type"),
                "file_size": job_data.get("file_size"),
                "sample_rate": job_data.get("sample_rate"),
                "center_frequency": job_data.get("center_frequency"),
                "duration": job_data.get("duration"),
                "num_samples": job_data.get("num_samples"),
                "num_channels": job_data.get("num_channels"),
                "data_type": job_data.get("data_type"),
            },
            "signal_overview": {
                "detected_modulation": job_data.get("detected_modulation"),
                "modulation_confidence": job_data.get("modulation_confidence"),
                "modulation_probabilities": job_data.get("modulation_probabilities"),
                "snr_db": job_data.get("snr"),
                "bandwidth_hz": job_data.get("bandwidth"),
                "symbol_rate": job_data.get("symbol_rate"),
                "frequency_offset_hz": job_data.get("frequency_offset"),
            },
            "extracted_parameters": job_data.get("parameters", []),
            "demodulation_result": job_data.get("demodulation_result"),
            "bitstream_summary": self._create_bitstream_summary(job_data.get("demodulation_result")),
            "confidence_assessment": self._assess_confidence(job_data),
            "limitations": self._identify_limitations(job_data),
        }
        
        filename = f"report_{job_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(filepath)
    
    def _generate_csv(self, job_data: Dict[str, Any]) -> str:
        """Generate CSV report with parameters."""
        import csv
        
        filename = f"report_{job_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Parameter", "Value", "Unit", "Confidence", "Source", "Notes"])
            
            params = job_data.get("parameters", [])
            for p in params:
                writer.writerow([
                    p.get("parameter_name", ""),
                    p.get("value", ""),
                    p.get("unit", ""),
                    p.get("confidence", ""),
                    p.get("source", ""),
                    p.get("notes", ""),
                ])
            
            writer.writerow([])
            writer.writerow(["Modulation", job_data.get("detected_modulation", ""), "", job_data.get("modulation_confidence", ""), "ML Classification", ""])
            writer.writerow(["SNR", job_data.get("snr", ""), "dB", "", "Estimated", ""])
            writer.writerow(["Bandwidth", job_data.get("bandwidth", ""), "Hz", "", "Estimated", ""])
            writer.writerow(["Symbol Rate", job_data.get("symbol_rate", ""), "sym/s", "", "Estimated", ""])
        
        return str(filepath)
    
    def _generate_pdf(self, job_data: Dict[str, Any]) -> str:
        """Generate PDF report."""
        if not HAS_FPDF:
            return self._generate_json(job_data).replace('.json', '.pdf')
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        
        pdf.cell(0, 15, "Signal Intelligence Report", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC", ln=True, align="C")
        pdf.cell(0, 6, f"SIH26147 Automated Signal Analyzer v1.0", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "1. File Information", ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        file_info = [
            ("Filename", job_data.get("filename", "N/A")),
            ("File Type", job_data.get("file_type", "N/A")),
            ("File Size", f"{job_data.get('file_size', 0) / 1024 / 1024:.2f} MB"),
            ("Sample Rate", f"{job_data.get('sample_rate', 0) / 1e6:.3f} MHz"),
            ("Center Frequency", f"{job_data.get('center_frequency', 0) / 1e6:.3f} MHz"),
            ("Duration", f"{job_data.get('duration', 0):.3f} s"),
            ("Number of Samples", f"{job_data.get('num_samples', 0):,}"),
            ("Channels", str(job_data.get("num_channels", "N/A"))),
            ("Data Type", job_data.get("data_type", "N/A")),
        ]
        
        for label, value in file_info:
            pdf.cell(60, 7, label, border=0)
            pdf.cell(0, 7, str(value), border=0, ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "2. Signal Overview", ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        overview = [
            ("Detected Modulation", job_data.get("detected_modulation", "N/A")),
            ("Modulation Confidence", f"{job_data.get('modulation_confidence', 0)*100:.1f}%"),
            ("SNR (Estimated)", f"{job_data.get('snr', 0):.1f} dB"),
            ("Bandwidth (Estimated)", f"{job_data.get('bandwidth', 0) / 1e3:.1f} kHz"),
            ("Symbol Rate (Estimated)", f"{job_data.get('symbol_rate', 0) / 1e3:.1f} ksym/s"),
            ("Frequency Offset (Estimated)", f"{job_data.get('frequency_offset', 0):.1f} Hz"),
        ]
        
        for label, value in overview:
            pdf.cell(60, 7, label, border=0)
            pdf.cell(0, 7, str(value), border=0, ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "3. Modulation Classification Probabilities", ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        probs = job_data.get("modulation_probabilities", {})
        for mod, prob in sorted(probs.items(), key=lambda x: -x[1]):
            pdf.cell(60, 7, mod, border=0)
            pdf.cell(0, 7, f"{prob*100:.1f}%", border=0, ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "4. Extracted Parameters", ln=True)
        pdf.set_font("Helvetica", "", 9)
        
        params = job_data.get("parameters", [])
        if params:
            pdf.cell(45, 7, "Parameter", border=1)
            pdf.cell(30, 7, "Value", border=1)
            pdf.cell(20, 7, "Unit", border=1)
            pdf.cell(20, 7, "Confidence", border=1)
            pdf.cell(25, 7, "Source", border=1)
            pdf.cell(50, 7, "Notes", border=1, ln=True)
            
            for p in params[:30]:
                pdf.cell(45, 6, str(p.get("parameter_name", ""))[:30], border=1)
                pdf.cell(30, 6, str(p.get("value", ""))[:20], border=1)
                pdf.cell(20, 6, str(p.get("unit", "")), border=1)
                pdf.cell(20, 6, f"{p.get('confidence', 0)*100:.0f}%", border=1)
                pdf.cell(25, 6, str(p.get("source", "")), border=1)
                pdf.cell(50, 6, str(p.get("notes", ""))[:40], border=1, ln=True)
        else:
            pdf.cell(0, 7, "No parameters extracted", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "5. Demodulation Result", ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        demod = job_data.get("demodulation_result", {})
        if demod:
            demo_info = [
                ("Status", "SUCCESS" if demod.get("success") else "FAILED"),
                ("Modulation", demod.get("modulation", "N/A")),
                ("Recovered Symbols", str(demod.get("num_symbols", "N/A"))),
                ("Recovered Bits", str(len(demod.get("bits", [])))),
                ("EVM", f"{demod.get('evm_db', 0):.1f} dB"),
                ("Quality", f"{demod.get('quality', 0)*100:.1f}%"),
            ]
            
            for label, value in demo_info:
                pdf.cell(60, 7, label, border=0)
                pdf.cell(0, 7, str(value), border=0, ln=True)
            
            bits = demod.get("bits", [])
            if bits:
                pdf.ln(3)
                pdf.cell(0, 7, "Bitstream (first 128 bits):", ln=True)
                bit_str = ''.join(str(b) for b in bits[:128])
                pdf.set_font("Courier", "", 8)
                for i in range(0, len(bit_str), 64):
                    pdf.cell(0, 5, bit_str[i:i+64], ln=True)
        else:
            pdf.cell(0, 7, "No demodulation performed", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "6. Confidence Assessment", ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        for item in self._assess_confidence(job_data):
            pdf.cell(0, 7, f"- {item}", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "7. Limitations", ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        for item in self._identify_limitations(job_data):
            pdf.cell(0, 7, f"- {item}", ln=True)
        
        filename = f"report_{job_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        pdf.output(str(filepath))
        
        return str(filepath)
    
    def _create_bitstream_summary(self, demod_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create bitstream summary."""
        if not demod_result or not demod_result.get("bits"):
            return {"available": False}
        
        bits = demod_result.get("bits", [])
        bytes_data = bytes((bits[i] << (7 - (i % 8))) | 0 for i in range(min(len(bits), 128)))
        
        return {
            "available": True,
            "total_bits": len(bits),
            "total_bytes": len(bits) // 8,
            "first_128_bits": ''.join(str(b) for b in bits[:128]),
            "first_16_bytes_hex": ' '.join(f'{b:02X}' for b in bytes_data[:16]),
            "first_16_bytes_ascii": ''.join(chr(b) if 32 <= b <= 126 else '.' for b in bytes_data[:16]),
        }
    
    def _assess_confidence(self, job_data: Dict[str, Any]) -> List[str]:
        """Assess overall confidence in results."""
        assessments = []
        
        snr = job_data.get("snr", 0)
        if snr > 20:
            assessments.append("High SNR - parameter estimates are reliable")
        elif snr > 10:
            assessments.append("Moderate SNR - parameter estimates have moderate uncertainty")
        else:
            assessments.append("Low SNR - parameter estimates have high uncertainty")
        
        mod_conf = job_data.get("modulation_confidence", 0)
        if mod_conf > 0.9:
            assessments.append("High modulation classification confidence")
        elif mod_conf > 0.7:
            assessments.append("Moderate modulation classification confidence")
        else:
            assessments.append("Low modulation classification confidence - verify manually")
        
        if job_data.get("demodulation_result", {}).get("success"):
            evm = job_data.get("demodulation_result", {}).get("evm_db", -30)
            if evm < -20:
                assessments.append("Excellent demodulation quality (low EVM)")
            elif evm < -10:
                assessments.append("Good demodulation quality")
            else:
                assessments.append("Poor demodulation quality - high symbol error rate likely")
        
        if not assessments:
            assessments.append("Insufficient data for confidence assessment")
        
        return assessments
    
    def _identify_limitations(self, job_data: Dict[str, Any]) -> List[str]:
        """Identify analysis limitations."""
        limitations = []
        
        duration = job_data.get("duration", 0)
        if duration < 0.01:
            limitations.append("Very short signal duration - statistical estimates unreliable")
        
        snr = job_data.get("snr", 0)
        if snr < 0:
            limitations.append("Negative SNR - signal below noise floor")
        
        if not job_data.get("demodulation_result", {}).get("success"):
            limitations.append("Demodulation failed - bitstream not recovered")
        
        mod_conf = job_data.get("modulation_confidence", 0)
        if mod_conf < 0.5:
            limitations.append("Modulation classification below confidence threshold")
        
        sample_rate = job_data.get("sample_rate", 1e6)
        symbol_rate = job_data.get("symbol_rate", 0)
        if symbol_rate > 0 and sample_rate / symbol_rate < 4:
            limitations.append("Low samples per symbol - timing recovery may be inaccurate")
        
        if not limitations:
            limitations.append("No significant limitations identified")
        
        return limitations


def generate_report(
    job_data: Dict[str, Any],
    format: str = "pdf",
    output_dir: str = "./reports",
) -> str:
    """Convenience function to generate report."""
    generator = SignalReportGenerator(output_dir)
    return generator.generate_report(job_data, format)