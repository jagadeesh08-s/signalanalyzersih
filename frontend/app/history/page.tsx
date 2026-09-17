'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { AnalysisJob } from '@/lib/types';

export default function HistoryPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);

  useEffect(() => { loadJobs(); }, [page]);

  async function loadJobs() {
    try {
      const data = await api.listAnalyses(page * 20, 20);
      setJobs(data.jobs || []);
      setTotal(data.total || 0);
    } catch (e) { console.error(e); }
  }

  return (
    <div className="animate-fade-in">
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Analysis History</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14 }}>{total} total analyses</p>
      {jobs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>No analyses yet.</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--border-primary)' }}>
              {['ID', 'File', 'Type', 'Modulation', 'Confidence', 'SNR', 'Status', 'Date'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 500, fontSize: 11, textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {jobs.map(job => (
              <tr key={job.id} onClick={() => router.push(`/workspace?id=${job.id}`)} style={{ borderBottom: '1px solid var(--border-primary)', cursor: 'pointer', transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ padding: '10px 12px' }} className="mono">{job.id}</td>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>{job.filename}</td>
                <td style={{ padding: '10px 12px' }} className="mono">{job.file_type.toUpperCase()}</td>
                <td style={{ padding: '10px 12px', color: 'var(--signal-cyan)' }}>{job.detected_modulation || '—'}</td>
                <td style={{ padding: '10px 12px' }} className="mono">{job.modulation_confidence ? `${(job.modulation_confidence * 100).toFixed(1)}%` : '—'}</td>
                <td style={{ padding: '10px 12px' }} className="mono">{job.snr ? `${job.snr.toFixed(1)} dB` : '—'}</td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                    color: job.status === 'completed' ? 'var(--status-success)' : job.status === 'failed' ? 'var(--status-error)' : 'var(--text-muted)',
                    background: job.status === 'completed' ? 'rgba(16,185,129,0.1)' : job.status === 'failed' ? 'rgba(239,68,68,0.1)' : 'rgba(107,114,128,0.1)',
                  }}>{job.status.toUpperCase()}</span>
                </td>
                <td style={{ padding: '10px 12px', color: 'var(--text-tertiary)' }}>{job.created_at ? new Date(job.created_at).toLocaleString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {total > 20 && (
        <div style={{ marginTop: 16, display: 'flex', gap: 8, justifyContent: 'center' }}>
          <button className="btn-secondary" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>← Prev</button>
          <span style={{ padding: '8px 16px', color: 'var(--text-secondary)' }}>Page {page + 1} of {Math.ceil(total / 20)}</span>
          <button className="btn-secondary" onClick={() => setPage(p => p + 1)} disabled={(page + 1) * 20 >= total}>Next →</button>
        </div>
      )}
    </div>
  );
}
