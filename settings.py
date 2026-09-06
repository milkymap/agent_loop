from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class LLMSettings(BaseSettings):
    gemini_api_key: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )