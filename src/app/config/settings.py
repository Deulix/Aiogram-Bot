from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int

    REDIS_PORT: int = 6379
    REDIS_HOST: str = "redis"
    DATABASE_URL: str = "sqlite+aiosqlite:///src/app/database/shop.db"

    MAPS_API_KEY: str
    TEST_PAYMENT_KEY: str

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False  # важность регистра env


settings = Settings()
