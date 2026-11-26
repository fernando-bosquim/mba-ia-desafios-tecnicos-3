import os


def _parse_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
DEBUG = _parse_bool(os.environ.get("DEBUG"), default=False)
APP_ENV = os.environ.get("APP_ENV", "producao")
APP_VERSION = "1.0.0"

DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "3600"))
