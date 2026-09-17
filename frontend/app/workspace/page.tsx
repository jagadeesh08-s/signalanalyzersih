'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, getWsUrl } from '@/lib/api';
import type { AnalysisJob, WaveformData, SpectrumData, SpectrogramData, ConstellationData, SignalParameter, BitstreamData } from '@/lib/types';
import Plot from '@/components/PlotlyWrapper';

const TABS = [
  { key: 'overview', label: 'Overview', icon: '◈' },
  { key: 'waveform', label: 'Waveform', icon: '∿' },
  { key: 'spectrum', label: 'Spectrum', icon: '▮' },
  { key: 'waterfall', label: 'Waterfall', icon: '▦' },
  { key: 'constellation', label: 'Constellation', icon: '✦' },
  { key: 'parameters', label: 'Parameters', icon: '⚙' },
  { key: 'modulation', label: 'Modulation', icon: '◉' },
  { key: 'demodulation', label: 'Demodulation', icon: '⇌' },
  { key: 'bitstream', label: 'Bitstream', icon: '▪' },
  { key: 'report', label: 'Report', icon: '▤' },
];

function WorkspaceContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get('id');
  const [tab, setTab] = useState('overview');
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [params, setParams] = useState<SignalParameter[]>([]);
  const [waveform, setWaveform] = useState<WaveformData | null>(null);
  const [spectrum, setSpectrum] = useState<SpectrumData | null>(null);
  const [spectrogram, setSpectrogram] = useState<SpectrogramData | null>(null);
  const [constellation, setConstellation] = useState<ConstellationData | null>(null);
  const [bitstream, setBitstream] = useState<BitstreamData | null>(null);
  const [wsStatus, setWsStatus] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const id = parseInt(jobId);
    loadJob(id);
    connectWs(id);
    return () => { wsRef.current?.close(); };
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    const id = parseInt(jobId);
    if (tab === 'waveform' && !waveform) api.getWaveform(id).then(setWaveform).catch(() => {});
    if (tab === 'spectrum' && !spectrum) api.getSpectrum(id).then(setSpectrum).catch(() => {});
    if (tab === 'waterfall' && !spectrogram) api.getSpectrogram(id).then(setSpectrogram).catch(() => {});
    if (tab === 'constellation' && !constellation) api.getConstellation(id).then(setConstellation).catch(() => {});
    if (tab === 'parameters' && params.length === 0) api.getParameters(id).then(setParams).catch(() => {});
    if (tab === 'bitstream' && !bitstream) api.getBitstream(id).then(setBitstream).catch(() => {});
  }, [tab, jobId]);

  async function loadJob(id: number) {
    try {
      const data = await api.getAnalysis(id);
      setJob(data);
      if (data.status === 'completed') {
        api.getParameters(id).then(setParams).catch(() => {});
      }
    } catch (e) { console.error(e); }
  }

  function connectWs(id: number) {
    try {
      const ws = new WebSocket(getWsUrl(id));
      ws.onmessage = (evt) => {
        const data = JSON.parse(evt.data);
        setWsStatus(data.message);
        setJob(prev => prev ? { ...prev, progress: data.progress, current_stage: data.message, status: data.status === 'completed' ? 'completed' : prev.status } : prev);
        if (data.status === 'completed') {
          loadJob(id);
          ws.close();
        }
      };
      wsRef.current = ws;
    } catch { /* WS not available */ }
  }

  if (!jobId) return <div className="card" style={{ textAlign: 'center', padding: 60 }}>No analysis selected. Go to Dashboard to start one.</div>;

  return (
    <div style={{ display: 'flex', gap: 0, height: 'calc(100vh - var(--header-height) - 48px)' }}>
      {/* Left Tab Bar */}
      <div style={{
        width: 180, flexShrink: 0,
        background: 'var(--bg-secondary)',
        borderRadius: '12px 0 0 12px',
        border: '1px solid var(--border-primary)',
        borderRight: 'none',
        padding: '8px',
        overflowY: 'auto',
      }}>
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              width: '100%', padding: '9px 12px', borderRadius: 8,
              border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: tab === t.key ? 600 : 400,
              color: tab === t.key ? 'var(--signal-cyan)' : 'var(--text-secondary)',
              background: tab === t.key ? 'rgba(0,212,255,0.08)' : 'transparent',
              textAlign: 'left', transition: 'all 0.15s', marginBottom: 2,
            }}
          >
            <span style={{ fontSize: 14 }}>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div style={{
        flex: 1,
        background: 'var(--bg-card)',
        borderRadius: '0 12px 12px 0',
        border: '1px solid var(--border-primary)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* Top Bar */}
        <div style={{
          padding: '12px 20px',
          borderBottom: '1px solid var(--border-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontWeight: 600, fontSize: 15 }}>{job?.filename || 'Loading...'}</span>
            {job?.status === 'processing' && (
              <span className="animate-pulse-glow" style={{ color: 'var(--signal-cyan)', fontSize: 12 }}>
                ◌ {wsStatus || job.current_stage || 'Processing...'}
              </span>
            )}
            {job?.status === 'completed' && <span style={{ color: 'var(--status-success)', fontSize: 12 }}>✓ Complete</span>}
            {job?.status === 'failed' && <span style={{ color: 'var(--status-error)', fontSize: 12 }}>✕ Failed</span>}
          </div>
          {job?.status === 'processing' && (
            <div style={{ width: 120, height: 4, borderRadius: 2, background: 'var(--bg-tertiary)' }}>
              <div style={{ height: '100%', borderRadius: 2, background: 'var(--gradient-primary)', width: `${job.progress}%`, transition: 'width 0.3s' }} />
            </div>
          )}
        </div>

        {/* Summary Metrics Row */}
        {job?.status === 'completed' && (
          <div style={{
            padding: '10px 20px',
            borderBottom: '1px solid var(--border-primary)',
            display: 'flex', gap: 24, fontSize: 12,
          }}>
            <MetricPill label="SNR" value={job.snr != null ? `${job.snr.toFixed(1)} dB` : '—'} tag="ESTIMATED" />
            <MetricPill label="Bandwidth" value={job.bandwidth ? `${(job.bandwidth / 1e3).toFixed(1)} kHz` : '—'} tag="ESTIMATED" />
            <MetricPill label="Modulation" value={job.detected_modulation || '—'} tag="ML CLASSIFICATION" />
            <MetricPill label="Confidence" value={job.modulation_confidence ? `${(job.modulation_confidence * 100).toFixed(1)}%` : '—'} tag="ML CLASSIFICATION" />
            <MetricPill label="Symbol Rate" value={job.symbol_rate ? `${(job.symbol_rate / 1e3).toFixed(1)} ksym/s` : '—'} tag="ESTIMATED" />
          </div>
        )}

        {/* Tab Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
          {tab === 'overview' && <OverviewTab job={job} params={params} />}
          {tab === 'waveform' && <WaveformTab data={waveform} />}
          {tab === 'spectrum' && <SpectrumTab data={spectrum} />}
          {tab === 'waterfall' && <WaterfallTab data={spectrogram} />}
          {tab === 'constellation' && <ConstellationTab data={constellation} />}
          {tab === 'parameters' && <ParametersTab params={params} />}
          {tab === 'modulation' && <ModulationTab job={job} />}
          {tab === 'demodulation' && <DemodulationTab job={job} jobId={parseInt(jobId)} />}
          {tab === 'bitstream' && <BitstreamTab data={bitstream} />}
          {tab === 'report' && <ReportTab job={job} jobId={parseInt(jobId)} />}
        </div>
      </div>
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense fallback={<div className="card" style={{ textAlign: 'center', padding: 60 }}>Loading workspace...</div>}>
      <WorkspaceContent />
    </Suspense>
  );
}

// ─── Sub Components ───

function MetricPill({ label, value, tag }: { label: string; value: string; tag: string }) {
  const tagClass = tag === 'ESTIMATED' ? 'badge-estimated' : tag === 'ML CLASSIFICATION' ? 'badge-ml' : tag === 'MEASURED' ? 'badge-measured' : 'badge-metadata';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ color: 'var(--text-tertiary)' }}>{label}:</span>
      <span className="mono" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{value}</span>
      <span className={`badge ${tagClass}`} style={{ fontSize: 8 }}>{tag}</span>
    </div>
  );
}

function OverviewTab({ job, params }: { job: AnalysisJob | null; params: SignalParameter[] }) {
  if (!job) return <div>Loading...</div>;
  return (
    <div className="animate-fade-in">
      {/* Pipeline Progress */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Processing Pipeline</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {['Upload', 'Parse', 'Preprocess', 'Detect', 'Extract', 'Classify', 'Demodulate', 'Analyze'].map((stage, i) => {
            const completed = job.status === 'completed' || (job.progress > (i + 1) * 12);
            const processing = job.status === 'processing' && job.progress >= i * 12 && job.progress < (i + 1) * 12;
            const arrowActive = job.status === 'processing' && job.progress >= (i * 12) && job.progress < ((i + 2) * 12);
            return (
              <div key={stage} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div className={`pipeline-step ${completed ? 'success' : processing ? 'processing' : 'pending'}`}>
                  <span>{completed ? '✓' : processing ? '◌' : '○'}</span>
                  {stage}
                </div>
                {i < 7 && <span className={`pipeline-arrow ${arrowActive ? 'active' : ''}`}>→</span>}
              </div>
            );
          })}
        </div>
      </div>

      {/* File Info + Key Params */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>File Information</h3>
          <InfoRow label="Filename" value={job.filename} />
          <InfoRow label="File Type" value={job.file_type.toUpperCase()} />
          <InfoRow label="File Size" value={`${(job.file_size / 1e6).toFixed(2)} MB`} />
          <InfoRow label="Sample Rate" value={job.sample_rate ? `${(job.sample_rate / 1e6).toFixed(3)} MHz` : '—'} tag="FILE METADATA" />
          <InfoRow label="Duration" value={job.duration ? `${job.duration.toFixed(3)} s` : '—'} tag="MEASURED" />
          <InfoRow label="Samples" value={job.num_samples ? job.num_samples.toLocaleString() : '—'} tag="MEASURED" />
        </div>
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Signal Overview</h3>
          <InfoRow label="Modulation" value={job.detected_modulation || '—'} tag="ML CLASSIFICATION" highlight />
          <InfoRow label="Confidence" value={job.modulation_confidence ? `${(job.modulation_confidence * 100).toFixed(1)}%` : '—'} tag="ML CLASSIFICATION" />
          <InfoRow label="SNR" value={job.snr != null ? `${job.snr.toFixed(1)} dB` : '—'} tag="ESTIMATED" />
          <InfoRow label="Bandwidth" value={job.bandwidth ? `${(job.bandwidth / 1e3).toFixed(1)} kHz` : '—'} tag="ESTIMATED" />
          <InfoRow label="Symbol Rate" value={job.symbol_rate ? `${(job.symbol_rate / 1e3).toFixed(1)} ksym/s` : '—'} tag="ESTIMATED" />
          <InfoRow label="Recovered Bits" value={job.recovered_bits ? job.recovered_bits.toLocaleString() : '—'} tag={job.demodulated ? 'DECODED' : 'UNAVAILABLE'} />
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value, tag, highlight }: { label: string; value: string; tag?: string; highlight?: boolean }) {
  const tagClass = tag === 'ESTIMATED' ? 'badge-estimated' : tag === 'ML CLASSIFICATION' ? 'badge-ml' : tag === 'MEASURED' ? 'badge-measured' : tag === 'FILE METADATA' ? 'badge-metadata' : tag === 'DECODED' ? 'badge-decoded' : 'badge-unavailable';
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border-primary)' }}>
      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span className="mono" style={{ fontSize: 13, fontWeight: highlight ? 700 : 500, color: highlight ? 'var(--signal-cyan)' : 'var(--text-primary)' }}>{value}</span>
        {tag && <span className={`badge ${tagClass}`} style={{ fontSize: 8 }}>{tag}</span>}
      </div>
    </div>
  );
}

// ─── Visualization Tabs ───

function WaveformTab({ data }: { data: WaveformData | null }) {
  const [viewMode, setViewMode] = useState<'i' | 'q' | 'magnitude' | 'phase'>('magnitude');

  if (!data) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Loading waveform data...</div>;

  const colors = { i: '#00d4ff', q: '#a78bfa', magnitude: '#00f5a0', phase: '#f59e0b' };
  
  return (
    <div className="animate-fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600 }}>Time Domain — {viewMode.toUpperCase()}</h3>
        <div className="tab-group">
          {(['i', 'q', 'magnitude', 'phase'] as const).map(m => (
            <button key={m} className={`tab-item ${viewMode === m ? 'active' : ''}`} onClick={() => setViewMode(m)}>{m.toUpperCase()}</button>
          ))}
        </div>
      </div>
      
      <div className="chart-container" style={{ flex: 1, minHeight: 400, padding: 0, overflow: 'hidden', display: 'flex' }}>
        <Plot
          data={[
            {
              x: data.time,
              y: data[viewMode],
              type: 'scattergl',
              mode: 'lines',
              line: { color: colors[viewMode], width: 1.5 },
              hoverinfo: 'x+y',
            }
          ]}
          layout={{
            autosize: true,
            margin: { t: 20, r: 20, l: 50, b: 40 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#94a3b8', family: 'JetBrains Mono, monospace', size: 10 },
            xaxis: { 
              title: 'Time (s)', 
              gridcolor: 'rgba(255,255,255,0.05)', 
              zerolinecolor: 'rgba(255,255,255,0.1)',
            },
            yaxis: { 
              title: 'Amplitude', 
              gridcolor: 'rgba(255,255,255,0.05)', 
              zerolinecolor: 'rgba(255,255,255,0.1)',
            },
            hovermode: 'closest'
          }}
          config={{ responsive: true, displayModeBar: true, displaylogo: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
      
      <div style={{ marginTop: 8, display: 'flex', gap: 16, fontSize: 11, color: 'var(--text-tertiary)' }}>
        <span>Samples: {data.original_length.toLocaleString()}</span>
        <span>Displayed: {data[viewMode].length.toLocaleString()}</span>
        {data.downsampled && <span className="badge badge-estimated">DOWNSAMPLED {data.downsample_factor}x</span>}
        <span>Sample Rate: {(data.sample_rate / 1e6).toFixed(3)} MHz</span>
      </div>
    </div>
  );
}

function SpectrumTab({ data }: { data: SpectrumData | null }) {
  if (!data) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Loading spectrum data...</div>;

  return (
    <div className="animate-fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600 }}>Power Spectral Density</h3>
        <div style={{ display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-tertiary)' }}>
          <span>FFT: {data.fft_size}</span>
          <span>Window: {data.window}</span>
          {data.occupied_bandwidth && <span>BW: {(data.occupied_bandwidth / 1e3).toFixed(1)} kHz</span>}
        </div>
      </div>
      <div className="chart-container" style={{ flex: 1, minHeight: 400, padding: 0, overflow: 'hidden', display: 'flex' }}>
        <Plot
          data={[
            {
              x: data.frequencies,
              y: data.magnitudes,
              type: 'scattergl',
              mode: 'lines',
              line: { color: '#00f5a0', width: 1.5 },
              fill: 'tozeroy',
              fillcolor: 'rgba(0,245,160,0.1)',
              name: 'PSD',
              hoverinfo: 'x+y',
            },
            ...(data.noise_floor ? [{
              x: [data.frequencies[0], data.frequencies[data.frequencies.length - 1]],
              y: [data.noise_floor, data.noise_floor],
              type: 'scattergl' as any,
              mode: 'lines' as any,
              line: { color: '#ef4444', width: 1, dash: 'dash' },
              name: 'Noise Floor',
              hoverinfo: 'none' as any,
            }] : []),
            ...(data.peak_frequency ? [{
              x: [data.peak_frequency],
              y: [Math.max(...data.magnitudes)],
              type: 'scattergl' as any,
              mode: 'markers' as any,
              marker: { color: '#f59e0b', size: 8 },
              name: 'Peak',
              hoverinfo: 'x+y' as any,
            }] : []),
          ]}
          layout={{
            autosize: true,
            margin: { t: 20, r: 20, l: 50, b: 40 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#94a3b8', family: 'JetBrains Mono, monospace', size: 10 },
            xaxis: { 
              title: 'Frequency (Hz)', 
              gridcolor: 'rgba(255,255,255,0.05)', 
              zerolinecolor: 'rgba(255,255,255,0.1)',
            },
            yaxis: { 
              title: 'Magnitude (dB)', 
              gridcolor: 'rgba(255,255,255,0.05)', 
              zerolinecolor: 'rgba(255,255,255,0.1)',
            },
            showlegend: true,
            legend: { x: 1, xanchor: 'right', y: 1 },
            hovermode: 'closest'
          }}
          config={{ responsive: true, displayModeBar: true, displaylogo: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
}

function WaterfallTab({ data }: { data: SpectrogramData | null }) {
  if (!data) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Loading spectrogram...</div>;

  return (
    <div className="animate-fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600 }}>3D Spectrogram Waterfall</h3>
        <div style={{ display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-tertiary)' }}>
          <span>FFT: {data.fft_size}</span>
          <span>Hop: {data.hop_size}</span>
          <span>Window: {data.window}</span>
        </div>
      </div>
      
      <div className="chart-container" style={{ flex: 1, minHeight: 450, padding: 0, overflow: 'hidden', display: 'flex' }}>
        <Plot
          data={[
            {
              z: data.magnitudes,
              x: data.times,
              y: data.frequencies,
              type: 'surface',
              colorscale: 'Viridis',
              showscale: false,
              contours: {
                z: { show: true, usecolormap: true, highlightcolor: "limegreen", project: { z: true } }
              }
            }
          ]}
          layout={{
            autosize: true,
            margin: { t: 0, r: 0, l: 0, b: 0 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            scene: {
              xaxis: { title: 'Time (s)', gridcolor: 'rgba(255,255,255,0.1)', backgroundcolor: 'rgba(0,0,0,0)' },
              yaxis: { title: 'Freq (Hz)', gridcolor: 'rgba(255,255,255,0.1)', backgroundcolor: 'rgba(0,0,0,0)' },
              zaxis: { title: 'Power', gridcolor: 'rgba(255,255,255,0.1)', backgroundcolor: 'rgba(0,0,0,0)' },
              camera: { eye: { x: -1.5, y: -1.5, z: 1.2 } },
              bgcolor: 'transparent'
            },
            font: { color: '#94a3b8', family: 'JetBrains Mono, monospace', size: 10 },
          }}
          config={{ responsive: true, displayModeBar: true, displaylogo: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
}

function ConstellationTab({ data }: { data: ConstellationData | null }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const dpr = window.devicePixelRatio || 1;
    const size = Math.min(canvas.parentElement!.clientWidth, 500);
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    ctx.fillStyle = '#0f1420';
    ctx.fillRect(0, 0, size, size);

    const pad = 40;
    const plotSize = size - 2 * pad;

    const allI = [...data.i, ...(data.reference_i || [])];
    const allQ = [...data.q, ...(data.reference_q || [])];
    const maxAbs = Math.max(Math.max(...allI.map(Math.abs)), Math.max(...allQ.map(Math.abs)), 0.01) * 1.2;

    // Grid
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    // Cross axes
    ctx.beginPath();
    ctx.moveTo(pad + plotSize / 2, pad);
    ctx.lineTo(pad + plotSize / 2, pad + plotSize);
    ctx.moveTo(pad, pad + plotSize / 2);
    ctx.lineTo(pad + plotSize, pad + plotSize / 2);
    ctx.stroke();
    // Unit circle
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.beginPath();
    const r = (1 / maxAbs) * plotSize / 2;
    ctx.arc(pad + plotSize / 2, pad + plotSize / 2, r, 0, 2 * Math.PI);
    ctx.stroke();

    // Reference constellation
    if (data.reference_i && data.reference_q) {
      ctx.fillStyle = 'rgba(245, 158, 11, 0.8)';
      for (let i = 0; i < data.reference_i.length; i++) {
        const x = pad + (data.reference_i[i] / maxAbs + 1) / 2 * plotSize;
        const y = pad + (1 - (data.reference_q[i] / maxAbs + 1) / 2) * plotSize;
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, 2 * Math.PI);
        ctx.fill();
        // Cross marker
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - 4, y - 4); ctx.lineTo(x + 4, y + 4);
        ctx.moveTo(x + 4, y - 4); ctx.lineTo(x - 4, y + 4);
        ctx.stroke();
      }
    }

    // Labels
    ctx.fillStyle = '#475569';
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.fillText('I →', pad + plotSize - 20, pad + plotSize / 2 + 15);
    ctx.fillText('Q ↑', pad + plotSize / 2 + 8, pad + 12);

    // Animated Data Points
    const totalPoints = data.i.length;
    let currentIdx = 0;
    const pointsPerFrame = Math.max(1, Math.floor(totalPoints / 60)); // Animate over ~1 second

    const animate = () => {
      // Glow effect (fading trail)
      // ctx.fillStyle = 'rgba(15, 20, 32, 0.05)'; // Background color with low opacity
      // ctx.fillRect(pad, pad, plotSize, plotSize); // Optional: creates a fading trail but smears grid

      ctx.fillStyle = 'rgba(0, 245, 160, 0.35)'; // Cyan/Green points
      
      const endIdx = Math.min(currentIdx + pointsPerFrame, totalPoints);
      for (let i = currentIdx; i < endIdx; i++) {
        const x = pad + (data.i[i] / maxAbs + 1) / 2 * plotSize;
        const y = pad + (1 - (data.q[i] / maxAbs + 1) / 2) * plotSize;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, 2 * Math.PI);
        ctx.fill();
      }

      currentIdx = endIdx;

      if (currentIdx < totalPoints) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [data]);

  if (!data) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Loading constellation...</div>;

  return (
    <div className="animate-fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600 }}>Constellation Diagram {data.modulation && `— ${data.modulation}`}</h3>
        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{data.num_points} points</span>
      </div>
      <div className="chart-container" style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 20 }}>
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}

function ParametersTab({ params }: { params: SignalParameter[] }) {
  if (params.length === 0) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>No parameters extracted yet.</div>;

  const tagClass = (s?: string) => s === 'ESTIMATED' ? 'badge-estimated' : s === 'ML CLASSIFICATION' ? 'badge-ml' : s === 'MEASURED' ? 'badge-measured' : s === 'FILE METADATA' ? 'badge-metadata' : s === 'DECODED' ? 'badge-decoded' : 'badge-unavailable';

  return (
    <div className="animate-fade-in">
      <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Extracted Signal Parameters</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ borderBottom: '2px solid var(--border-primary)' }}>
            {['Parameter', 'Value', 'Unit', 'Confidence', 'Source', 'Notes'].map(h => (
              <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 500, fontSize: 11, textTransform: 'uppercase' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {params.map((p, i) => (
            <tr key={i} style={{ borderBottom: '1px solid var(--border-primary)' }}>
              <td style={{ padding: '8px 12px', fontWeight: 500 }}>{p.parameter_name}</td>
              <td style={{ padding: '8px 12px' }} className="mono">{p.value != null ? (typeof p.value === 'number' ? p.value.toFixed(4) : p.value) : p.value_str || '—'}</td>
              <td style={{ padding: '8px 12px', color: 'var(--text-tertiary)' }}>{p.unit || ''}</td>
              <td style={{ padding: '8px 12px' }}>
                {p.confidence != null && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 40, height: 4, borderRadius: 2, background: 'var(--bg-tertiary)' }}>
                      <div style={{ width: `${p.confidence * 100}%`, height: '100%', borderRadius: 2, background: p.confidence > 0.7 ? 'var(--status-success)' : p.confidence > 0.4 ? 'var(--status-warning)' : 'var(--status-error)' }} />
                    </div>
                    <span className="mono" style={{ fontSize: 11 }}>{(p.confidence * 100).toFixed(0)}%</span>
                  </div>
                )}
              </td>
              <td style={{ padding: '8px 12px' }}><span className={`badge ${tagClass(p.source)}`}>{p.source}</span></td>
              <td style={{ padding: '8px 12px', color: 'var(--text-tertiary)', fontSize: 12 }}>{p.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ModulationTab({ job }: { job: AnalysisJob | null }) {
  if (!job) return null;
  const probs = job.modulation_probabilities || {};
  const sorted = Object.entries(probs).sort((a, b) => b[1] - a[1]);

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 16, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Classification Result</h3>
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--signal-cyan)', marginBottom: 8 }}>{job.detected_modulation || '—'}</div>
            <div className="mono" style={{ fontSize: 24, color: 'var(--text-primary)' }}>{job.modulation_confidence ? `${(job.modulation_confidence * 100).toFixed(1)}%` : '—'}</div>
            <span className="badge badge-ml" style={{ marginTop: 8 }}>ML CLASSIFICATION</span>
          </div>
        </div>
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 16, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Probability Distribution</h3>
          {sorted.map(([mod, prob]) => (
            <div key={mod} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span className="mono" style={{ width: 60, fontSize: 12, fontWeight: 500 }}>{mod}</span>
              <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'var(--bg-tertiary)', overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 4,
                  background: mod === job.detected_modulation ? 'var(--signal-cyan)' : 'var(--border-accent)',
                  width: `${prob * 100}%`, transition: 'width 0.5s ease',
                }} />
              </div>
              <span className="mono" style={{ width: 50, fontSize: 11, textAlign: 'right', color: 'var(--text-secondary)' }}>{(prob * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Model Information</h3>
        <InfoRow label="Method" value="Higher-Order Cumulant (HoC)" />
        <InfoRow label="Version" value="1.0" />
        <InfoRow label="Training Classes" value="BPSK, QPSK, 8PSK, FSK, 16QAM, 64QAM, AM, FM, ASK" />
        <InfoRow label="Confidence Threshold" value="50%" />
      </div>
    </div>
  );
}

function DemodulationTab({ job, jobId }: { job: AnalysisJob | null; jobId: number }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const runDemod = async () => {
    setLoading(true);
    try {
      const r = await api.demodulate(jobId, {});
      setResult(r);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div className="animate-fade-in">
      <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Demodulation</h3>
      {!result && !job?.demodulated ? (
        <div className="card" style={{ textAlign: 'center', padding: 40 }}>
          <p style={{ marginBottom: 16, color: 'var(--text-secondary)' }}>Run the demodulator to recover symbols and bits.</p>
          <button className="btn-primary" onClick={runDemod} disabled={loading}>{loading ? '◌ Demodulating...' : '⇌ Run Demodulation'}</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="card">
            <InfoRow label="Status" value={result?.success ? 'SUCCESS' : 'FAILED'} tag={result?.success ? 'DECODED' : 'UNAVAILABLE'} highlight />
            <InfoRow label="Modulation" value={String(result?.modulation || job?.detected_modulation || '—')} />
            <InfoRow label="Symbols" value={String(result?.num_symbols || '—')} />
            <InfoRow label="Recovered Bits" value={String(result?.bits ? (result.bits as number[]).length.toLocaleString() : job?.recovered_bits?.toLocaleString() || '—')} tag="DECODED" />
            <InfoRow label="EVM" value={result?.evm_db != null ? `${(result.evm_db as number).toFixed(1)} dB` : '—'} tag="MEASURED" />
            <InfoRow label="Quality" value={result?.quality != null ? `${((result.quality as number) * 100).toFixed(1)}%` : '—'} tag="ESTIMATED" />
          </div>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <div style={{ fontSize: 48, fontWeight: 800, color: result?.success ? 'var(--status-success)' : 'var(--status-error)' }}>
              {result?.success ? '✓' : '✕'}
            </div>
            <div style={{ fontSize: 16, fontWeight: 600, marginTop: 8 }}>{result?.success ? 'Demodulation Successful' : 'Demodulation Failed'}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function BitstreamTab({ data }: { data: BitstreamData | null }) {
  if (!data || data.total_bits === 0) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>No bitstream available. Run demodulation first.</div>;

  const hexLines: string[] = [];
  const hexBytes = data.hex_dump.split(' ');
  for (let i = 0; i < hexBytes.length; i += 16) {
    const offset = (data.offset / 8 + i).toString(16).padStart(8, '0').toUpperCase();
    const hex = hexBytes.slice(i, i + 16).join(' ');
    const ascii = data.ascii_dump.slice(i, i + 16);
    hexLines.push(`${offset}  ${hex.padEnd(47)}  ${ascii}`);
  }

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600 }}>Bitstream Viewer</h3>
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          {data.total_bits.toLocaleString()} bits • {data.total_bytes.toLocaleString()} bytes
          {!data.is_printable && <span className="badge badge-unavailable" style={{ marginLeft: 8 }}>NON-PRINTABLE</span>}
        </div>
      </div>
      <pre className="mono" style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-primary)',
        borderRadius: 8,
        padding: 16,
        fontSize: 12,
        lineHeight: 1.8,
        overflow: 'auto',
        maxHeight: 400,
        color: 'var(--text-primary)',
      }}>
        {hexLines.join('\n')}
      </pre>
    </div>
  );
}

function ReportTab({ job, jobId }: { job: AnalysisJob | null; jobId: number }) {
  const [exporting, setExporting] = useState(false);

  const exportReport = async (format: string) => {
    setExporting(true);
    try {
      if (format === 'json') {
        const data = await api.exportReport(jobId, 'json');
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${jobId}.json`;
        a.click();
      } else {
        const data = await api.exportReport(jobId, format);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${jobId}.${format}`;
        a.click();
      }
    } catch (e) { console.error(e); }
    setExporting(false);
  };

  return (
    <div className="animate-fade-in">
      <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Signal Intelligence Report</h3>
      <div className="card" style={{ marginBottom: 16, textAlign: 'center', padding: 30 }}>
        <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Export Report</div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>Download the full analysis report with all parameters, classifications, and results.</p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <button className="btn-primary" onClick={() => exportReport('pdf')} disabled={exporting}>▤ Export PDF</button>
          <button className="btn-secondary" onClick={() => exportReport('json')} disabled={exporting}>{ } Export JSON</button>
          <button className="btn-secondary" onClick={() => exportReport('csv')} disabled={exporting}>▦ Export CSV</button>
        </div>
      </div>
      {job && (
        <div className="card">
          <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, textTransform: 'uppercase', color: 'var(--text-tertiary)' }}>Report Preview</h4>
          <InfoRow label="File" value={job.filename} />
          <InfoRow label="Type" value={job.file_type.toUpperCase()} />
          <InfoRow label="Modulation" value={job.detected_modulation || '—'} tag="ML CLASSIFICATION" />
          <InfoRow label="SNR" value={job.snr != null ? `${job.snr.toFixed(1)} dB` : '—'} tag="ESTIMATED" />
          <InfoRow label="Bandwidth" value={job.bandwidth ? `${(job.bandwidth / 1e3).toFixed(1)} kHz` : '—'} tag="ESTIMATED" />
          <InfoRow label="Bits Recovered" value={job.recovered_bits?.toLocaleString() || '—'} tag={job.demodulated ? 'DECODED' : 'UNAVAILABLE'} />
        </div>
      )}
    </div>
  );
}
