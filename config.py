# config.py
import os

# ───────────────────────── TELEGRAM ─────────────────────────
# https://my.telegram.org se lo
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH_HERE")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ───────────────────────── DATABASE ─────────────────────────
# PostgreSQL recommended
# Example:
# postgresql+psycopg2://user:password@localhost:5432/ludo_db
DB_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/ludo_bot"
)

# ───────────────────────── GAME ECONOMY ─────────────────────────
# Total pot ka kitna % bonus milega (admin funded)
GAME_BONUS_PERCENT = int(os.getenv("GAME_BONUS_PERCENT", "10"))

# Entry fees (default presets)
DEFAULT_ENTRY_FEE = int(os.getenv("DEFAULT_ENTRY_FEE", "50"))

# ───────────────────────── DAILY BONUS ─────────────────────────
DAILY_BONUS_MIN = int(os.getenv("DAILY_BONUS_MIN", "10"))
DAILY_BONUS_MAX = int(os.getenv("DAILY_BONUS_MAX", "30"))

# ───────────────────────── ANTI-CHEAT / TIMEOUT ─────────────────────────
TURN_TIMEOUT_SECONDS = int(os.getenv("TURN_TIMEOUT_SECONDS", "30"))

# ───────────────────────── ADMIN PANEL ─────────────────────────
# Simple JWT secret (change in production)
ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "CHANGE_ME_SECRET")
ADMIN_JWT_EXPIRE_MINUTES = int(os.getenv("ADMIN_JWT_EXPIRE_MINUTES", "1440"))

# Owner Telegram IDs (comma separated)
# Example: "12345678,98765432"
ADMIN_OWNERS = [
    int(x) for x in os.getenv("ADMIN_OWNERS", "").split(",") if x.strip().isdigit()
]

# ───────────────────────── MISC ─────────────────────────
ENV = os.getenv("ENV", "development")  # development / production
DEBUG = ENV != "production"
