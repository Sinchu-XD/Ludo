# features/daily.py (FINAL FIXED VERSION)

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from config import DAILY_BONUS_MIN, DAILY_BONUS_MAX
from db.models import User
from db.wallet import add_coins


class DailyBonusError(Exception):
    pass


def can_claim(user: User) -> bool:
    if not user.last_daily_bonus:
        return True
    return datetime.utcnow() - user.last_daily_bonus >= timedelta(hours=24)


def claim_daily(db: Session, user_id: int) -> int:
    """
    Returns bonus amount if claimed successfully
    Raises DailyBonusError otherwise
    """

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise DailyBonusError("User not found")

    if not can_claim(user):
        remaining = timedelta(hours=24) - (
            datetime.utcnow() - user.last_daily_bonus
        )
        hours = int(remaining.total_seconds() // 3600)
        raise DailyBonusError(
            f"⏳ Daily bonus already claimed. Try again in {hours}h"
        )

    bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)

    add_coins(
        db,
        user_id=user_id,
        amount=bonus,
        reason="daily_bonus"
    )

    user.last_daily_bonus = datetime.utcnow()
    db.commit()

    return bonus
