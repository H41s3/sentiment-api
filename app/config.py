from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"
    max_length: int = 512
    port: int = 8000
    api_key: str | None = None
    cors_origins: list[str] = ["*"]
    web_concurrency: int = 2
    max_batch_size: int = 32

    class Config:
        env_file = ".env"

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if not (64 <= self.max_length <= 2048):
            raise ValueError("MAX_LENGTH must be between 64 and 2048")
        if self.web_concurrency < 1:
            raise ValueError("WEB_CONCURRENCY must be at least 1")
        if not (1 <= self.max_batch_size <= 128):
            raise ValueError("MAX_BATCH_SIZE must be between 1 and 128")
        return self


settings = Settings()
