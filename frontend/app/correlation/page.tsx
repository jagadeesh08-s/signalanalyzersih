'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { AnalysisJob, CorrelationResult } from '@/lib/types';

export default function CorrelationPage() {
  const [jobIdA, setJobIdA] = useState('');
  const [jobIdB, setJobIdB] = useState('');
  const [result, setResult] = useState<CorrelationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runCorrelation = async () => {
    if (!jobIdA || !jobIdB) { setError('Enter both Job IDs'); return; }
    setLoading(true);
    setError(null);
    try {
      const data = await api.correlate(parseInt(jobIdA), parseInt(jobIdB));
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Correlation failed. Ensure both analyses are in memory.');
    }
    setLoading(false);
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: 800, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Signal Correlation</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14 }}>
        Compare two signals using cross-correlation analysis.
      </p>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 16, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Select Signals</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Signal A (Job ID)</label>
            <input type="text" value={jobIdA} onChange={e => setJobIdA(e.target.value)} className="mono" placeholder="e.g. 1" style={{
              width: '100%', padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', fontSize: 14,
            }} />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Signal B (Job ID)</label>
            <input type="text" value={jobIdB} onChange={e => setJobIdB(e.target.value)} className="mono" placeholder="e.g. 2" style={{
              width: '100%', padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', fontSize: 14,
            }} />
          </div>
        </div>
        {error && <div style={{ padding: '8px 12px', borderRadius: 6, background: 'rgba(239,68,68,0.1)', color: 'var(--status-error)', fontSize: 13, marginBottom: 12 }}>⚠ {error}</div>}
        <button className="btn-primary" onClick={runCorrelation} disabled={loading} style={{ width: '100%' }}>
          {loading ? '◌ Computing...' : '≋ Run Cross-Correlation'}
        </button>
      </div>

      {result && (
        <div className="animate-fade-in">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
            <MetricCard label="Similarity Score" value={`${(result.similarity_score * 100).toFixed(1)}%`} color="var(--signal-green)" />
            <MetricCard label="Peak Correlation" value={result.peak_correlation.toFixed(4)} color="var(--signal-cyan)" />
            <MetricCard label="Time Offset" value={`${(result.time_offset_seconds * 1000).toFixed(2)} ms`} color="var(--signal-orange)" />
          </div>
          <div className="card">
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Detailed Results</h3>
            <InfoRow label="Peak Lag (samples)" value={result.peak_lag.toString()} />
            <InfoRow label="MSE" value={result.mse.toFixed(6)} />
            <InfoRow label="Spectral Similarity" value={`${(result.spectral_similarity * 100).toFixed(1)}%`} />
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="card" style={{ textAlign: 'center' }}>
      <div className="mono" style={{ fontSize: 28, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>{label}</div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-primary)' }}>
      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{label}</span>
      <span className="mono" style={{ fontSize: 13, fontWeight: 500 }}>{value}</span>
    </div>
  );
}
