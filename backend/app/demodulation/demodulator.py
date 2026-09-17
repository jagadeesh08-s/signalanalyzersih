import numpy as np
from scipy import signal
from typing import Tuple, Dict, Any, Optional, List
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


def demodulate_bpsk(
    iq_data: np.ndarray,
    symbol_rate: float,
    sample_rate: float,
    carrier_offset: float = 0.0,
) -> Dict[str, Any]:
    """BPSK demodulation with carrier recovery."""
    samples_per_symbol = int(sample_rate / symbol_rate)
    
    if carrier_offset != 0:
        t = np.arange(len(iq_data)) / sample_rate
        iq_data = iq_data * np.exp(-1j * 2 * np.pi * carrier_offset * t)
    
    matched_filter = np.ones(samples_per_symbol) / np.sqrt(samples_per_symbol)
    filtered = np.convolve(iq_data, matched_filter, mode='same')
    
    symbol_indices = np.arange(samples_per_symbol // 2, len(filtered), samples_per_symbol)
    symbol_indices = symbol_indices[symbol_indices < len(filtered)]
    
    symbols = filtered[symbol_indices]
    
    decisions = np.real(symbols) > 0
    bits = decisions.astype(int)
    
    constellation = symbols
    ref_constellation = np.array([-1+0j, 1+0j])
    distances = np.abs(constellation[:, np.newaxis] - ref_constellation)
    symbol_decisions = np.argmin(distances, axis=1)
    
    evm = np.mean(np.abs(constellation - ref_constellation[symbol_decisions]) ** 2)
    evm_db = 10 * np.log10(evm) if evm > 0 else -60
    
    return {
        'modulation': 'BPSK',
        'symbols': symbols.tolist(),
        'bits': bits.tolist(),
        'symbol_decisions': symbol_decisions.tolist(),
        'evm_db': float(evm_db),
        'samples_per_symbol': samples_per_symbol,
        'num_symbols': len(symbols),
        'quality': float(np.exp(evm_db / 10)) if evm_db < 0 else 0.0,
    }


def demodulate_qpsk(
    iq_data: np.ndarray,
    symbol_rate: float,
    sample_rate: float,
    carrier_offset: float = 0.0,
) -> Dict[str, Any]:
    """QPSK demodulation with carrier recovery."""
    samples_per_symbol = int(sample_rate / symbol_rate)
    
    if carrier_offset != 0:
        t = np.arange(len(iq_data)) / sample_rate
        iq_data = iq_data * np.exp(-1j * 2 * np.pi * carrier_offset * t)
    
    fourth_power = iq_data ** 4
    carrier_phase = np.angle(np.mean(fourth_power)) / 4
    iq_data = iq_data * np.exp(-1j * carrier_phase)
    
    matched_filter = np.ones(samples_per_symbol) / np.sqrt(samples_per_symbol)
    filtered = np.convolve(iq_data, matched_filter, mode='same')
    
    symbol_indices = np.arange(samples_per_symbol // 2, len(filtered), samples_per_symbol)
    symbol_indices = symbol_indices[symbol_indices < len(filtered)]
    
    symbols = filtered[symbol_indices]
    
    ref_constellation = np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2)
    distances = np.abs(symbols[:, np.newaxis] - ref_constellation)
    symbol_decisions = np.argmin(distances, axis=1)
    
    bit_mapping = {0: [0, 0], 1: [0, 1], 2: [1, 1], 3: [1, 0]}
    bits = []
    for d in symbol_decisions:
        bits.extend(bit_mapping[d])
    
    evm = np.mean(np.abs(symbols - ref_constellation[symbol_decisions]) ** 2)
    evm_db = 10 * np.log10(evm) if evm > 0 else -60
    
    return {
        'modulation': 'QPSK',
        'symbols': symbols.tolist(),
        'bits': bits,
        'symbol_decisions': symbol_decisions.tolist(),
        'evm_db': float(evm_db),
        'samples_per_symbol': samples_per_symbol,
        'num_symbols': len(symbols),
        'carrier_phase_offset': float(carrier_phase),
        'quality': float(np.exp(evm_db / 10)) if evm_db < 0 else 0.0,
    }


def demodulate_psk8(
    iq_data: np.ndarray,
    symbol_rate: float,
    sample_rate: float,
    carrier_offset: float = 0.0,
) -> Dict[str, Any]:
    """8-PSK demodulation."""
    samples_per_symbol = int(sample_rate / symbol_rate)
    
    if carrier_offset != 0:
        t = np.arange(len(iq_data)) / sample_rate
        iq_data = iq_data * np.exp(-1j * 2 * np.pi * carrier_offset * t)
    
    eighth_power = iq_data ** 8
    carrier_phase = np.angle(np.mean(eighth_power)) / 8
    iq_data = iq_data * np.exp(-1j * carrier_phase)
    
    matched_filter = np.ones(samples_per_symbol) / np.sqrt(samples_per_symbol)
    filtered = np.convolve(iq_data, matched_filter, mode='same')
    
    symbol_indices = np.arange(samples_per_symbol // 2, len(filtered), samples_per_symbol)
    symbol_indices = symbol_indices[symbol_indices < len(filtered)]
    
    symbols = filtered[symbol_indices]
    
    ref_constellation = np.array([np.exp(1j * 2 * np.pi * k / 8) for k in range(8)])
    distances = np.abs(symbols[:, np.newaxis] - ref_constellation)
    symbol_decisions = np.argmin(distances, axis=1)
    
    bit_mapping = {
        0: [0, 0, 0], 1: [0, 0, 1], 2: [0, 1, 1], 3: [0, 1, 0],
        4: [1, 1, 0], 5: [1, 1, 1], 6: [1, 0, 1], 7: [1, 0, 0],
    }
    bits = []
    for d in symbol_decisions:
        bits.extend(bit_mapping[d])
    
    evm = np.mean(np.abs(symbols - ref_constellation[symbol_decisions]) ** 2)
    evm_db = 10 * np.log10(evm) if evm > 0 else -60
    
    return {
        'modulation': '8PSK',
        'symbols': symbols.tolist(),
        'bits': bits,
        'symbol_decisions': symbol_decisions.tolist(),
        'evm_db': float(evm_db),
        'samples_per_symbol': samples_per_symbol,
        'num_symbols': len(symbols),
        'quality': float(np.exp(evm_db / 10)) if evm_db < 0 else 0.0,
    }


def demodulate_fsk(
    iq_data: np.ndarray,
    symbol_rate: float,
    sample_rate: float,
    freq_deviation: float = None,
) -> Dict[str, Any]:
    """FSK demodulation using frequency discrimination."""
    samples_per_symbol = int(sample_rate / symbol_rate)
    
    phase = np.unwrap(np.angle(iq_data))
    inst_freq = np.diff(phase) * sample_rate / (2 * np.pi)
    inst_freq = np.append(inst_freq, inst_freq[-1])
    
    symbol_indices = np.arange(samples_per_symbol // 2, len(inst_freq), samples_per_symbol)
    symbol_indices = symbol_indices[symbol_indices < len(inst_freq)]
    
    symbol_freqs = inst_freq[symbol_indices]
    
    center_freq = np.mean(symbol_freqs)
    if freq_deviation is None:
        freq_deviation = np.std(symbol_freqs) * 2
    
    decisions = (symbol_freqs > center_freq).astype(int)
    bits = decisions.tolist()
    
    return {
        'modulation': 'FSK',
        'symbol_freqs': symbol_freqs.tolist(),
        'bits': bits,
        'center_freq': float(center_freq),
        'freq_deviation': float(freq_deviation),
        'samples_per_symbol': samples_per_symbol,
        'num_symbols': len(decisions),
        'quality': 0.8,
    }


def demodulate_qam16(
    iq_data: np.ndarray,
    symbol_rate: float,
    sample_rate: float,
    carrier_offset: float = 0.0,
) -> Dict[str, Any]:
    """16-QAM demodulation."""
    samples_per_symbol = int(sample_rate / symbol_rate)
    
    if carrier_offset != 0:
        t = np.arange(len(iq_data)) / sample_rate
        iq_data = iq_data * np.exp(-1j * 2 * np.pi * carrier_offset * t)
    
    fourth_power = iq_data ** 4
    carrier_phase = np.angle(np.mean(fourth_power)) / 4
    iq_data = iq_data * np.exp(-1j * carrier_phase)
    
    magnitude = np.abs(iq_data)
    magnitude = magnitude - np.mean(magnitude)
    magnitude = magnitude / np.std(magnitude) if np.std(magnitude) > 0 else magnitude
    
    matched_filter = np.ones(samples_per_symbol) / np.sqrt(samples_per_symbol)
    filtered = np.convolve(iq_data, matched_filter, mode='same')
    
    symbol_indices = np.arange(samples_per_symbol // 2, len(filtered), samples_per_symbol)
    symbol_indices = symbol_indices[symbol_indices < len(filtered)]
    
    symbols = filtered[symbol_indices]
    
    ref_constellation = np.array([
        (2*i-3) + 1j*(2*j-3) for i in range(4) for j in range(4)
    ]) / np.sqrt(10)
    
    distances = np.abs(symbols[:, np.newaxis] - ref_constellation)
    symbol_decisions = np.argmin(distances, axis=1)
    
    bits = []
    for d in symbol_decisions:
        i = d // 4
        j = d % 4
        i_bits = [(i >> 1) & 1, i & 1]
        j_bits = [(j >> 1) & 1, j & 1]
        bits.extend(i_bits + j_bits)
    
    evm = np.mean(np.abs(symbols - ref_constellation[symbol_decisions]) ** 2)
    evm_db = 10 * np.log10(evm) if evm > 0 else -60
    
    return {
        'modulation': '16QAM',
        'symbols': symbols.tolist(),
        'bits': bits,
        'symbol_decisions': symbol_decisions.tolist(),
        'evm_db': float(evm_db),
        'samples_per_symbol': samples_per_symbol,
        'num_symbols': len(symbols),
        'quality': float(np.exp(evm_db / 10)) if evm_db < 0 else 0.0,
    }


def demodulate_am(
    iq_data: np.ndarray,
    sample_rate: float,
) -> Dict[str, Any]:
    """AM demodulation (envelope detection)."""
    envelope = np.abs(iq_data)
    
    b, a = signal.butter(4, 0.01, btype='high')
    audio = signal.filtfilt(b, a, envelope)
    
    return {
        'modulation': 'AM',
        'envelope': envelope.tolist(),
        'audio': audio.tolist(),
        'carrier_freq': 0.0,
        'quality': 0.7,
    }


def demodulate_fm(
    iq_data: np.ndarray,
    sample_rate: float,
) -> Dict[str, Any]:
    """FM demodulation (frequency discrimination)."""
    phase = np.unwrap(np.angle(iq_data))
    inst_freq = np.diff(phase) * sample_rate / (2 * np.pi)
    inst_freq = np.append(inst_freq, inst_freq[-1])
    
    b, a = signal.butter(4, 0.01, btype='high')
    audio = signal.filtfilt(b, a, inst_freq)
    
    return {
        'modulation': 'FM',
        'instantaneous_frequency': inst_freq.tolist(),
        'audio': audio.tolist(),
        'quality': 0.7,
    }


DEMODULATORS = {
    'BPSK': demodulate_bpsk,
    'QPSK': demodulate_qpsk,
    '8PSK': demodulate_psk8,
    'FSK': demodulate_fsk,
    '16QAM': demodulate_qam16,
    'AM': demodulate_am,
    'FM': demodulate_fm,
}


def demodulate(
    iq_data: np.ndarray,
    modulation: str,
    symbol_rate: float = None,
    sample_rate: float = 1_000_000,
    carrier_offset: float = 0.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Main demodulation entry point.
    """
    modulation = modulation.upper()
    
    if modulation not in DEMODULATORS:
        return {
            'error': f'Unsupported modulation: {modulation}',
            'modulation': modulation,
            'bits': [],
            'quality': 0.0,
        }
    
    if modulation in ['BPSK', 'QPSK', '8PSK', '16QAM'] and symbol_rate is None:
        return {
            'error': f'Symbol rate required for {modulation} demodulation',
            'modulation': modulation,
            'bits': [],
            'quality': 0.0,
        }
    
    demodulator = DEMODULATORS[modulation]
    
    try:
        if modulation in ['BPSK', 'QPSK', '8PSK', '16QAM']:
            result = demodulator(iq_data, symbol_rate, sample_rate, carrier_offset)
        elif modulation == 'FSK':
            result = demodulator(iq_data, symbol_rate, sample_rate, kwargs.get('freq_deviation'))
        else:
            result = demodulator(iq_data, sample_rate)
        
        result['success'] = True
        return result
    except Exception as e:
        return {
            'error': str(e),
            'modulation': modulation,
            'bits': [],
            'quality': 0.0,
            'success': False,
        }


def bits_to_bytes(bits: List[int]) -> bytes:
    """Convert bit list to bytes."""
    if len(bits) % 8 != 0:
        bits = bits + [0] * (8 - len(bits) % 8)
    
    bytes_data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        bytes_data.append(byte)
    
    return bytes(bytes_data)


def bytes_to_hex(bytes_data: bytes) -> str:
    """Convert bytes to hex string."""
    return ' '.join(f'{b:02X}' for b in bytes_data)


def bytes_to_ascii(bytes_data: bytes) -> str:
    """Convert bytes to ASCII string (non-printable as .)."""
    return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in bytes_data)