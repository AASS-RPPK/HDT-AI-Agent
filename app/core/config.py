from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PORT: int = Field(default=8000, ge=1, le=65535)
    DATABASE_URL: str

    # Google Gemini API key from https://aistudio.google.com/api-keys
    GEMINI_API_KEY: str

    # Gemini model to use for chat completions.
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # API Gateway base URL used to enrich chatbot context.
    API_GATEWAY_URL: str = "http://api-gateway:8000"
    CONTEXT_FETCH_LIMIT: int = Field(default=20, ge=1, le=200)

    # Comma-separated allowed origins for CORS.
    CORS_ORIGINS: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _normalize_cors_origins(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v)

    def cors_origins_list(self) -> list[str]:
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
