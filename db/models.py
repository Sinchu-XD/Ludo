# db/models.py
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean,
    DateTime, ForeignKey, Text, ARRAY
)
from sqlalchemy.sql import func
from db.database import Base

# ───────────────────────── USERS ─────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(64))
    coins = Column(BigInteger, default=0)

    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)

    daily_claim_at = Column(DateTime)
    is_banned = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ───────────────────────── MATCHES ─────────────────────────

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), index=True)

    players = Column(ARRAY(BigInteger))     # all player IDs
    winners = Column(ARRAY(BigInteger))     # winner IDs

    entry_fee = Column(BigInteger)
    total_pot = Column(BigInteger)
    bonus = Column(BigInteger)

    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))

# ───────────────────────── TRANSACTIONS ─────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    amount = Column(BigInteger)
    reason = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ───────────────────────── PENALTIES ─────────────────────────

class Penalty(Base):
    __tablename__ = "penalties"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)

    reason = Column(Text)
    coins_deducted = Column(BigInteger, default=0)
    banned_until = Column(DateTime)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
  
