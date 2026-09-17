const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API Error ${res.status}: ${error}`);
  }
  return res.json();
}

export async function apiUpload(file: File, config: Record<string, string | number | boolean>) {
  const formData = new FormData();
  formData.append('file', file);
  Object.entries(config).forEach(([key, value]) => {
    formData.append(key, String(value));
  });

  const res = await fetch(`${API_BASE}/files/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Upload Error ${res.status}: ${error}`);
  }
  return res.json();
}

export function getWsUrl(jobId: number): string {
  const wsBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1')
    .replace('http://', 'ws://')
    .replace('https://', 'wss://');
  return `${wsBase}/ws/${jobId}`;
}

// ── Typed API calls ──

export const api = {
  getStats: () => apiFetch('/stats'),
  listAnalyses: (skip = 0, limit = 50) => apiFetch(`/analysis?skip=${skip}&limit=${limit}`),
  getAnalysis: (id: number) => apiFetch(`/analysis/${id}`),
  getParameters: (id: number) => apiFetch(`/analysis/${id}/parameters`),
  getWaveform: (id: number, maxPoints = 10000) => apiFetch(`/analysis/${id}/waveform?max_points=${maxPoints}`),
  getSpectrum: (id: number, fftSize = 4096, window = 'hann') => apiFetch(`/analysis/${id}/spectrum?fft_size=${fftSize}&window=${window}`),
  getSpectrogram: (id: number, fftSize = 1024, window = 'hann') => apiFetch(`/analysis/${id}/spectrogram?fft_size=${fftSize}&window=${window}`),
  getConstellation: (id: number, normalized = false) => apiFetch(`/analysis/${id}/constellation?normalized=${normalized}`),
  demodulate: (id: number, config: Record<string, unknown>) => apiFetch(`/analysis/${id}/demodulate`, { method: 'POST', body: JSON.stringify(config) }),
  getBitstream: (id: number, offset = 0, length = 1024) => apiFetch(`/analysis/${id}/bitstream?offset=${offset}&length=${length}`),
  correlate: (jobIdA: number, jobIdB: number) => apiFetch('/correlation', { method: 'POST', body: JSON.stringify({ job_id_a: jobIdA, job_id_b: jobIdB }) }),
  exportReport: (id: number, format = 'json') => apiFetch(`/reports/${id}/export?format=${format}`),
  askAssistant: (query: string, jobId?: number) => apiFetch('/assistant/query', { method: 'POST', body: JSON.stringify({ query, job_id: jobId }) }),
  getMLEval: () => apiFetch('/ml/eval'),
};
