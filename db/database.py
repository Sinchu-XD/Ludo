# db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from config import DB_URL

# Base class for all DB models
Base = declarative_base()

# SQLAlchemy engine
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    poolclass=NullPool,  # Telegram bots ke liye safe
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Dependency / helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
      
