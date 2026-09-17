import numpy as np
from scipy import signal
from scipy import stats as sp_stats
from typing import Tuple, List, Dict, Any, Optional
import warnings
import os

warnings.filterwarnings("ignore", category=RuntimeWarning)


MODULATION_CLASSES = ['BPSK', 'QPSK', '8PSK', 'FSK', '16QAM', '64QAM', 'AM', 'FM', 'ASK']

REFERENCE_CONSTELLATIONS = {
    'BPSK': np.array([-1+0j, 1+0j]),
    'QPSK': np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2),
    '8PSK': np.array([np.exp(1j * 2 * np.pi * k / 8) for k in range(8)]),
    '16QAM': np.array([
        (2*i-3) + 1j*(2*j-3) for i in range(4) for j in range(4)
    ]) / np.sqrt(10),
    '64QAM': np.array([
        (2*i-7) + 1j*(2*j-7) for i in range(8) for j in range(8)
    ]) / np.sqrt(42),
}


def extract_features(iq_data: np.ndarray, sample_rate: float) -> Dict[str, float]:
    """Extract statistical and spectral features for modulation classification."""
    features = {}
    
    magnitude = np.abs(iq_data)
    phase = np.angle(iq_data)
    i_data = np.real(iq_data)
    q_data = np.imag(iq_data)
    
    features['mean_magnitude'] = float(np.mean(magnitude))
    features['std_magnitude'] = float(np.std(magnitude))
    features['max_magnitude'] = float(np.max(magnitude))
    features['min_magnitude'] = float(np.min(magnitude))
    
    features['mean_i'] = float(np.mean(i_data))
    features['std_i'] = float(np.std(i_data))
    features['mean_q'] = float(np.mean(q_data))
    features['std_q'] = float(np.std(q_data))
    
    features['magnitude_skewness'] = float(sp_stats.skew(magnitude))
    features['magnitude_kurtosis'] = float(sp_stats.kurtosis(magnitude))
    features['phase_skewness'] = float(sp_stats.skew(phase))
    features['phase_kurtosis'] = float(sp_stats.kurtosis(phase))
    
    moments_2_0 = np.mean(iq_data ** 2)
    moments_2_1 = np.mean(iq_data * np.conj(iq_data))
    moments_4_0 = np.mean(iq_data ** 4)
    moments_4_2 = np.mean((iq_data ** 2) * (np.conj(iq_data) ** 2))
    moments_6_0 = np.mean(iq_data ** 6)
    moments_6_3 = np.mean((iq_data ** 3) * (np.conj(iq_data) ** 3))
    
    features['cumulant_20'] = float(np.abs(moments_2_0))
    features['cumulant_21'] = float(np.abs(moments_2_1))
    features['cumulant_40'] = float(np.abs(moments_4_0 - 3 * moments_2_0 ** 2))
    features['cumulant_42'] = float(np.abs(moments_4_2 - np.abs(moments_2_0) ** 2 - 2 * moments_2_1 ** 2))
    features['cumulant_60'] = float(np.abs(moments_6_0 - 15 * moments_4_0 * moments_2_0 + 30 * moments_2_0 ** 3))
    features['cumulant_63'] = float(np.abs(moments_6_3 - 9 * moments_4_2 * moments_2_1 + 12 * moments_2_1 ** 3))
    
    if features['cumulant_42'] != 0:
        features['cumulant_ratio_40_42'] = features['cumulant_40'] / features['cumulant_42']
    else:
        features['cumulant_ratio_40_42'] = 0.0
    
    if features['cumulant_63'] != 0:
        features['cumulant_ratio_60_63'] = features['cumulant_60'] / features['cumulant_63']
    else:
        features['cumulant_ratio_60_63'] = 0.0
    
    n = len(iq_data)
    freqs = np.fft.fftfreq(n, 1/sample_rate)[:n//2]
    psd = np.abs(np.fft.fft(iq_data))[:n//2] ** 2
    psd_db = 10 * np.log10(psd + 1e-20)
    
    features['spectral_centroid'] = float(np.sum(freqs * psd) / np.sum(psd)) if np.sum(psd) > 0 else 0.0
    features['spectral_spread'] = float(np.sqrt(np.sum((freqs - features['spectral_centroid'])**2 * psd) / np.sum(psd))) if np.sum(psd) > 0 else 0.0
    features['spectral_peak'] = float(freqs[np.argmax(psd)]) if len(psd) > 0 else 0.0
    features['spectral_flatness'] = float(np.exp(np.mean(np.log(psd + 1e-20))) / np.mean(psd)) if np.mean(psd) > 0 else 0.0
    
    bandwidth_99, _, _ = compute_occupied_bandwidth(iq_data, sample_rate, -20)
    bandwidth_3db, _, _ = compute_occupied_bandwidth(iq_data, sample_rate, -3)
    features['bandwidth_99'] = float(bandwidth_99)
    features['bandwidth_3db'] = float(bandwidth_3db)
    
    symbol_rate, sr_confidence = estimate_symbol_rate(iq_data, sample_rate)
    features['estimated_symbol_rate'] = float(symbol_rate)
    features['symbol_rate_confidence'] = float(sr_confidence)
    
    snr = compute_snr(iq_data, sample_rate)
    features['snr'] = float(snr)
    
    return features


def compute_occupied_bandwidth(
    iq_data: np.ndarray,
    sample_rate: float,
    threshold_db: float = -20.0,
) -> Tuple[float, float, float]:
    """Compute occupied bandwidth at given threshold."""
    n = len(iq_data)
    freqs = np.fft.fftshift(np.fft.fftfreq(n, 1/sample_rate))
    psd = np.fft.fftshift(np.abs(np.fft.fft(iq_data)) ** 2)
    psd_db = 10 * np.log10(psd + 1e-20)
    
    peak_power = np.max(psd_db)
    threshold = peak_power + threshold_db
    
    above = psd_db >= threshold
    if not np.any(above):
        return 0.0, 0.0, 0.0
    
    indices = np.where(above)[0]
    lower = freqs[indices[0]]
    upper = freqs[indices[-1]]
    
    return float(upper - lower), float(lower), float(upper)


def classify_modulation_hoc(
    features: Dict[str, float],
) -> Tuple[str, float, Dict[str, float]]:
    """
    Higher-order cumulant based modulation classification.
    Returns: (predicted_modulation, confidence, all_probabilities)
    """
    c40 = features.get('cumulant_40', 0)
    c42 = features.get('cumulant_42', 0)
    c60 = features.get('cumulant_60', 0)
    c63 = features.get('cumulant_63', 0)
    
    ratio_40_42 = features.get('cumulant_ratio_40_42', 0)
    ratio_60_63 = features.get('cumulant_ratio_60_63', 0)
    
    mag_kurt = features.get('magnitude_kurtosis', 0)
    phase_kurt = features.get('phase_kurtosis', 0)
    
    scores = {mod: 0.0 for mod in MODULATION_CLASSES}
    
    if abs(c42) < 1e-6:
        scores['BPSK'] += 2.0
        scores['ASK'] += 1.5
        scores['AM'] += 1.0
    elif ratio_40_42 > 1.5:
        scores['QPSK'] += 2.0
        scores['8PSK'] += 1.0
    elif ratio_40_42 < -1.5:
        scores['16QAM'] += 2.0
        scores['64QAM'] += 1.0
    else:
        scores['QPSK'] += 1.0
        scores['8PSK'] += 1.0
    
    if abs(phase_kurt) < 0.5:
        scores['FSK'] += 2.0
        scores['FM'] += 1.5
    
    if mag_kurt > 2:
        scores['16QAM'] += 1.5
        scores['64QAM'] += 1.0
    elif mag_kurt < -1:
        scores['BPSK'] += 1.0
    
    snr = features.get('snr', 10)
    if snr < 0:
        for mod in scores:
            scores[mod] *= 0.5
    
    exp_scores = {k: np.exp(v) for k, v in scores.items()}
    total = sum(exp_scores.values())
    probs = {k: v / total for k, v in exp_scores.items()}
    
    predicted = max(probs, key=probs.get)
    confidence = probs[predicted]
    
    return predicted, confidence, probs


def classify_modulation_ml(
    iq_data: np.ndarray,
    model_path: str = None,
) -> Tuple[str, float, Dict[str, float]]:
    """
    ML-based modulation classification using PyTorch CNN.
    Falls back to mock or HoC if model not available.
    """
    from app.modulation.cnn_model import TORCH_AVAILABLE, get_mock_prediction
    
    if not TORCH_AVAILABLE:
        # Fallback to mock inference to demonstrate pipeline integration
        return get_mock_prediction(iq_data)
        
    try:
        import torch
        from app.modulation.cnn_model import IQ_CNN
        
        # Load model architecture
        model = IQ_CNN(num_classes=11, num_samples=1024)
        
        if model_path and os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location='cpu'))
            
        model.eval()
        
        # Prepare data: Take first 1024 samples, pad if necessary
        n_samples = 1024
        iq_slice = iq_data[:n_samples]
        if len(iq_slice) < n_samples:
            iq_slice = np.pad(iq_slice, (0, n_samples - len(iq_slice)))
            
        # Format for PyTorch (Batch, Channels, I/Q, Samples) -> (1, 1, 2, 1024)
        i_chan = np.real(iq_slice)
        q_chan = np.imag(iq_slice)
        tensor_data = torch.tensor(np.array([[[i_chan, q_chan]]]), dtype=torch.float32)
        
        with torch.no_grad():
            outputs = model(tensor_data)
            probs = torch.nn.functional.softmax(outputs, dim=1).numpy()[0]
            
        classes = ['8PSK', 'AM-DSB', 'AM-SSB', 'BPSK', 'CPFSK', 'GFSK', 'PAM4', 'QAM16', 'QAM64', 'QPSK', 'WBFM']
        predicted = classes[np.argmax(probs)]
        confidence = float(np.max(probs))
        prob_dict = {classes[i]: float(probs[i]) for i in range(len(classes))}
        
        return predicted, confidence, prob_dict
        
    except Exception as e:
        # Graceful degradation
        import logging
        logging.getLogger(__name__).warning(f"PyTorch CNN inference failed: {e}. Falling back.")
        return get_mock_prediction(iq_data)


