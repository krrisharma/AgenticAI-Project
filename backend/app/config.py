import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # API & Keys
    OPENAQ_API_KEY: str = ""
    WAQI_TOKEN: str = ""
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = ""
    GROQ_MODEL_PREFERENCE: str = "qwen,openai/gpt-oss-120b,openai/gpt-oss-20b"
    
    # Traffic
    TRAFFIC_PROVIDER: str = "synthetic"
    TOMTOM_API_KEY: str = ""
    
    # User Agent
    NOMINATIM_USER_AGENT: str = "clearpath-demo (contact: clearpath@example.com)"
    
    # Storage & Paths
    DATA_DIR: str = str(BACKEND_DIR / "data")
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    VITE_API_BASE_URL: str = "http://localhost:8000"
    
    # File Paths
    CONFIG_DIR: Path = BACKEND_DIR / "config"
    SNAPSHOTS_DIR: Path = BACKEND_DIR / "data" / "snapshots"
    PROCESSED_DIR: Path = BACKEND_DIR / "data" / "processed"
    KNOWLEDGE_DIR: Path = ROOT_DIR / "agents" / "knowledge"
    SQLITE_PATH: Path = BACKEND_DIR / "data" / "clearpath.db"
    


    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
