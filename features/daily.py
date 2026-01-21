# features/daily.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from db.models import User
from db.wallet import add_coins
from config import DAILY_BONUS


class DailyBonusError(Exception):
    pass


def can_claim(user: User) -> bool:
    if not user.daily_claim_at:
        return True
    return datetime.utcnow() - user.daily_claim_at >= timedelta(hours=24)


def claim_daily(db: Session, user_id: int) -> int:
    """
    Returns bonus amount if claimed successfully
    Raises DailyBonusError otherwise
    """
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        user = User(user_id=user_id, coins=0)
        db.add(user)
        db.flush()

    if not can_claim(user):
        remaining = timedelta(hours=24) - (datetime.utcnow() - user.daily_claim_at)
        raise DailyBonusError(
            f"Daily bonus already claimed. Try again in {remaining}."
        )

    # Update claim time
    user.daily_claim_at = datetime.utcnow()

    # Add coins
    add_coins(
        db,
        user_id=user_id,
        amount=DAILY_BONUS,
        reason="Daily Bonus"
    )

    db.commit()
    return DAILY_BONUS
  
