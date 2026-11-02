"""
Configuration module for AI IncidentOps.
Loads environment variables and sets sane project defaults.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI IncidentOps"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    DB_PATH: Path = BASE_DIR / "database" / "incidentops.db"
    LOGS_DIR: Path = BASE_DIR / "logs"
    SERVICE_REGISTRY_PATH: Path = BASE_DIR / "infrastructure" / "service_registry.json"
    RUNBOOKS_DIR: Path = BASE_DIR / "infrastructure" / "runbooks"
    
    # Persistence & Caching
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'database' / 'incidentops.db'}")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security & Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-incidentops-jwt-token-key-32b")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # LLM & Semantic Kernel
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_ORG_ID: str = os.getenv("OPENAI_ORG_ID", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    MOCK_LLM: bool = os.getenv("MOCK_LLM", "true").lower() in ("true", "1", "yes")
    
    # Server configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Ensure directories exist
settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
settings.RUNBOOKS_DIR.mkdir(parents=True, exist_ok=True)
