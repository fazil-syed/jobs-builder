from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
                        env_file=".env",
                        extra="allow"
                    )
        
    SEARCH_QUERY : str
    

settings = Settings()