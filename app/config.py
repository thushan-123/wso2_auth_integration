from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field

class Settings(BaseSettings):
    ASGARDEO_DOMAIN: str
    ASGARDEO_CLIENT_ID: str
    ASGARDEO_CLIENT_SERECT: str   
    ASGARDEO_CALLBACK_URL: AnyUrl

    SESSION_SECRET: str = Field(min_length=32)
    DATABASE_URL: str = "sqlite:///./app.db"
    APP_DEBUG: bool = False
    PORT: int = 8000

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()

