
import os

from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

class Settings:

    APP_NAME: str = os.getenv("APP_NAME", "GK21 Player OS")

    APP_ENV: str = os.getenv("APP_ENV", "dev")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    database_url: str = DATABASE_URL

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "OPENAI")

    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-5.5")

    AI_PROMPT_VERSION: str = os.getenv("AI_PROMPT_VERSION", "v1.0.0")

settings = Settings()

