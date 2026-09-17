'use client';

import { useState } from 'react';

export default function SettingsPage() {
  const [fftSize, setFftSize] = useState('4096');
  const [window, setWindow] = useState('hann');
  const [maxPoints, setMaxPoints] = useState('10000');
  const [maxFileSize, setMaxFileSize] = useState('500');
  const [autoAnalysis, setAutoAnalysis] = useState(true);
  const [autoDemod, setAutoDemod] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState('0.5');
  const [theme, setTheme] = useState('dark');
  const [density, setDensity] = useState('comfortable');

  const toggleTheme = (t: string) => {
    setTheme(t);
    document.documentElement.classList.toggle('light', t === 'light');
    document.documentElement.classList.toggle('dark', t === 'dark');
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: 700, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Settings</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 32, fontSize: 14 }}>
        Configure analysis defaults and application preferences.
      </p>

      {/* Processing */}
      <Section title="Processing">
        <SettingSelect label="Default FFT Size" value={fftSize} onChange={setFftSize} options={['256', '512', '1024', '2048', '4096', '8192', '16384']} />
        <SettingSelect label="Default Window" value={window} onChange={setWindow} options={['hann', 'hamming', 'blackman', 'rectangular', 'bartlett', 'kaiser']} />
        <SettingInput label="Max Visualization Points" value={maxPoints} onChange={setMaxPoints} />
        <SettingInput label="Max File Size (MB)" value={maxFileSize} onChange={setMaxFileSize} />
      </Section>

      {/* Analysis */}
      <Section title="Analysis">
        <SettingToggle label="Automatic Analysis on Upload" value={autoAnalysis} onChange={setAutoAnalysis} description="Start analysis immediately after file upload." />
        <SettingToggle label="Automatic Demodulation" value={autoDemod} onChange={setAutoDemod} description="Run demodulation as part of the analysis pipeline." />
        <SettingInput label="Confidence Threshold" value={confidenceThreshold} onChange={setConfidenceThreshold} />
      </Section>

      {/* Appearance */}
      <Section title="Appearance">
        <SettingSelect label="Theme" value={theme} onChange={toggleTheme} options={['dark', 'light']} />
        <SettingSelect label="Density" value={density} onChange={setDensity} options={['comfortable', 'compact']} />
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 16, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {children}
      </div>
    </div>
  );
}

function SettingSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{label}</span>
      <select value={value} onChange={e => onChange(e.target.value)} style={{
        padding: '6px 12px', borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)',
        color: 'var(--text-primary)', fontSize: 13, minWidth: 140, cursor: 'pointer',
      }}>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

function SettingInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{label}</span>
      <input type="text" value={value} onChange={e => onChange(e.target.value)} className="mono" style={{
        padding: '6px 12px', borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)',
        color: 'var(--text-primary)', fontSize: 13, width: 140, textAlign: 'right',
      }} />
    </div>
  );
}

function SettingToggle({ label, value, onChange, description }: { label: string; value: boolean; onChange: (v: boolean) => void; description?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{label}</div>
        {description && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{description}</div>}
      </div>
      <button onClick={() => onChange(!value)} style={{
        width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
        background: value ? 'var(--signal-cyan)' : 'var(--bg-tertiary)',
        position: 'relative', transition: 'background 0.2s',
      }}>
        <div style={{
          width: 18, height: 18, borderRadius: '50%', background: '#fff',
          position: 'absolute', top: 3,
          left: value ? 23 : 3,
          transition: 'left 0.2s',
        }} />
      </button>
    </div>
  );
}
