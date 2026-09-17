'use client';

import { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiUpload } from '@/lib/api';

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // IQ Config
  const [dtype, setDtype] = useState('int16');
  const [iqOrder, setIqOrder] = useState('IQ');
  const [endianness, setEndianness] = useState('little');
  const [sampleRate, setSampleRate] = useState('1000000');
  const [centerFreq, setCenterFreq] = useState('0');
  const [showConfig, setShowConfig] = useState(false);

  const ALLOWED = ['.iq', '.wav', '.bin', '.raw'];
  const MAX_SIZE = 500 * 1024 * 1024;

  const validateFile = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) return `Unsupported file type: ${ext}. Supported: ${ALLOWED.join(', ')}`;
    if (f.size > MAX_SIZE) return `File too large: ${(f.size / 1e6).toFixed(1)} MB. Max: 500 MB`;
    if (f.size === 0) return 'File is empty';
    return null;
  };

  const onFileSelect = (f: File) => {
    const err = validateFile(f);
    if (err) { setError(err); return; }
    setFile(f);
    setError(null);
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (ext !== 'wav') setShowConfig(true);
    else setShowConfig(false);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files[0]) onFileSelect(e.dataTransfer.files[0]);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(10);
    try {
      const job = await apiUpload(file, {
        dtype,
        iq_order: iqOrder,
        endianness,
        sample_rate: parseFloat(sampleRate),
        center_frequency: parseFloat(centerFreq),
        scale_factor: 1.0,
        auto_analyze: true,
      });
      setProgress(100);
      router.push(`/workspace?id=${job.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed');
      setUploading(false);
      setProgress(0);
    }
  };

  const formatSize = (bytes: number) => bytes > 1e6 ? `${(bytes / 1e6).toFixed(2)} MB` : `${(bytes / 1e3).toFixed(1)} KB`;

  return (
    <div className="animate-fade-in" style={{ maxWidth: 800, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Upload & Analyze</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14 }}>
        Upload an IQ, WAV, BIN, or RAW file to begin automated signal analysis.
      </p>

      {/* Drop Zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragActive ? 'var(--signal-cyan)' : 'var(--border-secondary)'}`,
          borderRadius: 16,
          padding: '60px 40px',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragActive ? 'rgba(0,212,255,0.05)' : 'var(--bg-card)',
          transition: 'all 0.2s',
          marginBottom: 24,
        }}
      >
        <div style={{ fontSize: 48, marginBottom: 12 }}>↑</div>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
          {file ? file.name : 'Drop file here or click to browse'}
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Supported: .IQ, .WAV, .BIN, .RAW • Max 500 MB
        </div>
        {file && (
          <div style={{ marginTop: 16, display: 'flex', gap: 16, justifyContent: 'center', fontSize: 13 }}>
            <span className="mono" style={{ color: 'var(--text-secondary)' }}>Size: {formatSize(file.size)}</span>
            <span className="mono" style={{ color: 'var(--text-secondary)' }}>Type: {file.name.split('.').pop()?.toUpperCase()}</span>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".iq,.wav,.bin,.raw"
          style={{ display: 'none' }}
          onChange={e => e.target.files?.[0] && onFileSelect(e.target.files[0])}
        />
      </div>

      {error && (
        <div style={{
          padding: '12px 16px', borderRadius: 8,
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          color: 'var(--status-error)', fontSize: 13, marginBottom: 16,
        }}>
          ⚠ {error}
        </div>
      )}

      {/* IQ Config */}
      {showConfig && file && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>IQ File Configuration</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            <ConfigSelect label="Data Type" value={dtype} onChange={setDtype} options={['int8', 'int16', 'int32', 'float32', 'uint8', 'uint16']} />
            <ConfigSelect label="IQ Order" value={iqOrder} onChange={setIqOrder} options={['IQ', 'QI']} />
            <ConfigSelect label="Endianness" value={endianness} onChange={setEndianness} options={['little', 'big']} />
            <ConfigInput label="Sample Rate (Hz)" value={sampleRate} onChange={setSampleRate} />
            <ConfigInput label="Center Frequency (Hz)" value={centerFreq} onChange={setCenterFreq} />
          </div>
        </div>
      )}

      {/* Upload Button */}
      {file && (
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button className="btn-primary" onClick={handleUpload} disabled={uploading} style={{ flex: 1 }}>
            {uploading ? `Uploading... ${progress}%` : '⬆ Upload & Analyze'}
          </button>
          <button className="btn-secondary" onClick={() => { setFile(null); setShowConfig(false); setError(null); }}>
            Cancel
          </button>
        </div>
      )}

      {uploading && (
        <div style={{ marginTop: 16 }}>
          <div style={{ height: 4, borderRadius: 2, background: 'var(--bg-tertiary)', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 2,
              background: 'var(--gradient-primary)',
              width: `${progress}%`,
              transition: 'width 0.3s ease',
            }} />
          </div>
        </div>
      )}
    </div>
  );
}

function ConfigSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{
          width: '100%', padding: '8px 12px', borderRadius: 6,
          background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)',
          color: 'var(--text-primary)', fontSize: 13,
        }}
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

function ConfigInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</label>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        className="mono"
        style={{
          width: '100%', padding: '8px 12px', borderRadius: 6,
          background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)',
          color: 'var(--text-primary)', fontSize: 13,
        }}
      />
    </div>
  );
}
