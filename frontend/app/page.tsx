'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { AnalysisJob, DashboardStats } from '@/lib/types';

export default function Dashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [statsData, jobsData] = await Promise.all([
        api.getStats().catch(() => null),
        api.listAnalyses(0, 10).catch(() => ({ jobs: [], total: 0 })),
      ]);
      if (statsData) setStats(statsData);
      setRecentJobs(jobsData.jobs || []);
    } catch (e) {
      console.error('Failed to load dashboard data:', e);
    } finally {
      setLoading(false);
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes > 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    if (bytes > 1e3) return `${(bytes / 1e3).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  const formatDuration = (s?: number) => {
    if (!s) return '—';
    if (s < 0.001) return `${(s * 1e6).toFixed(0)} µs`;
    if (s < 1) return `${(s * 1e3).toFixed(1)} ms`;
    return `${s.toFixed(2)} s`;
  };

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <section style={{ marginBottom: 40, textAlign: 'center', padding: '40px 0 20px' }}>
        <h1 style={{ fontSize: 36, fontWeight: 800, marginBottom: 12 }}>
          <span className="gradient-text">Automated RF Signal Analysis</span>
        </h1>
        <p style={{ fontSize: 16, color: 'var(--text-secondary)', maxWidth: 600, margin: '0 auto 28px' }}>
          Turn raw IQ and WAV recordings into actionable signal intelligence.
          Upload a file to begin.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <button className="btn-primary" onClick={() => router.push('/upload')}>
            ↑ Upload Signal
          </button>
        </div>
      </section>

      {/* Stats Cards */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard label="Total Analyses" value={stats?.total_analyses ?? 0} icon="◈" color="var(--signal-cyan)" />
        <StatCard label="Signals Processed" value={stats?.signals_processed ?? 0} icon="✓" color="var(--status-success)" />
        <StatCard label="Average SNR" value={stats?.average_snr != null ? `${stats.average_snr} dB` : '—'} icon="∿" color="var(--signal-orange)" />
        <StatCard label="Most Detected" value={stats?.most_detected_modulation ?? '—'} icon="◉" color="var(--signal-purple)" />
      </section>


      {/* Recent Analyses Table */}
      <section>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: 'var(--text-primary)' }}>
          Recent Analyses
        </h2>
        {recentJobs.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>
            {loading ? 'Loading...' : 'No analyses yet. Upload a signal to get started.'}
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-primary)' }}>
                  {['File', 'Type', 'Duration', 'Modulation', 'Confidence', 'SNR', 'Status', 'Date'].map(h => (
                    <th key={h} style={{ padding: '10px 12px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 500, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recentJobs.map(job => (
                  <tr
                    key={job.id}
                    onClick={() => router.push(`/workspace?id=${job.id}`)}
                    style={{ borderBottom: '1px solid var(--border-primary)', cursor: 'pointer', transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <td style={{ padding: '10px 12px', fontWeight: 500 }}>{job.filename}</td>
                    <td style={{ padding: '10px 12px' }}><span className="mono">{job.file_type.toUpperCase()}</span></td>
                    <td style={{ padding: '10px 12px' }} className="mono">{formatDuration(job.duration)}</td>
                    <td style={{ padding: '10px 12px', color: 'var(--signal-cyan)', fontWeight: 600 }}>{job.detected_modulation || '—'}</td>
                    <td style={{ padding: '10px 12px' }} className="mono">{job.modulation_confidence ? `${(job.modulation_confidence * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ padding: '10px 12px' }} className="mono">{job.snr ? `${job.snr.toFixed(1)} dB` : '—'}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <StatusBadge status={job.status} />
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-tertiary)', fontSize: 12 }}>
                      {job.created_at ? new Date(job.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: string; color: string }) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
      <div style={{
        width: 44, height: 44, borderRadius: 10,
        background: `${color}15`,
        border: `1px solid ${color}30`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 20, color,
      }}>
        {icon}
      </div>
      <div>
        <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>{value}</div>
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{label}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: 'var(--status-success)',
    processing: 'var(--signal-cyan)',
    pending: 'var(--status-pending)',
    failed: 'var(--status-error)',
  };
  const color = colors[status] || 'var(--text-muted)';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 4,
      background: `${color}15`, color,
      fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: color }} />
      {status}
    </span>
  );
}
