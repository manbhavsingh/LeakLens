from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://leaklens:leaklens@localhost:5432/leaklens"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