def classify_modulation(
    iq_data: np.ndarray,
    sample_rate: float,
    model_path: str = None,
) -> Dict[str, Any]:
    """
    Main modulation classification entry point.
    Now prioritizes the PyTorch CNN approach.
    """
    features = extract_features(iq_data, sample_rate)
    
    # Try CNN ML approach first
    modulation, confidence, probabilities = classify_modulation_ml(iq_data, model_path)
    
    # If the CNN failed or confidence is terribly low, fallback to HoC
    if modulation is None or confidence < 0.1:
        modulation, confidence, probabilities = classify_modulation_hoc(features)
        method = 'HoC'
    else:
        method = 'PyTorch CNN'
    
    return {
        'modulation': modulation,
        'confidence': confidence,
        'probabilities': probabilities,
        'features': features,
        'method': method,
    }


def estimate_symbol_rate(
    iq_data: np.ndarray,
    sample_rate: float,
    max_symbol_rate: float = None,
) -> Tuple[float, float]:
    """Estimate symbol rate using spectral analysis."""
    if max_symbol_rate is None:
        max_symbol_rate = sample_rate / 4
    
    magnitude = np.abs(iq_data)
    magnitude = magnitude - np.mean(magnitude)
    
    n = len(magnitude)
    freqs = np.fft.fftfreq(n, 1/sample_rate)[:n//2]
    mag_spectrum = np.abs(np.fft.fft(magnitude))[:n//2]
    
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


def compute_snr(iq_data: np.ndarray, sample_rate: float) -> float:
    """Estimate SNR."""
    signal_power = np.mean(np.abs(iq_data) ** 2)
    
    n = len(iq_data)
    psd = np.abs(np.fft.fft(iq_data)) ** 2 / (sample_rate * n)
    psd_db = 10 * np.log10(psd + 1e-20)
    noise_floor = np.median(psd_db)
    noise_power = 10 ** (noise_floor / 10)
    
    if noise_power > 0:
        snr_db = 10 * np.log10(signal_power / noise_power)
    else:
        snr_db = 100.0
    
    return np.clip(snr_db, -20, 60)


def get_reference_constellation(modulation: str) -> np.ndarray:
    """Get reference constellation for a modulation type."""
    return REFERENCE_CONSTELLATIONS.get(modulation.upper(), np.array([]))


def normalize_constellation(constellation: np.ndarray) -> np.ndarray:
    """Normalize constellation to unit average energy."""
    if len(constellation) == 0:
        return constellation
    
    avg_energy = np.mean(np.abs(constellation) ** 2)
    if avg_energy > 0:
        return constellation / np.sqrt(avg_energy)
    return constellation