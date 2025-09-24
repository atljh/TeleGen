from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool
    SECRET_KEY: str
    ALLOWED_HOSTS: str

    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_ID: str

    OPENAI_API_KEY: str

    USERBOT_API_ID: int
    USERBOT_API_HASH: str
    TELEGRAM_PHONE: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TIMEZONE: str

    model_config = ConfigDict(env_file=".env")
