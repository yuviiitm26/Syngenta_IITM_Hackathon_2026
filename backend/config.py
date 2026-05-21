import logging
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("syngenta-copilot")

class Settings(BaseSettings):
    app_name: str = "Syngenta Co-Pilot Enterprise API"
    version: str = "1.0.0"
    debug: bool = False
    
    # Auth
    jwt_secret_key: str = "your-super-secret-key-change-me" # Should be set in .env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    
    # External APIs
    gemini_api_key: str = ""
    frontend_url: str = "http://localhost:5173"
    
    # Database
    db_path: str = "syngenta_prod.db"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
