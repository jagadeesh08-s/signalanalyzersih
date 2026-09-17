from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileType(str, enum.Enum):
    IQ = "iq"
    WAV = "wav"
    BIN = "bin"
    RAW = "raw"
    UNKNOWN = "unknown"


class ModulationType(str, enum.Enum):
    BPSK = "BPSK"
    QPSK = "QPSK"
    PSK8 = "8PSK"
    FSK = "FSK"
    QAM16 = "16QAM"
    QAM64 = "64QAM"
    AM = "AM"
    FM = "FM"
    ASK = "ASK"
    UNKNOWN = "UNKNOWN"


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    
    sample_rate = Column(Float, nullable=True)
    center_frequency = Column(Float, nullable=True)
    duration = Column(Float, nullable=True)
    num_samples = Column(Integer, nullable=True)
    num_channels = Column(Integer, nullable=True)
    data_type = Column(String(50), nullable=True)
    
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    progress = Column(Float, default=0.0)
    current_stage = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    detected_modulation = Column(SQLEnum(ModulationType), nullable=True)
    modulation_confidence = Column(Float, nullable=True)
    modulation_probabilities = Column(JSON, nullable=True)
    
    snr = Column(Float, nullable=True)
    bandwidth = Column(Float, nullable=True)
    symbol_rate = Column(Float, nullable=True)
    frequency_offset = Column(Float, nullable=True)
    
    demodulated = Column(Boolean, default=False)
    recovered_bits = Column(Integer, nullable=True)
    ber = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    report_path = Column(String(512), nullable=True)
    
    def __repr__(self):
        return f"<AnalysisJob(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class SignalParameter(Base):
    __tablename__ = "signal_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    
    parameter_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=True)
    value_str = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    source = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    job = relationship("AnalysisJob", backref="parameters")


class SpectrumData(Base):
    __tablename__ = "spectrum_data"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    
    frequencies = Column(JSON, nullable=False)
    magnitudes = Column(JSON, nullable=False)
    fft_size = Column(Integer, nullable=False)
    window = Column(String(50), nullable=False)
    sample_rate = Column(Float, nullable=False)
    
    job = relationship("AnalysisJob", backref="spectrum_data")


class ConstellationData(Base):
    __tablename__ = "constellation_data"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    
    i_samples = Column(JSON, nullable=False)
    q_samples = Column(JSON, nullable=False)
    normalized = Column(Boolean, default=False)
    equalized = Column(Boolean, default=False)
    
    job = relationship("AnalysisJob", backref="constellation_data")


class DemodulationResult(Base):
    __tablename__ = "demodulation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    
    modulation = Column(SQLEnum(ModulationType), nullable=False)
    symbol_rate = Column(Float, nullable=True)
    samples_per_symbol = Column(Integer, nullable=True)
    
    symbols = Column(JSON, nullable=True)
    bits = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    quality_metrics = Column(JSON, nullable=True)
    
    job = relationship("AnalysisJob", backref="demodulation_results")


class CorrelationResult(Base):
    __tablename__ = "correlation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=True)
    reference_job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=True)
    
    correlation_coefficient = Column(Float, nullable=False)
    time_offset = Column(Float, nullable=True)
    similarity_score = Column(Float, nullable=False)
    method = Column(String(100), nullable=False)
    
    job = relationship("AnalysisJob", foreign_keys=[job_id], backref="correlations")
    reference_job = relationship("AnalysisJob", foreign_keys=[reference_job_id])


class SampleSignal(Base):
    __tablename__ = "sample_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    modulation = Column(SQLEnum(ModulationType), nullable=False)
    description = Column(Text, nullable=True)
    
    sample_rate = Column(Float, nullable=False)
    symbol_rate = Column(Float, nullable=False)
    snr = Column(Float, nullable=False)
    carrier_offset = Column(Float, default=0.0)
    frequency_offset = Column(Float, default=0.0)
    num_samples = Column(Integer, nullable=False)
    samples_per_symbol = Column(Integer, nullable=False)
    
    file_path = Column(String(512), nullable=True)
    is_synthetic = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)