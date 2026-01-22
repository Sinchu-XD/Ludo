# db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from config import DB_URL
from utils.logger import setup_logger

log = setup_logger("database")

# ───────────────────────── BASE ─────────────────────────

Base = declarative_base()

# ───────────────────────── ENGINE ─────────────────────────

engine = create_engine(
    DB_URL,
    pool_pre_ping=True,   # dead connections auto-recover
    poolclass=NullPool,   # Telegram bots ke liye best
    future=True,
)

log.info("Database engine initialized")

# ───────────────────────── SESSION ─────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # IMPORTANT for async bot
)

# ───────────────────────── HELPER ─────────────────────────

def get_db():
    """
    Generator for DB session (FastAPI / internal use)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        log.error("DB session error", exc_info=True)
        raise
    finally:
        db.close()
