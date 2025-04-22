from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    
    class Config:
        env_file = '.env'