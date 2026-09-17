import numpy as np
from scipy import signal
from typing import Tuple, Dict, Any, Optional
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


def cross_correlation(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
    max_lag: int = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Compute cross-correlation between two signals.
    Returns: (correlation, lags, metadata)
    """
    if len(signal_a) != len(signal_b):
        min_len = min(len(signal_a), len(signal_b))
        signal_a = signal_a[:min_len]
        signal_b = signal_b[:min_len]
    
    n = len(signal_a)
    
    if max_lag is None:
        max_lag = n // 4
    
    max_lag = min(max_lag, n // 2)
    
    corr = signal.correlate(signal_a, signal_b, mode='full')
    lags = signal.correlation_lags(n, n, mode='full')
    
    center = len(corr) // 2
    start = center - max_lag
    end = center + max_lag + 1
    
    corr = corr[start:end]
    lags = lags[start:end]
    
    corr_normalized = corr / (np.std(signal_a) * np.std(signal_b) * n) if np.std(signal_a) > 0 and np.std(signal_b) > 0 else corr
    
    peak_idx = np.argmax(np.abs(corr_normalized))
    peak_corr = corr_normalized[peak_idx]
    peak_lag = lags[peak_idx]
    
    time_offset = peak_lag / n if n > 0 else 0
    
    metadata = {
        'peak_correlation': float(peak_corr),
        'peak_lag': int(peak_lag),
        'time_offset': float(time_offset),
        'similarity_score': float(np.abs(peak_corr)),
        'max_lag': max_lag,
    }
    
    return corr_normalized, lags, metadata


def normalized_cross_correlation(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
) -> Tuple[float, int]:
    """Compute normalized cross-correlation coefficient and lag."""
    corr, lags, meta = cross_correlation(signal_a, signal_b)
    return meta['peak_correlation'], meta['peak_lag']


def compare_signals(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
    sample_rate: float,
) -> Dict[str, Any]:
    """
    Comprehensive signal comparison.
    """
    min_len = min(len(signal_a), len(signal_b))
    signal_a = signal_a[:min_len]
    signal_b = signal_b[:min_len]
    
    corr, lags, meta = cross_correlation(signal_a, signal_b, max_lag=min_len//4)
    
    mse = np.mean(np.abs(signal_a - signal_b) ** 2)
    nmse = mse / np.mean(np.abs(signal_a) ** 2) if np.mean(np.abs(signal_a) ** 2) > 0 else 1.0
    
    corr_coef = np.corrcoef(np.real(signal_a), np.real(signal_b))[0, 1]
    corr_coef_imag = np.corrcoef(np.imag(signal_a), np.imag(signal_b))[0, 1]
    
    snr_a = 10 * np.log10(np.mean(np.abs(signal_a) ** 2) / (np.var(np.abs(signal_a)) + 1e-20))
    snr_b = 10 * np.log10(np.mean(np.abs(signal_b) ** 2) / (np.var(np.abs(signal_b)) + 1e-20))
    
    freqs_a = np.fft.fftfreq(min_len, 1/sample_rate)[:min_len//2]
    psd_a = np.abs(np.fft.fft(signal_a))[:min_len//2] ** 2
    psd_b = np.abs(np.fft.fft(signal_b))[:min_len//2] ** 2
    
    spectral_similarity = np.corrcoef(psd_a, psd_b)[0, 1] if len(psd_a) > 1 else 0.0
    
    return {
        'cross_correlation': corr.tolist(),
        'lags': lags.tolist(),
        'peak_correlation': meta['peak_correlation'],
        'peak_lag': meta['peak_lag'],
        'time_offset_seconds': meta['time_offset'] / sample_rate,
        'similarity_score': meta['similarity_score'],
        'mse': float(mse),
        'nmse': float(nmse),
        'correlation_coefficient_real': float(corr_coef) if not np.isnan(corr_coef) else 0.0,
        'correlation_coefficient_imag': float(corr_coef_imag) if not np.isnan(corr_coef_imag) else 0.0,
        'spectral_similarity': float(spectral_similarity) if not np.isnan(spectral_similarity) else 0.0,
        'snr_a_db': float(snr_a),
        'snr_b_db': float(snr_b),
    }


def find_signal_in_noise(
    signal_template: np.ndarray,
    noisy_signal: np.ndarray,
    sample_rate: float,
    threshold: float = 0.7,
) -> Dict[str, Any]:
    """Find a known signal template within a noisy signal."""
    corr, lags, meta = cross_correlation(noisy_signal, signal_template)
    
    peaks = signal.find_peaks(np.abs(corr), height=threshold * np.max(np.abs(corr)))[0]
    
    detections = []
    for peak in peaks:
        detections.append({
            'lag': int(lags[peak]),
            'time_offset': float(lags[peak]) / sample_rate,
            'correlation': float(corr[peak]),
        })
    
    return {
        'detections': detections,
        'num_detections': len(detections),
        'max_correlation': float(np.max(np.abs(corr))),
    }


def auto_correlation(signal_data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Compute auto-correlation of a signal."""
    n = len(signal_data)
    
    if max_lag is None:
        max_lag = n // 4
    
    corr = signal.correlate(signal_data, signal_data, mode='full')
    lags = signal.correlation_lags(n, n, mode='full')
    
    center = len(corr) // 2
    start = center - max_lag
    end = center + max_lag + 1
    
    corr = corr[start:end]
    lags = lags[start:end]
    
    corr_normalized = corr / corr[center] if corr[center] > 0 else corr
    
    return {
        'autocorrelation': corr_normalized.tolist(),
        'lags': lags.tolist(),
        'peak_lag': int(lags[np.argmax(corr_normalized[1:]) + 1]) if len(corr_normalized) > 1 else 0,
    }


def compute_coherence(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
    sample_rate: float,
    nperseg: int = 256,
) -> Dict[str, Any]:
    """Compute magnitude-squared coherence between two signals."""
    min_len = min(len(signal_a), len(signal_b))
    signal_a = signal_a[:min_len]
    signal_b = signal_b[:min_len]
    
    freqs, coh = signal.coherence(
        np.real(signal_a), np.real(signal_b),
        fs=sample_rate, nperseg=min(nperseg, min_len//4)
    )
    
    return {
        'frequencies': freqs.tolist(),
        'coherence': coh.tolist(),
        'mean_coherence': float(np.mean(coh)),
        'max_coherence': float(np.max(coh)),
    }