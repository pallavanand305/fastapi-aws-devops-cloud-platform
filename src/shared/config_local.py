"""
Local development configuration (without external dependencies).
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalDatabaseSettings(BaseSettings):
    """Local database configuration using SQLite."""
    
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    # Use SQLite for local development
    url: str = Field(default="sqlite+aiosqlite:///./ml_platform.db", description="Database URL")


class LocalRedisSettings(BaseSettings):
    """Local Redis configuration (mock)."""
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    
    # Mock Redis for local development
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    
    @property
    def url(self) -> str:
        """Get the Redis URL."""
        return f"redis://{self.host}:{self.port}/0"


class LocalSettings(BaseSettings):
    """Local development settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="ML Workflow Platform (Local)", description="Application name")
    app_url: str = Field(default="http://localhost:8000", description="Application URL")
    debug: bool = Field(default=True, description="Debug mode")
    version: str = Field(default="0.1.0", description="Application version")
    
    # Service settings
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8000, description="Service port")
    
    # JWT settings
    jwt_secret_key: str = Field(
        default="local-dev-secret-key-not-for-production",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )
    
    # Component settings
    database: LocalDatabaseSettings = Field(default_factory=LocalDatabaseSettings)
    redis: LocalRedisSettings = Field(default_factory=LocalRedisSettings)


# Local settings instance
local_settings = LocalSettings()