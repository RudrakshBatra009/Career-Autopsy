from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env
load_dotenv()


class Settings(BaseModel):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./career_autopsy.db")


settings = Settings()
