"""Configuration settings for the application."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Telegram Client (for pyrogram - optional, for full member sync)
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    
    # Admin Panel
    ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", "")
    ADMIN_PANEL_HOST: str = os.getenv("ADMIN_PANEL_HOST", "0.0.0.0")
    ADMIN_PANEL_PORT: int = int(os.getenv("ADMIN_PANEL_PORT", "8000"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./usercontrol.db")
    
    # Default Admin
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    DEFAULT_ADMIN_TELEGRAM_ID: int = int(os.getenv("DEFAULT_ADMIN_TELEGRAM_ID", "0"))
    
    # Security
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    TEMPLATES_DIR: Path = BASE_DIR / "admin_panel" / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

