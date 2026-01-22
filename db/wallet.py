# db/wallet.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import User, Transaction
from utils.logger import setup_logger

log = setup_logger("wallet")


class WalletError(Exception):
    pass


# ───────────────────────── BALANCE ─────────────────────────

def get_balance(db: Session, user_id: int) -> int:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise WalletError("User not found")
    return user.coins


# ───────────────────────── ADD COINS ─────────────────────────

def add_coins(
    db: Session,
    user_id: int,
    amount: int,
    reason: str = ""
):
    if amount <= 0:
        return

    try:
        # Row-level lock to avoid race conditions
        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .with_for_update()
            .first()
        )

        if not user:
            user = User(
                user_id=user_id,
                coins=0,
            )
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

        log.info(
            f"Coins added | user={user_id} amount={amount} "
            f"balance={user.coins} reason={reason}"
        )

    except SQLAlchemyError as e:
        db.rollback()
        log.error(
            f"Add coins failed | user={user_id} amount={amount}",
            exc_info=True
        )
        raise WalletError(str(e))


# ───────────────────────── DEDUCT COINS ─────────────────────────

def deduct_coins(
    db: Session,
    user_id: int,
    amount: int,
    reason: str = ""
):
    if amount <= 0:
        return

    try:
        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .with_for_update()
            .first()
        )

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

        log.info(
            f"Coins deducted | user={user_id} amount={amount} "
            f"balance={user.coins} reason={reason}"
        )

    except WalletError:
        db.rollback()
        raise

    except SQLAlchemyError as e:
        db.rollback()
        log.error(
            f"Deduct coins failed | user={user_id} amount={amount}",
            exc_info=True
        )
        raise WalletError(str(e))
