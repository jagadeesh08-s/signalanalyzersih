"""
Pydantic schemas for API request/response payloads.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FileTypeEnum(str, Enum):
    IQ = "iq"
    WAV = "wav"
    BIN = "bin"
    RAW = "raw"
    UNKNOWN = "unknown"


class AnalysisStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceTag(str, Enum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    ML_CLASSIFICATION = "ML CLASSIFICATION"
    FILE_METADATA = "FILE METADATA"
    DECODED = "DECODED"
    UNAVAILABLE = "UNAVAILABLE"
    DEMO = "DEMO / SYNTHETIC SIGNAL"


# ----- IQ File Configuration -----

class IQConfig(BaseModel):
    dtype: str = Field("int16", description="Data type: int8, int16, int32, float32")
    iq_order: str = Field("IQ", description="Interleaving order: IQ or QI")
    endianness: str = Field("little", description="Byte order: little or big")
    sample_rate: float = Field(1_000_000, description="Sample rate in Hz")
    center_frequency: float = Field(0.0, description="Center frequency in Hz")
    scale_factor: float = Field(1.0, description="Scale factor for integer types")


class PreprocessingConfig(BaseModel):
    dc_removal: bool = True
    normalize: bool = True
    bandpass_low: Optional[float] = None
    bandpass_high: Optional[float] = None
    lowpass_cutoff: Optional[float] = None
    resample_rate: Optional[float] = None
    noise_reduction: bool = False


# ----- Analysis Job -----

class AnalysisJobCreate(BaseModel):
    filename: str
    file_type: FileTypeEnum
    iq_config: Optional[IQConfig] = None
    preprocessing: Optional[PreprocessingConfig] = None


class ParameterResponse(BaseModel):
    parameter_name: str
    value: Optional[float] = None
    value_str: Optional[str] = None
    unit: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class AnalysisJobResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    progress: float
    current_stage: Optional[str] = None
    error_message: Optional[str] = None

    sample_rate: Optional[float] = None
    center_frequency: Optional[float] = None
    duration: Optional[float] = None
    num_samples: Optional[int] = None
    num_channels: Optional[int] = None
    data_type: Optional[str] = None

    detected_modulation: Optional[str] = None
    modulation_confidence: Optional[float] = None
    modulation_probabilities: Optional[Dict[str, float]] = None

    snr: Optional[float] = None
    bandwidth: Optional[float] = None
    symbol_rate: Optional[float] = None
    frequency_offset: Optional[float] = None

    demodulated: bool = False
    recovered_bits: Optional[int] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    is_demo: bool = False

    class Config:
        from_attributes = True


class AnalysisJobList(BaseModel):
    jobs: List[AnalysisJobResponse]
    total: int


# ----- Waveform -----

class WaveformResponse(BaseModel):
    i: List[float]
    q: List[float]
    magnitude: List[float]
    phase: List[float]
    time: List[float]
    sample_rate: float
    downsampled: bool
    downsample_factor: int = 1
    original_length: int


# ----- Spectrum -----

class SpectrumResponse(BaseModel):
    frequencies: List[float]
    magnitudes: List[float]
    fft_size: int
    window: str
    sample_rate: float
    peak_frequency: Optional[float] = None
    noise_floor: Optional[float] = None
    occupied_bandwidth: Optional[float] = None


# ----- Spectrogram -----

class SpectrogramResponse(BaseModel):
    times: List[float]
    frequencies: List[float]
    magnitudes: List[List[float]]
    fft_size: int
    hop_size: int
    window: str
    sample_rate: float


# ----- Constellation -----

class ConstellationResponse(BaseModel):
    i: List[float]
    q: List[float]
    reference_i: Optional[List[float]] = None
    reference_q: Optional[List[float]] = None
    modulation: Optional[str] = None
    normalized: bool = False
    num_points: int


# ----- Demodulation -----

class DemodulationRequest(BaseModel):
    modulation: Optional[str] = None
    symbol_rate: Optional[float] = None
    carrier_offset: float = 0.0


class DemodulationResponse(BaseModel):
    success: bool
    modulation: str
    num_symbols: Optional[int] = None
    num_bits: Optional[int] = None
    evm_db: Optional[float] = None
    quality: Optional[float] = None
    error: Optional[str] = None


# ----- Bitstream -----

class BitstreamResponse(BaseModel):
    bits: List[int]
    hex_dump: str
    ascii_dump: str
    total_bits: int
    total_bytes: int
    offset: int
    length: int
    is_printable: bool


# ----- Correlation -----

class CorrelationRequest(BaseModel):
    job_id_a: int
    job_id_b: int
    max_lag: Optional[int] = None


class CorrelationResponse(BaseModel):
    similarity_score: float
    peak_correlation: float
    peak_lag: int
    time_offset_seconds: float
    mse: float
    spectral_similarity: float
    correlation_data: Optional[List[float]] = None
    lags: Optional[List[int]] = None


# ----- Sample Signals -----

class SampleSignalResponse(BaseModel):
    id: int
    name: str
    modulation: str
    description: Optional[str] = None
    sample_rate: float
    symbol_rate: float
    snr: float
    num_samples: int
    samples_per_symbol: int
    is_synthetic: bool

    class Config:
        from_attributes = True


class SampleGenerateRequest(BaseModel):
    sample_id: Optional[int] = None
    modulation: Optional[str] = "QPSK"
    sample_rate: float = 1_000_000
    symbol_rate: float = 100_000
    snr: float = 20.0
    num_samples: int = 100_000
    carrier_offset: float = 0.0
    frequency_offset: float = 0.0


# ----- Report -----

class ReportRequest(BaseModel):
    format: str = Field("pdf", description="Export format: pdf, json, csv")


# ----- AI Assistant -----

class AIAssistantQuery(BaseModel):
    query: str
    job_id: Optional[int] = None


class AIAssistantResponse(BaseModel):
    response: str
    context_used: bool = False


# ----- ML Evaluation -----

class MLEvalResponse(BaseModel):
    accuracy: float
    precision: Dict[str, float]
    recall: Dict[str, float]
    f1_score: Dict[str, float]
    confusion_matrix: List[List[int]]
    classes: List[str]
    num_samples: int


# ----- Settings -----

class AppSettings(BaseModel):
    default_fft_size: int = 4096
    default_window: str = "hann"
    max_visualization_points: int = 10000
    max_file_size_mb: int = 500
    auto_analysis: bool = True
    auto_demodulate: bool = False
    confidence_threshold: float = 0.5
    theme: str = "dark"
    density: str = "comfortable"


# ----- WebSocket -----

class WSProgressMessage(BaseModel):
    job_id: int
    stage: str
    progress: float
    message: str
    status: str = "processing"
