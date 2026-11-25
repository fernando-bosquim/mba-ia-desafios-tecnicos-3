import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "3600"))
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "dev-smtp")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "dev-only-change-me")
