import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq, fftshift
from typing import Tuple, Optional, Dict, Any
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


def parse_iq_file(
    file_path: str,
    dtype: str = "int16",
    iq_order: str = "IQ",
    endianness: str = "little",
    sample_rate: float = 1_000_000,
    center_freq: float = 0.0,
    scale_factor: float = 1.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Parse raw IQ file with configurable parameters.
    
    Args:
        file_path: Path to IQ file
        dtype: Data type (int8, int16, int32, float32)
        iq_order: IQ interleaving order (IQ or QI)
        endianness: Byte order (little or big)
        sample_rate: Sample rate in Hz
        center_freq: Center frequency in Hz
        scale_factor: Scaling factor for integer types
    
    Returns:
        Complex IQ array and metadata dict
    """
    dtype_map = {
        "int8": np.int8,
        "int16": np.int16,
        "int32": np.int32,
        "float32": np.float32,
        "float64": np.float64,
        "uint8": np.uint8,
        "uint16": np.uint16,
    }
    
    np_dtype = dtype_map.get(dtype, np.int16)
    
    if endianness == "big":
        np_dtype = np.dtype(np_dtype).newbyteorder('>')
    
    raw_data = np.fromfile(file_path, dtype=np_dtype)
    
    if len(raw_data) % 2 != 0:
        raw_data = raw_data[:-1]
    
    if iq_order == "IQ":
        i_data = raw_data[0::2]
        q_data = raw_data[1::2]
    else:
        q_data = raw_data[0::2]
        i_data = raw_data[1::2]
    
    if np.issubdtype(np_dtype, np.integer):
        max_val = np.iinfo(np_dtype).max
        i_data = i_data.astype(np.float32) / max_val * scale_factor
        q_data = q_data.astype(np.float32) / max_val * scale_factor
    else:
        i_data = i_data.astype(np.float32)
        q_data = q_data.astype(np.float32)
    
    iq_data = i_data + 1j * q_data
    
    metadata = {
        "sample_rate": sample_rate,
        "center_frequency": center_freq,
        "num_samples": len(iq_data),
        "duration": len(iq_data) / sample_rate,
        "dtype": dtype,
        "iq_order": iq_order,
        "endianness": endianness,
        "scale_factor": scale_factor,
        "num_channels": 1,
    }
    
    return iq_data, metadata


def parse_wav_file(file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Parse WAV file and convert to complex IQ if stereo (I/Q channels).
    """
    import wave
    
    with wave.open(file_path, 'rb') as wav:
        n_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        frame_rate = wav.getframerate()
        n_frames = wav.getnframes()
        
        raw_data = wav.readframes(n_frames)
        
        if sample_width == 1:
            dtype = np.uint8
        elif sample_width == 2:
            dtype = np.int16
        elif sample_width == 4:
            dtype = np.int32
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")
        
        audio_data = np.frombuffer(raw_data, dtype=dtype)
        
        if n_channels == 1:
            max_val = np.iinfo(dtype).max if np.issubdtype(dtype, np.integer) else 1.0
            if np.issubdtype(dtype, np.integer):
                audio_data = audio_data.astype(np.float32) / max_val
            iq_data = audio_data.astype(np.complex64)
            iq_data = iq_data + 1j * np.zeros_like(iq_data)
        elif n_channels == 2:
            audio_data = audio_data.reshape(-1, 2)
            max_val = np.iinfo(dtype).max if np.issubdtype(dtype, np.integer) else 1.0
            if np.issubdtype(dtype, np.integer):
                audio_data = audio_data.astype(np.float32) / max_val
            i_data = audio_data[:, 0]
            q_data = audio_data[:, 1]
            iq_data = i_data + 1j * q_data
        else:
            raise ValueError(f"Unsupported number of channels: {n_channels}")
        
        metadata = {
            "sample_rate": float(frame_rate),
            "center_frequency": 0.0,
            "num_samples": len(iq_data),
            "duration": len(iq_data) / frame_rate,
            "dtype": str(dtype),
            "num_channels": n_channels,
        }
        
        return iq_data, metadata


def parse_raw_file(
    file_path: str,
    dtype: str = "int16",
    num_channels: int = 1,
    sample_rate: float = 1_000_000,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Parse raw binary file."""
    return parse_iq_file(
        file_path,
        dtype=dtype,
        sample_rate=sample_rate,
    )


def auto_detect_format(file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Auto-detect file format and parse accordingly."""
    ext = file_path.split('.')[-1].lower()
    
    if ext in ['wav']:
        return parse_wav_file(file_path)
    elif ext in ['iq', 'bin', 'raw']:
        return parse_iq_file(file_path)
    else:
        return parse_iq_file(file_path)


def remove_dc(iq_data: np.ndarray) -> np.ndarray:
    """Remove DC offset from IQ data."""
    return iq_data - np.mean(iq_data)


def normalize_signal(iq_data: np.ndarray, target_rms: float = 1.0) -> np.ndarray:
    """Normalize signal to target RMS."""
    current_rms = np.sqrt(np.mean(np.abs(iq_data) ** 2))
    if current_rms > 0:
        return iq_data * (target_rms / current_rms)
    return iq_data


def bandpass_filter(
    iq_data: np.ndarray,
    sample_rate: float,
    low_freq: float,
    high_freq: float,
    order: int = 4,
) -> np.ndarray:
    """Apply bandpass filter to IQ data."""
    nyquist = sample_rate / 2
    low = low_freq / nyquist
    high = high_freq / nyquist
    
    if low >= high or low <= 0 or high >= 1:
        return iq_data
    
    b, a = signal.butter(order, [low, high], btype='band')
    filtered = signal.filtfilt(b, a, iq_data)
    return filtered


def lowpass_filter(
    iq_data: np.ndarray,
    sample_rate: float,
    cutoff: float,
    order: int = 4,
) -> np.ndarray:
    """Apply lowpass filter to IQ data."""
    nyquist = sample_rate / 2
    normalized_cutoff = cutoff / nyquist
    
    if normalized_cutoff >= 1 or normalized_cutoff <= 0:
        return iq_data
    
    b, a = signal.butter(order, normalized_cutoff, btype='low')
    filtered = signal.filtfilt(b, a, iq_data)
    return filtered


def resample_signal(
    iq_data: np.ndarray,
    original_rate: float,
    target_rate: float,
) -> np.ndarray:
    """Resample signal to target sample rate."""
    if original_rate == target_rate:
        return iq_data
    
    num_samples = int(len(iq_data) * target_rate / original_rate)
    resampled = signal.resample(iq_data, num_samples)
    return resampled


def estimate_noise_floor(iq_data: np.ndarray, sample_rate: float) -> float:
    """Estimate noise floor using median of PSD."""
    n = len(iq_data)
    psd = np.abs(fft(iq_data)) ** 2 / (sample_rate * n)
    psd_db = 10 * np.log10(psd + 1e-20)
    noise_floor = np.median(psd_db)
    return noise_floor


def compute_snr(iq_data: np.ndarray, sample_rate: float) -> float:
    """Estimate SNR using signal power vs noise floor."""
    signal_power = np.mean(np.abs(iq_data) ** 2)
    noise_floor = estimate_noise_floor(iq_data, sample_rate)
    noise_power = 10 ** (noise_floor / 10)
    
    if noise_power > 0:
        snr_db = 10 * np.log10(signal_power / noise_power)
    else:
        snr_db = 100.0
    
    return np.clip(snr_db, -20, 60)


def compute_bandwidth(
    iq_data: np.ndarray,
    sample_rate: float,
    threshold_db: float = -3.0,
) -> Tuple[float, float, float]:
    """
    Compute occupied bandwidth.
    Returns: (bandwidth, lower_freq, upper_freq)
    """
    n = len(iq_data)
    freqs = fftshift(fftfreq(n, 1/sample_rate))
    psd = fftshift(np.abs(fft(iq_data)) ** 2)
    psd_db = 10 * np.log10(psd + 1e-20)
    
    peak_idx = np.argmax(psd_db)
    peak_power = psd_db[peak_idx]
    threshold = peak_power + threshold_db
    
    above_threshold = psd_db >= threshold
    if not np.any(above_threshold):
        return 0.0, 0.0, 0.0
    
    indices = np.where(above_threshold)[0]
    lower_idx = indices[0]
    upper_idx = indices[-1]
    
    lower_freq = freqs[lower_idx]
    upper_freq = freqs[upper_idx]
    bandwidth = upper_freq - lower_freq
    
    return abs(bandwidth), lower_freq, upper_freq


def estimate_symbol_rate(
    iq_data: np.ndarray,
    sample_rate: float,
    max_symbol_rate: float = None,
) -> Tuple[float, float]:
    """
    Estimate symbol rate using spectral analysis of magnitude.
    Returns: (symbol_rate, confidence)
    """
    if max_symbol_rate is None:
        max_symbol_rate = sample_rate / 4
    
    magnitude = np.abs(iq_data)
    magnitude = magnitude - np.mean(magnitude)
    
    n = len(magnitude)
    freqs = fftfreq(n, 1/sample_rate)[:n//2]
    mag_spectrum = np.abs(fft(magnitude))[:n//2]
    
    symbol_rate_range = (freqs > 1000) & (freqs < max_symbol_rate)
    if not np.any(symbol_rate_range):
        return 0.0, 0.0
    
    candidate_freqs = freqs[symbol_rate_range]
    candidate_mags = mag_spectrum[symbol_rate_range]
    
    peak_idx = np.argmax(candidate_mags)
    estimated_rate = candidate_freqs[peak_idx]
    
    peak_mag = candidate_mags[peak_idx]
    avg_mag = np.mean(candidate_mags)
    confidence = min(1.0, (peak_mag / avg_mag - 1) / 10) if avg_mag > 0 else 0.0
    
    return abs(estimated_rate), confidence


def compute_psd(
    iq_data: np.ndarray,
    sample_rate: float,
    nfft: int = 4096,
    window: str = 'hann',
    overlap: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute Power Spectral Density."""
    window_func = get_window(window, nfft)
    step = int(nfft * (1 - overlap))
    
    if len(iq_data) < nfft:
        nfft = len(iq_data)
        window_func = get_window(window, nfft)
    
    num_segments = max(1, (len(iq_data) - nfft) // step + 1)
    psd_accum = np.zeros(nfft)
    
    for i in range(num_segments):
        start = i * step
        end = start + nfft
        segment = iq_data[start:end] * window_func
        psd_segment = np.abs(fft(segment, nfft)) ** 2
        psd_accum += psd_segment
    
    psd_avg = psd_accum / num_segments
    psd_avg = psd_avg / (sample_rate * np.sum(window_func ** 2))
    
    freqs = fftshift(fftfreq(nfft, 1/sample_rate))
    psd_db = 10 * np.log10(fftshift(psd_avg) + 1e-20)
    
    return freqs, psd_db


def get_window(window_name: str, nfft: int) -> np.ndarray:
    """Get window function by name."""
    windows = {
        'hann': np.hanning,
        'hamming': np.hamming,
        'blackman': np.blackman,
        'rectangular': lambda n: np.ones(n),
        'bartlett': np.bartlett,
        'kaiser': lambda n: np.kaiser(n, beta=8),
    }
    func = windows.get(window_name.lower(), np.hanning)
    return func(nfft)


def compute_spectrogram(
    iq_data: np.ndarray,
    sample_rate: float,
    nfft: int = 1024,
    hop: int = None,
    window: str = 'hann',
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute spectrogram (time-frequency representation)."""
    if hop is None:
        hop = nfft // 4
    
    window_func = get_window(window, nfft)
    num_frames = max(1, (len(iq_data) - nfft) // hop + 1)
    
    spectrogram = np.zeros((num_frames, nfft))
    
    for i in range(num_frames):
        start = i * hop
        end = start + nfft
        if end > len(iq_data):
            segment = np.pad(iq_data[start:], (0, end - len(iq_data)))
        else:
            segment = iq_data[start:end]
        
        segment = segment * window_func
        spec = np.abs(fft(segment, nfft)) ** 2
        spectrogram[i, :] = 10 * np.log10(fftshift(spec) + 1e-20)
    
    times = np.arange(num_frames) * hop / sample_rate
    freqs = fftshift(fftfreq(nfft, 1/sample_rate))
    
    return times, freqs, spectrogram.T


def downsample_for_visualization(
    iq_data: np.ndarray,
    max_points: int = 10000,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Downsample IQ data for visualization while preserving characteristics."""
    n = len(iq_data)
    
    if n <= max_points:
        return iq_data, {"downsampled": False, "factor": 1}
    
    factor = n // max_points + 1
    
    indices = np.arange(0, n, factor)[:max_points]
    downsampled = iq_data[indices]
    
    return downsampled, {"downsampled": True, "factor": factor, "original_length": n}


def extract_constellation_points(
    iq_data: np.ndarray,
    samples_per_symbol: int = 10,
    num_symbols: int = 1000,
) -> np.ndarray:
    """Extract constellation points from IQ data."""
    if len(iq_data) < samples_per_symbol * num_symbols:
        num_symbols = len(iq_data) // samples_per_symbol
    
    if num_symbols < 10:
        return iq_data
    
    total_samples = num_symbols * samples_per_symbol
    truncated = iq_data[:total_samples]
    
    reshaped = truncated.reshape(num_symbols, samples_per_symbol)
    constellation = np.mean(reshaped, axis=1)
    
    return constellation