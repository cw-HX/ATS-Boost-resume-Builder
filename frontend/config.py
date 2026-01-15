"""
Streamlit Frontend Configuration
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Frontend configuration."""
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    APP_TITLE: str = "ATS CV Generator"
    APP_ICON: str = "📄"
    
    # Session config
    TOKEN_KEY: str = "auth_token"
    REFRESH_TOKEN_KEY: str = "refresh_token"
    USER_KEY: str = "user"
    
    # Page config
    PAGE_TITLE: str = "ATS CV Generator"
    LAYOUT: str = "wide"


config = Config()
