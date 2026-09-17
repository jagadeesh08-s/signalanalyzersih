import numpy as np
import scipy.io.wavfile as wavfile
import os
import struct

def generate_fsk(duration=0.1, sample_rate=100000, symbol_rate=10000, f0=-15000, f1=15000):
    t = np.arange(int(duration * sample_rate)) / sample_rate
    num_symbols = int(duration * symbol_rate)
    symbols = np.random.randint(0, 2, num_symbols)
    
    # Repeat symbols to match sample rate
    samps_per_sym = int(sample_rate / symbol_rate)
    symbol_stream = np.repeat(symbols, samps_per_sym)
    
    # Generate FSK
    phase = 0
    signal = np.zeros(len(t), dtype=np.complex64)
    for i in range(len(t)):
        freq = f1 if symbol_stream[i] == 1 else f0
        phase += 2 * np.pi * freq / sample_rate
        signal[i] = np.exp(1j * phase)
        
    # Add noise
    noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
    return signal + noise

def generate_bpsk(duration=0.1, sample_rate=100000, symbol_rate=10000):
    t = np.arange(int(duration * sample_rate)) / sample_rate
    num_symbols = int(duration * symbol_rate)
    symbols = np.random.randint(0, 2, num_symbols) * 2 - 1 # -1 or 1
    
    samps_per_sym = int(sample_rate / symbol_rate)
    symbol_stream = np.repeat(symbols, samps_per_sym)
    
    # Baseband BPSK
    signal = symbol_stream.astype(np.complex64)
    
    # Add noise
    noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.2
    return signal + noise

os.makedirs("test_signals", exist_ok=True)

# 1. Generate FSK .wav file (Stereo: I=Left, Q=Right)
fsk = generate_fsk()
fsk_normalized = np.int16(fsk / np.max(np.abs(fsk)) * 32767)
fsk_stereo = np.column_stack((np.real(fsk_normalized), np.imag(fsk_normalized)))
wavfile.write("test_signals/test_fsk_signal.wav", 100000, fsk_stereo)

# 2. Generate BPSK .iq file (complex64 binary)
bpsk = generate_bpsk()
with open("test_signals/test_bpsk_signal.iq", "wb") as f:
    f.write(bpsk.tobytes())

print("Successfully generated test_fsk_signal.wav and test_bpsk_signal.iq in the test_signals folder!")
