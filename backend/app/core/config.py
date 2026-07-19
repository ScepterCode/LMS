"""
Configuration settings for the Learnlyf backend.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: Optional[str] = None
    USE_DIRECT_POSTGRES: bool = False
    
    # JWT Authentication
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Security
    BCRYPT_ROUNDS: int = 12
    COOKIE_NAME: str = "access_token"
    COOKIE_MAX_AGE: int = 86400  # 24 hours in seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = [
            str(Path(__file__).resolve().parents[3] / ".env"),
            str(Path(__file__).resolve().parents[2] / ".env"),
            ".env",
        ]
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_available(self) -> bool:
        """Check if direct PostgreSQL is explicitly enabled and configured."""
        return bool(self.DATABASE_URL and self.USE_DIRECT_POSTGRES)
    
    @property
    def supabase_available(self) -> bool:
        """Check if Supabase is configured for backend use."""
        return bool(self.SUPABASE_URL and (self.SUPABASE_SERVICE_KEY or self.SUPABASE_KEY))
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins from ALLOWED_ORIGINS, in both dev and production.

        Set ALLOWED_ORIGINS to the deployed frontend's real origin(s) in
        production - there is no hardcoded fallback domain, since a wrong
        guess here silently breaks every cross-origin request.
        """
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',') if origin.strip()]
        return self.ALLOWED_ORIGINS


# Create global settings instance
settings = Settings()

# Validate critical settings
if settings.USE_DIRECT_POSTGRES and not settings.DATABASE_URL:
    print("⚠️  WARNING: USE_DIRECT_POSTGRES=true but DATABASE_URL is not set.")
    print("   The app will fall back to Supabase only.")

if not settings.SUPABASE_URL or not (settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY):
    print("⚠️  WARNING: Supabase configuration is incomplete.")
    print("   Some features may not work correctly.")
    print("   Set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file.")

if settings.JWT_SECRET == "your-super-secret-jwt-key-change-in-production":
    print("⚠️  WARNING: Using default JWT_SECRET.")
    print("   Change JWT_SECRET in production for security.")


def print_config_summary():
    """Print a summary of the current configuration."""
    print("\n" + "=" * 60)
    print("LEARNLYF - CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Server: http://{settings.HOST}:{settings.PORT}")
    print(f"Direct PostgreSQL Enabled: {settings.USE_DIRECT_POSTGRES}")
    print(f"Database Available: {settings.database_available}")
    print(f"Supabase Available: {settings.supabase_available}")
    print(f"CORS Origins: {', '.join(settings.get_cors_origins())}")
    print("=" * 60 + "\n")


# Print config summary when module is loaded
if __name__ == "__main__":
    print_config_summary()
else:
    # Only print in development
    if settings.ENVIRONMENT == "development":
        print_config_summary()