import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "3600"))
