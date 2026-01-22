# features/daily.py (FINAL – MODEL COMPATIBLE)

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from config import DAILY_BONUS_MIN, DAILY_BONUS_MAX
from db.models import User
from db.wallet import add_coins


class DailyBonusError(Exception):
    pass


def can_claim(user: User) -> bool:
    if not user.daily_claim_at:
        return True
    return datetime.utcnow() - user.daily_claim_at >= timedelta(hours=24)


def claim_daily(db: Session, user_id: int) -> int:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise DailyBonusError("User not found")

    if not can_claim(user):
        remaining = timedelta(hours=24) - (
            datetime.utcnow() - user.daily_claim_at
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

    user.daily_claim_at = datetime.utcnow()
    db.commit()

    return bonus
