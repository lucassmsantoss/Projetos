from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    sleeper_league_id: str
    fantasypros_api_key: str
    nfl_season: int = 2026
    database_url: str = "sqlite:///./data/app.db"


settings = Settings()
