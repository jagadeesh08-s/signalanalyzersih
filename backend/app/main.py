"""
SIH26147 Signal Analyzer — FastAPI Application Entry Point
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("Initializing database...")
    await init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.SAMPLE_SIGNALS_DIR, exist_ok=True)
    os.makedirs("./reports", exist_ok=True)
    logger.info("SIH26147 Signal Analyzer started.")
    yield
    logger.info("SIH26147 Signal Analyzer shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated Analysis of .IQ and .WAV Files + Signal Parameter Extraction",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount reports directory for static access
if os.path.exists("./reports"):
    app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# Import and include API router
from app.api.endpoints import router as api_router  # noqa: E402
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
