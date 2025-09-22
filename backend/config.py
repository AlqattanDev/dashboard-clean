"""
Configuration settings for the dashboard backend
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB settings
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "clean_dashboard"
    
    # JWT settings
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # LDAP settings (optional)
    ldap_enabled: bool = False
    ldap_server: str = "ldap://localhost:389"
    ldap_base_dn: str = "dc=example,dc=com"
    ldap_user_dn_template: str = "uid={username},ou=users,{base_dn}"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    login_rate_limit_per_minute: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()