"""
Application configuration using Pydantic BaseSettings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings for automatic environment variable loading.
    Supports .env file for local development.
    """
    
    # API Configuration
    api_title: str = "Agentic Market Intelligence Hub API"
    api_version: str = "1.0.0"
    api_description: str = "Competitive intelligence monitoring and reporting API"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.2
    openai_max_tokens: int = 3000
    
    # Crawler Configuration
    crawler_timeout: int = 60  # seconds
    crawler_use_playwright: bool = False
    crawler_wait_for: Optional[str] = None
    
    # Agent Configuration
    watcher_agent_id: str = "watcher"
    analyst_agent_id: str = "analyst"
    reporter_agent_id: str = "reporter"
    
    # Analyst Agent Thresholds
    critical_threshold: float = 0.8
    price_change_threshold: float = 0.2
    
    # Reporter Agent Configuration
    reporter_max_change_records: int = 15
    reporter_generate_html: bool = True
    
    # Email Configuration
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_smtp_username: Optional[str] = None
    email_smtp_password: Optional[str] = None
    email_from_address: Optional[str] = None
    email_from_name: str = "Market Intelligence Hub"
    email_use_tls: bool = True
    email_template_dir: str = "templates/email"
    
    # Scheduler Configuration
    scheduler_enabled: bool = True
    scheduler_timezone: str = "UTC"
    default_user_id: Optional[str] = None
    
    # Database Configuration
    # Firestore uses Application Default Credentials (ADC)
    # No explicit configuration needed
    
    # CORS Configuration
    cors_origins: list[str] = ["*"]  # MVP: Allow all origins
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Logging Configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure single instance across the application.
    
    Returns:
        Settings instance
    """
    return Settings()
