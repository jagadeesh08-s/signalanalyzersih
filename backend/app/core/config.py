from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "SIH26147 Signal Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    API_V1_PREFIX: str = "/api/v1"
    
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./signal_analyzer.db"
    
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 500 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [".iq", ".IQ", ".wav", ".WAV", ".bin", ".raw"]
    
    SAMPLE_SIGNALS_DIR: str = "./data/samples"
    
    DEFAULT_FFT_SIZE: int = 4096
    DEFAULT_WINDOW: str = "hann"
    MAX_VISUALIZATION_POINTS: int = 10000
    
    MODEL_PATH: str = "./models"
    CONFIDENCE_THRESHOLD: float = 0.5
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()