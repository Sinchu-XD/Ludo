# db/wallet.py (FIXED & HARDENED)

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import User, Transaction
from utils.logger import setup_logger

log = setup_logger("wallet")


class WalletError(Exception):
    pass


# ───────────────────────── HELPERS ─────────────────────────

def _validate_amount(amount: int):
    if not isinstance(amount, int) or amount <= 0:
        raise WalletError("Invalid amount")


# ───────────────────────── BALANCE ─────────────────────────

def get_balance(db: Session, user_id: int) -> int:
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise WalletError("User not found")
    return user.coins


# ───────────────────────── ADD COINS ─────────────────────────

def add_coins(
    db: Session,
    user_id: int,
    amount: int,
    reason: str
) -> int:
    """
    Adds coins atomically.
    COMMIT MUST BE HANDLED BY CALLER.
    """
    _validate_amount(amount)

    if not reason:
        raise WalletError("Reason required")

    try:
        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .with_for_update()
            .first()
        )

        if not user:
            raise WalletError("User not found")

        user.coins += amount

        tx = Transaction(
            user_id=user_id,
            amount=amount,
            reason=reason
        )
        db.add(tx)

        log.info(
            f"Coins added | user={user_id} amount={amount} "
            f"balance={user.coins} reason={reason}"
        )

        return user.coins

    except WalletError:
        raise

    except SQLAlchemyError as e:
        log.exception(
            f"Add coins failed | user={user_id} amount={amount}"
        )
        raise WalletError("Add coins failed") from e


# ───────────────────────── DEDUCT COINS ─────────────────────────

def deduct_coins(
    db: Session,
    user_id: int,
    amount: int,
    reason: str
) -> int:
    """
    Deduct coins atomically.
    COMMIT MUST BE HANDLED BY CALLER.
    """
    _validate_amount(amount)

    if not reason:
        raise WalletError("Reason required")

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

        log.info(
            f"Coins deducted | user={user_id} amount={amount} "
            f"balance={user.coins} reason={reason}"
        )

        return user.coins

    except WalletError:
        raise

    except SQLAlchemyError as e:
        log.exception(
            f"Deduct coins failed | user={user_id} amount={amount}"
        )
        raise WalletError("Deduct coins failed") from e
        
