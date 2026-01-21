# db/wallet.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import User, Transaction


class WalletError(Exception):
    pass


def get_balance(db: Session, user_id: int) -> int:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise WalletError("User not found")
    return user.coins


def add_coins(db: Session, user_id: int, amount: int, reason: str = ""):
    if amount <= 0:
        return

    try:
        user = db.query(User).filter(User.user_id == user_id).with_for_update().first()
        if not user:
            user = User(user_id=user_id, coins=0)
            db.add(user)
            db.flush()

        user.coins += amount

        tx = Transaction(
            user_id=user_id,
            amount=amount,
            reason=reason
        )
        db.add(tx)
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        raise WalletError(str(e))


def deduct_coins(db: Session, user_id: int, amount: int, reason: str = ""):
    if amount <= 0:
        return

    try:
        user = db.query(User).filter(User.user_id == user_id).with_for_update().first()
        if not user:
            raise WalletError("User not found")

        if user.coins < amount:
            raise WalletError("Insufficient balance")

        user.coins -= amount

        tx = Transaction(
            user_id=user_id,
            amount=-amount,
            reason=reason
        )
        db.add(tx)
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        raise WalletError(str(e))
      
