"""
CockroachDB configuration for production deployment.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CockroachDBSettings(BaseSettings):
    """CockroachDB configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=26257, description="Database port")
    name: str = Field(default="fastapi_platform", description="Database name")
    user: str = Field(default="root", description="Database user")
    password: str = Field(default="", description="Database password")
    sslmode: str = Field(default="disable", description="SSL mode")
    
    @property
    def url(self) -> str:
        """Get the database URL for CockroachDB."""
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?sslmode={self.sslmode}"
        else:
            return f"postgresql://{self.user}@{self.host}:{self.port}/{self.name}?sslmode={self.sslmode}"


class CockroachSettings(BaseSettings):
    """CockroachDB application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="ML Workflow Platform (CockroachDB)", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    version: str = Field(default="0.1.0", description="Application version")
    
    # Service settings
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8000, description="Service port")
    
    # JWT settings
    jwt_secret_key: str = Field(
        default="production-secret-key-change-this",
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
    database: CockroachDBSettings = Field(default_factory=CockroachDBSettings)


# CockroachDB settings instance
cockroach_settings = CockroachSettings()