# config.py (FINAL – PRODUCTION SAFE)

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ───────────────────────── TELEGRAM ─────────────────────────

def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env variable: {name}")
    return val

API_ID = int(_require("API_ID"))
API_HASH = _require("API_HASH")
BOT_TOKEN = _require("BOT_TOKEN")

# ───────────────────────── DATABASE ─────────────────────────
# Example:
# postgresql+psycopg2://user:password@localhost:5432/ludo_db

DB_URL = _require("DATABASE_URL")

# ───────────────────────── GAME ECONOMY ─────────────────────────

GAME_BONUS_PERCENT = int(os.getenv("GAME_BONUS_PERCENT", "10"))
DEFAULT_ENTRY_FEE = int(os.getenv("DEFAULT_ENTRY_FEE", "50"))

if not (0 <= GAME_BONUS_PERCENT <= 100):
    raise RuntimeError("GAME_BONUS_PERCENT must be between 0 and 100")

# ───────────────────────── DAILY BONUS ─────────────────────────

DAILY_BONUS_MIN = int(os.getenv("DAILY_BONUS_MIN", "10"))
DAILY_BONUS_MAX = int(os.getenv("DAILY_BONUS_MAX", "30"))

if DAILY_BONUS_MIN > DAILY_BONUS_MAX:
    raise RuntimeError("DAILY_BONUS_MIN cannot be greater than DAILY_BONUS_MAX")

# ───────────────────────── ANTI-CHEAT / TIMEOUT ─────────────────────────

TURN_TIMEOUT_SECONDS = int(os.getenv("TURN_TIMEOUT_SECONDS", "30"))
if TURN_TIMEOUT_SECONDS < 10:
    raise RuntimeError("TURN_TIMEOUT_SECONDS too low (min 10s)")

# ───────────────────────── ADMIN PANEL ─────────────────────────

ADMIN_JWT_SECRET = _require("ADMIN_JWT_SECRET")
ADMIN_JWT_EXPIRE_MINUTES = int(
    os.getenv("ADMIN_JWT_EXPIRE_MINUTES", "1440")
)

ADMIN_OWNERS = [
    int(x)
    for x in os.getenv("ADMIN_OWNERS", "").split(",")
    if x.strip().isdigit()
]

# ───────────────────────── ENV / DEBUG ─────────────────────────

ENV = os.getenv("ENV", "development").lower()
DEBUG = ENV != "production"
