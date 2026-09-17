export interface AnalysisJob {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_stage?: string;
  error_message?: string;
  sample_rate?: number;
  center_frequency?: number;
  duration?: number;
  num_samples?: number;
  num_channels?: number;
  data_type?: string;
  detected_modulation?: string;
  modulation_confidence?: number;
  modulation_probabilities?: Record<string, number>;
  snr?: number;
  bandwidth?: number;
  symbol_rate?: number;
  frequency_offset?: number;
  demodulated: boolean;
  recovered_bits?: number;
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
  is_demo?: boolean;
}

export interface SignalParameter {
  parameter_name: string;
  value?: number;
  value_str?: string;
  unit?: string;
  confidence?: number;
  source?: string;
  notes?: string;
}

export interface WaveformData {
  i: number[];
  q: number[];
  magnitude: number[];
  phase: number[];
  time: number[];
  sample_rate: number;
  downsampled: boolean;
  downsample_factor: number;
  original_length: number;
}

export interface SpectrumData {
  frequencies: number[];
  magnitudes: number[];
  fft_size: number;
  window: string;
  sample_rate: number;
  peak_frequency?: number;
  noise_floor?: number;
  occupied_bandwidth?: number;
}

export interface SpectrogramData {
  times: number[];
  frequencies: number[];
  magnitudes: number[][];
  fft_size: number;
  hop_size: number;
  window: string;
  sample_rate: number;
}

export interface ConstellationData {
  i: number[];
  q: number[];
  reference_i?: number[];
  reference_q?: number[];
  modulation?: string;
  normalized: boolean;
  num_points: number;
}

export interface BitstreamData {
  bits: number[];
  hex_dump: string;
  ascii_dump: string;
  total_bits: number;
  total_bytes: number;
  offset: number;
  length: number;
  is_printable: boolean;
}

export interface SampleSignal {
  id: number;
  name: string;
  modulation: string;
  description?: string;
  sample_rate: number;
  symbol_rate: number;
  snr: number;
  num_samples: number;
  samples_per_symbol: number;
  is_synthetic: boolean;
}

export interface DashboardStats {
  total_analyses: number;
  signals_processed: number;
  average_snr?: number;
  most_detected_modulation?: string;
}

export interface WSProgressMessage {
  job_id: number;
  stage: string;
  progress: number;
  message: string;
  status: string;
}

export interface CorrelationResult {
  similarity_score: number;
  peak_correlation: number;
  peak_lag: number;
  time_offset_seconds: number;
  mse: number;
  spectral_similarity: number;
  correlation_data?: number[];
  lags?: number[];
}

export interface MLEvalResult {
  accuracy: number;
  precision: Record<string, number>;
  recall: Record<string, number>;
  f1_score: Record<string, number>;
  confusion_matrix: number[][];
  classes: string[];
  num_samples: number;
}
