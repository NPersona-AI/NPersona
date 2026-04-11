"""Application configuration via environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Force-load .env before pydantic-settings reads anything.
# Try multiple locations so it works regardless of cwd or how uvicorn starts.
_HERE = Path(__file__).resolve().parent          # backend/app/
_ENV_CANDIDATES = [
    _HERE.parent / ".env",                        # backend/.env  ← primary
    _HERE.parent.parent / ".env",                 # project root/.env
]
_ENV_FILE = None
for _candidate in _ENV_CANDIDATES:
    if _candidate.exists():
        load_dotenv(dotenv_path=_candidate, override=True)
        _ENV_FILE = str(_candidate)
        break


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "Adversarial Persona Maker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- LLM Provider: "gemini" | "groq" | "openai" ---
    LLM_PROVIDER: str = "groq"

    # --- Google Gemini ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- Groq ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # --- OpenAI (fallback / optional) ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_RETRIES: int = 3

    # --- Azure OpenAI ---
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""       # e.g. https://xxx.cognitiveservices.azure.com/
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2025-01-01-preview"

    # --- Generation scaling ---
    # Max output tokens per LLM call. Set this to match your model/tier:
    #   gemini-2.0-flash (free/paid):   8,192
    #   gemini-2.5-pro (paid):         65,536  ← set for 1000+ personas fast
    #   groq llama-3.3-70b:             8,192  (but 2000 recommended to save TPD quota)
    #   gpt-4o:                        16,384
    #   gpt-4o-mini:                    16,384
    LLM_MAX_OUTPUT_TOKENS: int = 16384

    # How many persona-generation batches to run in parallel.
    # Free tier: keep at 1-2. Paid Gemini: 5-10. High-quota OpenAI: 5.
    LLM_CONCURRENCY: int = 3

    # --- Database ---
    DATABASE_PATH: str = str(Path(__file__).parent.parent / "data" / "personas.db")

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,           # pydantic-settings reads .env directly
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
