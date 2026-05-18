"""
Configuration Module
Loads environment variables and app settings
"""

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    APP_NAME: str = "YouTube Study Assistant"
    DEBUG: bool = True
    GEMINI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
