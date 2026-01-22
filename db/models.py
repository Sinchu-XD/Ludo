# db/models.py
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    ARRAY,
)
from sqlalchemy.sql import func
from db.database import Base

# ───────────────────────── USERS ─────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(64), index=True)

    coins = Column(BigInteger, default=0, nullable=False)

    total_games = Column(Integer, default=0, nullable=False)
    wins = Column(Integer, default=0, nullable=False)
    losses = Column(Integer, default=0, nullable=False)

    daily_claim_at = Column(DateTime(timezone=True), nullable=True)

    # ───── Anti-cheat / moderation ─────
    cheat_strikes = Column(Integer, default=0, nullable=False)
    last_cheat_reason = Column(Text, nullable=True)
    last_cheat_at = Column(DateTime(timezone=True), nullable=True)

    is_banned = Column(Boolean, default=False, nullable=False)
    ban_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

# ───────────────────────── MATCHES ─────────────────────────

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), index=True, nullable=False)

    players = Column(ARRAY(BigInteger), nullable=False)
    winners = Column(ARRAY(BigInteger), nullable=False)

    entry_fee = Column(BigInteger, nullable=False)
    total_pot = Column(BigInteger, nullable=False)
    bonus = Column(BigInteger, nullable=False)

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)

# ───────────────────────── TRANSACTIONS ─────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    amount = Column(BigInteger, nullable=False)
    reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

# ───────────────────────── PENALTIES (AUDIT / OPTIONAL) ─────────────────────────

class Penalty(Base):
    __tablename__ = "penalties"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True, nullable=False)

    reason = Column(Text, nullable=False)
    coins_deducted = Column(BigInteger, default=0, nullable=False)
    banned_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
