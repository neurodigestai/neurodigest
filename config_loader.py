import os
from dotenv import load_dotenv

# Load environment variables from config/.env
# override=False ensures OS-level env vars (e.g. GitHub Actions secrets)
# take priority over .env file values.
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "config", ".env"),
    override=False,
)


class Config:
    """Central configuration class.

    Priority order:
    1. OS environment variables (GitHub Actions secrets, system env)
    2. Values from config/.env file (local development)
    3. Hardcoded defaults below

    This allows the same codebase to run locally (via .env) and in
    GitHub Actions (via repository secrets injected as env vars).
    """

    APP_NAME: str = os.getenv("APP_NAME", "NeuroAIDigest")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    RUN_INTERVAL_HOURS: int = int(os.getenv("RUN_INTERVAL_HOURS", "72"))
    MAX_ITEMS_PER_RUN: int = int(os.getenv("MAX_ITEMS_PER_RUN", "60"))
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "llama-3.3-70b-versatile")
    MAX_SUMMARY_WORDS: int = int(os.getenv("MAX_SUMMARY_WORDS", "120"))
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "")
    EMAIL_APP_PASSWORD: str = os.getenv("EMAIL_APP_PASSWORD", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    DIGEST_TITLE: str = os.getenv("DIGEST_TITLE", "Neuro-AI Research Digest")
    IMAGE_MODEL_PROVIDER: str = os.getenv("IMAGE_MODEL_PROVIDER", "")
    IMAGE_API_KEY: str = os.getenv("IMAGE_API_KEY", "")
    SUBSCRIBERS_SHEET_CSV: str = os.getenv("SUBSCRIBERS_SHEET_CSV", "")
    UNSUBSCRIBE_SHEET_CSV: str = os.getenv("UNSUBSCRIBE_SHEET_CSV", "")
    UNSUBSCRIBE_FORM_URL: str = os.getenv("UNSUBSCRIBE_FORM_URL", "")


