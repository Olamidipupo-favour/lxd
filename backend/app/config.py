from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    APP_ENV: str = "prod"
    APP_SECRET: str = Field(..., min_length=32)
    API_BASE_URL: str
    TRACKING_DOMAIN: str = ""
    ADMIN_BASE_URL: str = ""
    CORS_ORIGINS: str = ""

    INTERNAL_CRON_SECRET: str

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    DATABASE_URL: str

    PIXEL_PATH: str = "/o"
    CLICK_PATH: str = "/c"
    UNSUB_PATH: str = "/unsubscribe"

    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "none"
    JWT_ACCESS_TTL_MIN: int = 60
    JWT_REFRESH_TTL_DAYS: int = 7

    @property
    def cors_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
