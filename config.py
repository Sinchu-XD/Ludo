import os

# ───────── Telegram ─────────
API_ID = int(os.getenv("API_ID", 123456))
API_HASH = os.getenv("API_HASH", "API_HASH_HERE")
BOT_TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKEN_HERE")

# ───────── Database ─────────
DB_URL = os.getenv(
    "DB_URL",
    "postgresql://ludo:ludo@localhost:5432/ludo_db"
)

# ───────── Redis ─────────
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# ───────── Game Settings ─────────
TURN_TIME = 30           # seconds
DAILY_BONUS = 200
HOUSE_BONUS_PERCENT = 10
MAX_ROOMS_PER_USER = 3

