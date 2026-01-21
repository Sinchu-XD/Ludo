# features/referral.py
from sqlalchemy.orm import Session
from sqlalchemy import Column, String
from datetime import datetime

from db.models import User
from db.wallet import add_coins


# ───────── CONFIG ─────────
REFERRAL_BONUS_NEW = 100
REFERRAL_BONUS_INVITER = 150


class ReferralError(Exception):
    pass


def generate_referral_code(user_id: int) -> str:
    """
    Simple deterministic referral code
    """
    return f"LUDO{user_id}"


def apply_referral(
    db: Session,
    new_user_id: int,
    referral_code: str
):
    """
    Apply referral when a NEW user starts the bot
    """
    if not referral_code.startswith("LUDO"):
        raise ReferralError("Invalid referral code")

    inviter_id = int(referral_code.replace("LUDO", ""))

    if inviter_id == new_user_id:
        raise ReferralError("Self referral not allowed")

    inviter = db.query(User).filter(User.user_id == inviter_id).first()
    if not inviter:
        raise ReferralError("Inviter not found")

    new_user = db.query(User).filter(User.user_id == new_user_id).first()
    if not new_user:
        new_user = User(user_id=new_user_id, coins=0)
        db.add(new_user)
        db.flush()

    # Prevent double referral
    if getattr(new_user, "referred_by", None):
        raise ReferralError("Referral already applied")

    # Mark referral (dynamic attribute, or add column later)
    new_user.referred_by = inviter_id
    new_user.created_at = datetime.utcnow()

    # Reward both
    add_coins(
        db,
        user_id=new_user_id,
        amount=REFERRAL_BONUS_NEW,
        reason="Referral bonus (new user)"
    )

    add_coins(
        db,
        user_id=inviter_id,
        amount=REFERRAL_BONUS_INVITER,
        reason="Referral bonus (inviter)"
    )

    db.commit()
  
