"""
Analysis Pipeline Service — coordinates the full signal processing pipeline.
"""
import numpy as np
import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.dsp.signal_processing import (
    parse_iq_file, parse_wav_file, auto_detect_format,
    remove_dc, normalize_signal, bandpass_filter, lowpass_filter,
    resample_signal, compute_snr, compute_bandwidth,
    estimate_symbol_rate, compute_psd, compute_spectrogram,
    downsample_for_visualization, extract_constellation_points,
)
from app.modulation.classifier import (
    classify_modulation, extract_features, get_reference_constellation,
    normalize_constellation,
)
from app.demodulation.demodulator import demodulate, bits_to_bytes, bytes_to_hex, bytes_to_ascii

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """
    Orchestrates the full signal analysis pipeline:
    Parse -> Preprocess -> Extract -> Classify -> Demodulate -> Report
    """

    def __init__(self):
        self.iq_data: Optional[np.ndarray] = None
        self.metadata: Dict[str, Any] = {}
        self.parameters: List[Dict[str, Any]] = []
        self.classification: Dict[str, Any] = {}
        self.demod_result: Dict[str, Any] = {}
        self.progress_callback = None

    def set_progress_callback(self, callback):
        self.progress_callback = callback

    async def _update_progress(self, stage: str, progress: float, message: str):
        if self.progress_callback:
            await self.progress_callback(stage, progress, message)

    async def run_full_pipeline(
        self,
        file_path: str,
        iq_config: Optional[Dict[str, Any]] = None,
        preprocessing: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the complete analysis pipeline on a file."""
        result = {
            "status": "processing",
            "stages": {},
        }

        try:
            # Stage 1: Parse
            await self._update_progress("parse", 5, "Parsing file...")
            self.iq_data, self.metadata = self._parse_file(file_path, iq_config)
            result["stages"]["parse"] = "success"
            result["metadata"] = self.metadata

            # Stage 2: Preprocess
            await self._update_progress("preprocess", 15, "Preprocessing signal...")
            self.iq_data = self._preprocess(self.iq_data, self.metadata, preprocessing)
            result["stages"]["preprocess"] = "success"

            # Stage 3: Parameter extraction
            await self._update_progress("extract", 30, "Extracting signal parameters...")
            self.parameters = self._extract_parameters(self.iq_data, self.metadata)
            result["parameters"] = self.parameters
            result["stages"]["extract"] = "success"

            # Stage 4: Modulation classification
            await self._update_progress("classify", 55, "Classifying modulation...")
            self.classification = self._classify_modulation(self.iq_data, self.metadata)
            result["classification"] = self.classification
            result["stages"]["classify"] = "success"

            # Stage 5: Demodulation
            await self._update_progress("demodulate", 75, "Running demodulator...")
            self.demod_result = self._demodulate(self.iq_data, self.metadata, self.classification)
            result["demodulation"] = self.demod_result
            result["stages"]["demodulate"] = "success"

            # Stage 6: Complete
            await self._update_progress("complete", 100, "Analysis complete.")
            result["status"] = "completed"

        except Exception as e:
            logger.error(f"Pipeline error: {traceback.format_exc()}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    async def _run_from_iq_data(self) -> Dict[str, Any]:
        """Run pipeline starting from already-loaded IQ data."""
        result = {"status": "processing", "stages": {}, "metadata": self.metadata}

        try:
            await self._update_progress("preprocess", 15, "Preprocessing signal...")
            self.iq_data = self._preprocess(self.iq_data, self.metadata, None)
            result["stages"]["preprocess"] = "success"

            await self._update_progress("extract", 30, "Extracting signal parameters...")
            self.parameters = self._extract_parameters(self.iq_data, self.metadata)
            result["parameters"] = self.parameters
            result["stages"]["extract"] = "success"

            await self._update_progress("classify", 55, "Classifying modulation...")
            self.classification = self._classify_modulation(self.iq_data, self.metadata)
            result["classification"] = self.classification
            result["stages"]["classify"] = "success"

            await self._update_progress("demodulate", 75, "Running demodulator...")
            self.demod_result = self._demodulate(self.iq_data, self.metadata, self.classification)
            result["demodulation"] = self.demod_result
            result["stages"]["demodulate"] = "success"

            await self._update_progress("complete", 100, "Analysis complete.")
            result["status"] = "completed"

        except Exception as e:
            logger.error(f"Pipeline error: {traceback.format_exc()}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def _parse_file(self, file_path: str, iq_config: Optional[Dict[str, Any]] = None) -> tuple:
        ext = file_path.rsplit('.', 1)[-1].lower()
        if ext == 'wav':
            return parse_wav_file(file_path)
        elif iq_config:
            return parse_iq_file(
                file_path,
                dtype=iq_config.get("dtype", "int16"),
                iq_order=iq_config.get("iq_order", "IQ"),
                endianness=iq_config.get("endianness", "little"),
                sample_rate=iq_config.get("sample_rate", 1_000_000),
                center_freq=iq_config.get("center_frequency", 0.0),
                scale_factor=iq_config.get("scale_factor", 1.0),
            )
        else:
            return auto_detect_format(file_path)

    def _preprocess(self, iq_data: np.ndarray, metadata: Dict, config: Optional[Dict]) -> np.ndarray:
        if config is None:
            config = {"dc_removal": True, "normalize": True}

        if config.get("dc_removal", True):
            iq_data = remove_dc(iq_data)

        sample_rate = metadata.get("sample_rate", 1_000_000)

        bp_low = config.get("bandpass_low")
        bp_high = config.get("bandpass_high")
        if bp_low is not None and bp_high is not None:
            iq_data = bandpass_filter(iq_data, sample_rate, bp_low, bp_high)

        lp_cutoff = config.get("lowpass_cutoff")
        if lp_cutoff is not None:
            iq_data = lowpass_filter(iq_data, sample_rate, lp_cutoff)

        resample_rate = config.get("resample_rate")
        if resample_rate is not None and resample_rate != sample_rate:
            iq_data = resample_signal(iq_data, sample_rate, resample_rate)

        if config.get("normalize", True):
            iq_data = normalize_signal(iq_data)

        return iq_data

    def _extract_parameters(self, iq_data: np.ndarray, metadata: Dict) -> List[Dict[str, Any]]:
        sample_rate = metadata.get("sample_rate", 1_000_000)
        params = []

        params.append({
            "parameter_name": "Sample Rate",
            "value": sample_rate,
            "unit": "Hz",
            "confidence": 1.0,
            "source": "FILE METADATA",
            "notes": "",
        })

        params.append({
            "parameter_name": "Number of Samples",
            "value": float(len(iq_data)),
            "unit": "samples",
            "confidence": 1.0,
            "source": "MEASURED",
            "notes": "",
        })

        duration = len(iq_data) / sample_rate
        params.append({
            "parameter_name": "Duration",
            "value": duration,
            "unit": "s",
            "confidence": 1.0,
            "source": "MEASURED",
            "notes": "",
        })

        center_freq = metadata.get("center_frequency", 0.0)
        params.append({
            "parameter_name": "Center Frequency",
            "value": center_freq,
            "unit": "Hz",
            "confidence": 1.0 if center_freq != 0 else 0.0,
            "source": "FILE METADATA" if center_freq != 0 else "UNAVAILABLE",
            "notes": "" if center_freq != 0 else "Not available from file metadata",
        })

        # Peak frequency
        n = len(iq_data)
        freqs = np.fft.fftshift(np.fft.fftfreq(n, 1 / sample_rate))
        psd = np.fft.fftshift(np.abs(np.fft.fft(iq_data)) ** 2)
        peak_idx = np.argmax(psd)
        peak_freq = float(freqs[peak_idx])
        params.append({
            "parameter_name": "Peak Frequency",
            "value": peak_freq,
            "unit": "Hz",
            "confidence": 0.9,
            "source": "ESTIMATED",
            "notes": "FFT peak detection",
        })

        # Bandwidth
        bw, bw_low, bw_high = compute_bandwidth(iq_data, sample_rate, threshold_db=-3.0)
        params.append({
            "parameter_name": "Estimated Bandwidth (-3dB)",
            "value": float(bw),
            "unit": "Hz",
            "confidence": 0.8,
            "source": "ESTIMATED",
            "notes": "-3dB bandwidth",
        })

        # Signal power
        signal_power = float(np.mean(np.abs(iq_data) ** 2))
        params.append({
            "parameter_name": "Signal Power",
            "value": float(10 * np.log10(signal_power + 1e-20)),
            "unit": "dBFS",
            "confidence": 0.95,
            "source": "MEASURED",
            "notes": "",
        })

        # SNR
        snr = float(compute_snr(iq_data, sample_rate))
        params.append({
            "parameter_name": "SNR",
            "value": snr,
            "unit": "dB",
            "confidence": 0.7,
            "source": "ESTIMATED",
            "notes": "Estimated from PSD noise floor",
        })

        # Peak amplitude
        peak_amp = float(np.max(np.abs(iq_data)))
        params.append({
            "parameter_name": "Peak Amplitude",
            "value": peak_amp,
            "unit": "",
            "confidence": 1.0,
            "source": "MEASURED",
            "notes": "",
        })

        # RMS amplitude
        rms_amp = float(np.sqrt(np.mean(np.abs(iq_data) ** 2)))
        params.append({
            "parameter_name": "RMS Amplitude",
            "value": rms_amp,
            "unit": "",
            "confidence": 1.0,
            "source": "MEASURED",
            "notes": "",
        })

        # Frequency offset estimation
        freq_offset = peak_freq
        params.append({
            "parameter_name": "Frequency Offset",
            "value": freq_offset,
            "unit": "Hz",
            "confidence": 0.6,
            "source": "ESTIMATED",
            "notes": "Estimated from spectral peak",
        })

        # Symbol rate
        sym_rate, sym_conf = estimate_symbol_rate(iq_data, sample_rate)
        params.append({
            "parameter_name": "Estimated Symbol Rate",
            "value": float(sym_rate),
            "unit": "sym/s",
            "confidence": float(sym_conf),
            "source": "ESTIMATED",
            "notes": "Spectral analysis of magnitude envelope",
        })

        return params

    def _classify_modulation(self, iq_data: np.ndarray, metadata: Dict) -> Dict[str, Any]:
        sample_rate = metadata.get("sample_rate", 1_000_000)
        result = classify_modulation(iq_data, sample_rate)
        return result

    def _demodulate(self, iq_data: np.ndarray, metadata: Dict, classification: Dict) -> Dict[str, Any]:
        sample_rate = metadata.get("sample_rate", 1_000_000)
        modulation = classification.get("modulation", "UNKNOWN")

        if modulation == "UNKNOWN":
            return {"success": False, "error": "Unknown modulation", "bits": [], "modulation": "UNKNOWN"}

        # Get estimated symbol rate
        sym_rate = 0.0
        for p in self.parameters:
            if p["parameter_name"] == "Estimated Symbol Rate":
                sym_rate = p.get("value", 0.0)
                break

        if sym_rate <= 0:
            sym_rate = sample_rate / 10  # Fallback

        # Use known symbol rate for synthetic
        if metadata.get("symbol_rate"):
            sym_rate = metadata["symbol_rate"]

        return demodulate(
            iq_data, modulation,
            symbol_rate=sym_rate,
            sample_rate=sample_rate,
        )

    def get_waveform_data(self, max_points: int = 10000) -> Dict[str, Any]:
        if self.iq_data is None:
            return {}
        ds, ds_info = downsample_for_visualization(self.iq_data, max_points)
        sample_rate = self.metadata.get("sample_rate", 1_000_000)
        factor = ds_info.get("factor", 1)
        time_axis = np.arange(len(ds)) * factor / sample_rate
        return {
            "i": np.real(ds).tolist(),
            "q": np.imag(ds).tolist(),
            "magnitude": np.abs(ds).tolist(),
            "phase": np.angle(ds).tolist(),
            "time": time_axis.tolist(),
            "sample_rate": sample_rate,
            "downsampled": ds_info.get("downsampled", False),
            "downsample_factor": factor,
            "original_length": ds_info.get("original_length", len(ds)),
        }

    def get_spectrum_data(self, fft_size: int = 4096, window: str = "hann") -> Dict[str, Any]:
        if self.iq_data is None:
            return {}
        sample_rate = self.metadata.get("sample_rate", 1_000_000)
        freqs, psd_db = compute_psd(self.iq_data, sample_rate, nfft=fft_size, window=window)

        peak_idx = np.argmax(psd_db)
        noise_floor = float(np.median(psd_db))
        bw, _, _ = compute_bandwidth(self.iq_data, sample_rate)

        return {
            "frequencies": freqs.tolist(),
            "magnitudes": psd_db.tolist(),
            "fft_size": fft_size,
            "window": window,
            "sample_rate": sample_rate,
            "peak_frequency": float(freqs[peak_idx]),
            "noise_floor": noise_floor,
            "occupied_bandwidth": float(bw),
        }

    def get_spectrogram_data(self, fft_size: int = 1024, hop: int = None, window: str = "hann") -> Dict[str, Any]:
        if self.iq_data is None:
            return {}
        sample_rate = self.metadata.get("sample_rate", 1_000_000)
        if hop is None:
            hop = fft_size // 4
        times, freqs, spec = compute_spectrogram(self.iq_data, sample_rate, nfft=fft_size, hop=hop, window=window)

        # Downsample spectrogram for transfer
        max_time_bins = 500
        max_freq_bins = 512
        if spec.shape[1] > max_time_bins:
            step = spec.shape[1] // max_time_bins
            spec = spec[:, ::step]
            times = times[::step]
        if spec.shape[0] > max_freq_bins:
            step = spec.shape[0] // max_freq_bins
            spec = spec[::step, :]
            freqs = freqs[::step]

        return {
            "times": times.tolist(),
            "frequencies": freqs.tolist(),
            "magnitudes": spec.tolist(),
            "fft_size": fft_size,
            "hop_size": hop,
            "window": window,
            "sample_rate": sample_rate,
        }

    def get_constellation_data(self, normalized: bool = False) -> Dict[str, Any]:
        if self.iq_data is None:
            return {}
        sample_rate = self.metadata.get("sample_rate", 1_000_000)
        sps = self.metadata.get("samples_per_symbol", 10)

        constellation = extract_constellation_points(self.iq_data, samples_per_symbol=sps, num_symbols=2000)
        if normalized:
            constellation = normalize_constellation(constellation)

        # Reference constellation
        mod = self.classification.get("modulation", "")
        ref = get_reference_constellation(mod)
        ref_i = np.real(ref).tolist() if len(ref) > 0 else None
        ref_q = np.imag(ref).tolist() if len(ref) > 0 else None

        return {
            "i": np.real(constellation).tolist(),
            "q": np.imag(constellation).tolist(),
            "reference_i": ref_i,
            "reference_q": ref_q,
            "modulation": mod,
            "normalized": normalized,
            "num_points": len(constellation),
        }

    def get_bitstream_data(self, offset: int = 0, length: int = 1024) -> Dict[str, Any]:
        bits = self.demod_result.get("bits", [])
        if not bits:
            return {
                "bits": [], "hex_dump": "", "ascii_dump": "",
                "total_bits": 0, "total_bytes": 0,
                "offset": 0, "length": 0, "is_printable": False,
            }

        total_bits = len(bits)
        total_bytes = total_bits // 8
        chunk = bits[offset:offset + length]

        byte_data = bits_to_bytes(chunk)
        hex_dump = bytes_to_hex(byte_data)
        ascii_dump = bytes_to_ascii(byte_data)
        is_printable = any(32 <= b <= 126 for b in byte_data)

        return {
            "bits": chunk,
            "hex_dump": hex_dump,
            "ascii_dump": ascii_dump,
            "total_bits": total_bits,
            "total_bytes": total_bytes,
            "offset": offset,
            "length": len(chunk),
            "is_printable": is_printable,
        }

    def get_job_summary(self) -> Dict[str, Any]:
        """Build summary dict suitable for DB updates and report generation."""
        snr = None
        bw = None
        sym_rate = None
        freq_offset = None
        for p in self.parameters:
            if p["parameter_name"] == "SNR":
                snr = p.get("value")
            elif p["parameter_name"] == "Estimated Bandwidth (-3dB)":
                bw = p.get("value")
            elif p["parameter_name"] == "Estimated Symbol Rate":
                sym_rate = p.get("value")
            elif p["parameter_name"] == "Frequency Offset":
                freq_offset = p.get("value")

        return {
            "sample_rate": self.metadata.get("sample_rate"),
            "center_frequency": self.metadata.get("center_frequency", 0),
            "duration": self.metadata.get("duration"),
            "num_samples": self.metadata.get("num_samples", len(self.iq_data) if self.iq_data is not None else 0),
            "num_channels": self.metadata.get("num_channels", 1),
            "data_type": self.metadata.get("dtype", ""),
            "detected_modulation": self.classification.get("modulation"),
            "modulation_confidence": self.classification.get("confidence"),
            "modulation_probabilities": self.classification.get("probabilities"),
            "snr": snr,
            "bandwidth": bw,
            "symbol_rate": sym_rate,
            "frequency_offset": freq_offset,
            "demodulated": self.demod_result.get("success", False),
            "recovered_bits": len(self.demod_result.get("bits", [])),
            "parameters": self.parameters,
            "demodulation_result": self.demod_result,
            "is_demo": self.metadata.get("is_demo", False),
        }
