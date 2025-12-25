from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).parents[3] / ".env"
        ),  # расположение env файла, эквивалентно С:\Users\Artur\Desktop\Aiogram Bot\.env
        env_file_encoding="utf-8",
        case_sensitive=False,  # важность регистра env
    )
    BOT_TOKEN: str
    ADMIN_ID: int

    REDIS_PORT: int = 6379
    REDIS_HOST: str = "localhost"
    DATABASE_URL: str = "sqlite+aiosqlite:///src/app/database/shop.db"

    MAPS_API_KEY: str
    TEST_PAYMENT_KEY: str

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
