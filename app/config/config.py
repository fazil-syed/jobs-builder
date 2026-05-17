from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    GREENHOUSE_SEARCH_QUERY: str
    GREENHOUSE_URL_TEMPLATE: str

    LEVER_SEARCH_QUERY: str
    LEVER_URL_TEMPLATE: str

    POST_URL: str

    JOBS_AUTH_KEY: str


settings = Settings()
