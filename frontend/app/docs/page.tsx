'use client';

export default function DocsPage() {
  return (
    <div className="animate-fade-in" style={{ maxWidth: 800, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Documentation</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 32, fontSize: 14 }}>
        RF and DSP concepts explained for engineering students.
      </p>

      <DocSection title="What is IQ Data?" id="iq">
        <p>IQ (In-phase and Quadrature) data is a way to represent radio signals digitally using two components:</p>
        <ul>
          <li><strong>I (In-phase)</strong> — the real component of the signal, aligned with the carrier wave.</li>
          <li><strong>Q (Quadrature)</strong> — the imaginary component, shifted 90° from the carrier.</li>
        </ul>
        <p>Together, I and Q form a <strong>complex baseband signal</strong>: <code className="mono">s(t) = I(t) + j·Q(t)</code></p>
        <p>This representation preserves both amplitude and phase information, which is essential for digital modulation analysis. IQ files typically store interleaved I and Q samples: <code className="mono">I₁ Q₁ I₂ Q₂ I₃ Q₃ ...</code></p>
      </DocSection>

      <DocSection title="What is WAV?" id="wav">
        <p>WAV (Waveform Audio File Format) is a standard audio container. In SDR contexts, stereo WAV files are often used to store IQ data — the left channel carries I and the right channel carries Q.</p>
        <p>WAV files include metadata (sample rate, bit depth, channels) that IQ files typically lack.</p>
      </DocSection>

      <DocSection title="What is FFT?" id="fft">
        <p>The <strong>Fast Fourier Transform</strong> converts a time-domain signal into its frequency-domain representation. It reveals which frequencies are present and their relative power.</p>
        <p>Key parameters:</p>
        <ul>
          <li><strong>FFT Size (N)</strong> — number of samples per transform. Larger N = finer frequency resolution but slower computation.</li>
          <li><strong>Window Function</strong> — applied before FFT to reduce spectral leakage. Common choices: Hann, Hamming, Blackman.</li>
        </ul>
        <p>The frequency resolution is: <code className="mono">Δf = sample_rate / N</code></p>
      </DocSection>

      <DocSection title="What is SNR?" id="snr">
        <p><strong>Signal-to-Noise Ratio</strong> measures the signal power relative to the noise power, expressed in decibels (dB).</p>
        <p><code className="mono">SNR = 10 · log₁₀(P_signal / P_noise)</code></p>
        <ul>
          <li><strong>&gt;20 dB</strong> — excellent quality, reliable demodulation.</li>
          <li><strong>10–20 dB</strong> — moderate quality, some errors possible.</li>
          <li><strong>&lt;10 dB</strong> — poor quality, significant errors likely.</li>
          <li><strong>&lt;0 dB</strong> — signal below noise floor.</li>
        </ul>
      </DocSection>

      <DocSection title="What is Bandwidth?" id="bandwidth">
        <p><strong>Bandwidth</strong> is the range of frequencies a signal occupies. The <strong>-3dB bandwidth</strong> is measured where the power spectral density drops 3dB below the peak — this is where the signal has half its peak power.</p>
        <p>Occupied bandwidth helps identify the signal type and is related to the symbol rate and modulation scheme.</p>
      </DocSection>

      <DocSection title="What is Modulation?" id="modulation">
        <p><strong>Modulation</strong> is the process of encoding information onto a carrier wave by varying its amplitude, frequency, or phase.</p>
        <p>Common digital modulation types:</p>
        <ul>
          <li><strong>BPSK</strong> — Binary Phase Shift Keying. 2 symbols, 1 bit/symbol. Phase shifts between 0° and 180°.</li>
          <li><strong>QPSK</strong> — Quadrature PSK. 4 symbols, 2 bits/symbol. Phase shifts at 45°, 135°, 225°, 315°.</li>
          <li><strong>8PSK</strong> — 8 Phase Shift Keying. 8 symbols, 3 bits/symbol.</li>
          <li><strong>FSK</strong> — Frequency Shift Keying. Information encoded in frequency changes.</li>
          <li><strong>16QAM</strong> — 16-Quadrature Amplitude Modulation. 16 symbols, 4 bits/symbol. Both amplitude and phase vary.</li>
          <li><strong>AM</strong> — Amplitude Modulation. Analog modulation varying the carrier amplitude.</li>
          <li><strong>FM</strong> — Frequency Modulation. Analog modulation varying the carrier frequency.</li>
        </ul>
      </DocSection>

      <DocSection title="What is Demodulation?" id="demodulation">
        <p><strong>Demodulation</strong> is the reverse process — extracting the original information from a modulated signal. Steps typically include:</p>
        <ol>
          <li><strong>Carrier recovery</strong> — synchronize to the carrier frequency and phase.</li>
          <li><strong>Matched filtering</strong> — optimize SNR for symbol detection.</li>
          <li><strong>Symbol timing recovery</strong> — sample at the optimal point within each symbol.</li>
          <li><strong>Decision making</strong> — map received symbols to the nearest reference constellation point.</li>
          <li><strong>Bit extraction</strong> — convert symbols to binary data.</li>
        </ol>
      </DocSection>

      <DocSection title="What is a Constellation Diagram?" id="constellation">
        <p>A <strong>constellation diagram</strong> plots the received IQ symbols on a 2D plane (I axis horizontal, Q axis vertical). Each point represents one symbol decision.</p>
        <p>A clean constellation has tight clusters around the reference points. Noise, interference, and distortion cause the clusters to spread out, increasing symbol error probability.</p>
        <p><strong>EVM (Error Vector Magnitude)</strong> measures how far received symbols deviate from ideal positions.</p>
      </DocSection>

      <DocSection title="What is FEC?" id="fec">
        <p><strong>Forward Error Correction</strong> adds redundancy to transmitted data so the receiver can detect and correct errors without retransmission.</p>
        <ul>
          <li><strong>Hamming codes</strong> — simple block codes that correct single-bit errors.</li>
          <li><strong>Convolutional codes</strong> — encode data using shift registers, decoded with the Viterbi algorithm.</li>
          <li><strong>Reed-Solomon</strong> — block codes effective against burst errors, used in DVB, QR codes.</li>
          <li><strong>LDPC</strong> — near-capacity codes used in modern standards (5G, Wi-Fi 6, DVB-S2).</li>
        </ul>
      </DocSection>

      <DocSection title="Symbol Rate" id="symbol-rate">
        <p>The <strong>symbol rate</strong> (baud rate) is the number of symbol changes per second, measured in symbols/second (sym/s or baud).</p>
        <p>Relationship to bit rate: <code className="mono">bit_rate = symbol_rate × bits_per_symbol</code></p>
        <p>For example, QPSK at 100 ksym/s carries 200 kbit/s (2 bits per symbol).</p>
      </DocSection>
    </div>
  );
}

function DocSection({ title, id, children }: { title: string; id: string; children: React.ReactNode }) {
  return (
    <section id={id} className="card" style={{ marginBottom: 16 }}>
      <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: 'var(--signal-cyan)' }}>{title}</h2>
      <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)' }}>
        <style jsx>{`
          p { margin-bottom: 12px; }
          ul, ol { margin: 8px 0 12px 20px; }
          li { margin-bottom: 6px; }
          code { background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
        `}</style>
        {children}
      </div>
    </section>
  );
}
