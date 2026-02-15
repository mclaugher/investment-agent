"""Application configuration via Pydantic BaseSettings (per §14 Environment Configuration)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All settings loaded from environment variables / .env file."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # --- Required ---
    anthropic_api_key: str = ""
    fmp_api_key: str = ""
    sec_user_agent: str = "Superhuman Alpha Fund admin@yourdomain.com"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://superhuman:superhuman@localhost:5432/superhuman_alpha_fund"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- ChromaDB ---
    chroma_host: str = "localhost"
    chroma_port: int = 8100

    # --- JWT Auth ---
    jwt_secret: str = "change_this_to_a_random_string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # --- Portfolio Defaults ---
    initial_cash_balance: int = 100_000
    default_aggressiveness: int = 5

    # --- Auth ---
    admin_username: str = "admin"
    admin_password: str = "change_me"

    # --- Optional ---
    newsapi_key: str = ""
    alpha_vantage_key: str = ""


settings = Settings()
