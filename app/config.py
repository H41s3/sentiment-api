from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Sentiment API, driven entirely by environment variables.

    All fields map 1-to-1 to an env var of the same name in UPPER_SNAKE_CASE
    (e.g. MAX_LENGTH=256, API_KEY=secret). A .env file is also supported for
    local development. Validation runs at import time so a misconfigured
    container crashes immediately with a clear error rather than silently
    misbehaving on the first request.
    """

    model_config = SettingsConfigDict(env_file=".env", protected_namespaces=("settings_",))

    model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"

    # Token budget passed to the HuggingFace tokenizer. Inputs longer than this
    # are truncated by the tokenizer at the correct subword boundary.
    max_length: int = 512

    port: int = 8000

    # When None, authentication is fully disabled — zero config needed for local
    # dev and existing deployments. Set API_KEY in the environment to lock down
    # all analyze endpoints without touching any code.
    api_key: str | None = None

    cors_origins: list[str] = ["*"]

    # Number of gunicorn worker processes. Each worker holds its own copy of the
    # model in memory, so factor in available RAM/VRAM before raising this.
    # On CPU: 2 workers gives real parallelism without doubling the ~260MB footprint.
    web_concurrency: int = 2

    max_batch_size: int = 32

    # Standard Python logging level name. Accepts DEBUG, INFO, WARNING, ERROR, CRITICAL.
    log_level: str = "INFO"

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Reject obviously wrong values before the app starts accepting traffic."""
        if not (64 <= self.max_length <= 2048):
            raise ValueError("MAX_LENGTH must be between 64 and 2048")
        if self.web_concurrency < 1:
            raise ValueError("WEB_CONCURRENCY must be at least 1")
        if not (1 <= self.max_batch_size <= 128):
            raise ValueError("MAX_BATCH_SIZE must be between 1 and 128")
        import logging

        if self.log_level.upper() not in logging._nameToLevel:
            raise ValueError(f"LOG_LEVEL must be one of {list(logging._nameToLevel)}")
        return self


settings = Settings()
