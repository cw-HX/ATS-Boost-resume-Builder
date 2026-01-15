"""
Application configuration management using Pydantic Settings.
All secrets are loaded from environment variables.
"""
import os
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "ATS CV Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Security
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # MongoDB
    MONGODB_URL: str = Field(..., description="MongoDB connection string")
    MONGODB_DATABASE: str = "ats_cv_generator"
    
    # Groq API
    GROQ_API_KEY: str = Field(..., description="Groq API key")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.0  # Deterministic outputs
    GROQ_MAX_TOKENS: int = 4096
    
    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LaTeX - Platform-aware defaults
    LATEX_COMPILER: str = "pdflatex"  # Use pdflatex on Linux/Railway
    LATEX_TIMEOUT: int = 60  # seconds
    LATEX_TEMP_DIR: str = "/tmp/latex"  # Linux default for Railway
    
    # Pandoc
    PANDOC_TIMEOUT: int = 30  # seconds
    
    # CORS - Allow Streamlit Cloud domains
    CORS_ORIGINS: str = "http://localhost:8501,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # ATS
    ATS_MIN_SCORE: int = 90
    ATS_MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
