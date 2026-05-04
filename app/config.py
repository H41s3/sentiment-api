from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"
    max_length: int = 512
    port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
