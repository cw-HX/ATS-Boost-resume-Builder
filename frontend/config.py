"""
Streamlit Frontend Configuration
"""
import os
from dataclasses import dataclass

# Try to get from Streamlit secrets first, then environment variable
def get_api_url():
    try:
        import streamlit as st
        return st.secrets.get("API_BASE_URL", os.getenv("API_BASE_URL", "http://localhost:8000/api/v1"))
    except:
        return os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


@dataclass
class Config:
    """Frontend configuration."""
    API_BASE_URL: str = None
    APP_TITLE: str = "ATS CV Generator"
    APP_ICON: str = "📄"
    
    # Session config
    TOKEN_KEY: str = "auth_token"
    REFRESH_TOKEN_KEY: str = "refresh_token"
    USER_KEY: str = "user"
    
    # Page config
    PAGE_TITLE: str = "ATS CV Generator"
    LAYOUT: str = "wide"
    
    def __post_init__(self):
        if self.API_BASE_URL is None:
            self.API_BASE_URL = get_api_url()


config = Config()
