from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expires_minutes: int
    database_url: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    ANTHROPIC_API_KEY: str
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # --- LLM ---------------------------------------------------------------
    LLM_MODEL: str = "claude-haiku-4-5"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 4096

    # --- Agent orchestration (phase 5) -------------------------------------
    # Upper bound on agent <-> tool round trips before LangGraph aborts the run.
    AGENT_RECURSION_LIMIT: int = 18
    # How many times the itinerary workflow may re-draft after a failed review.
    ITINERARY_MAX_REVISIONS: int = 2

    # --- External tool APIs (all keyless) ----------------------------------
    TOOL_HTTP_TIMEOUT: float = 15.0
    OPEN_METEO_GEOCODING_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
    OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org/search"
    # Nominatim's usage policy requires an identifying User-Agent.
    NOMINATIM_USER_AGENT: str = "ai-vacation-planner/0.1 (capstone project)"


settings = Settings()  # type: ignore[call-arg]
