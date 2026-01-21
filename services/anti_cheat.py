# services/anti_cheat.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from db.models import User
from db.wallet import deduct_coins, add_coins
from services.room_store import ROOMS


class AntiCheatError(Exception):
    pass


class AntiCheatService:
    """
    Handles:
    - Leave mid-game penalties
    - AFK penalties
    - Repeat abuse escalation
    """

    # ───────── CONFIG (tune as needed) ─────────
    LEAVE_FINE_COINS = 20
    AFK_FINE_COINS = 10
    MAX_STRIKES_BEFORE_TEMP_BAN = 3
    TEMP_BAN_MINUTES = 30

    @staticmethod
    def _apply_strike(db: Session, user: User, reason: str):
        """
        Increase strike count and apply temp ban if needed
        """
        user.cheat_strikes = (user.cheat_strikes or 0) + 1
        user.last_cheat_reason = reason
        user.last_cheat_at = datetime.utcnow()

        # Temp ban if exceeded
        if user.cheat_strikes >= AntiCheatService.MAX_STRIKES_BEFORE_TEMP_BAN:
            user.is_banned = True
            user.ban_until = datetime.utcnow() + timedelta(
                minutes=AntiCheatService.TEMP_BAN_MINUTES
            )

        db.commit()

    # ───────────────────────── LEAVE MID-GAME ─────────────────────────

    @staticmethod
    def handle_leave_mid_game(
        db: Session,
        room_id: str,
        user_id: int
    ):
        """
        User leaves while match is active
        """
        room = ROOMS.get(room_id)
        if not room:
            return

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return

        # Deduct fine (if possible)
        try:
            deduct_coins(
                db,
                user_id=user_id,
                amount=AntiCheatService.LEAVE_FINE_COINS,
                reason="Leave mid-game penalty"
            )
        except Exception:
            pass  # insufficient balance → ignore

        AntiCheatService._apply_strike(
            db,
            user,
            reason="Left mid-game"
        )

        # Mark player inactive in room
        for p in room.players:
            if p.user_id == user_id:
                p.active = False

    # ───────────────────────── AFK PENALTY ─────────────────────────

    @staticmethod
    def handle_afk(
        db: Session,
        room_id: str,
        user_id: int
    ):
        """
        User missed turn / AFK
        """
        room = ROOMS.get(room_id)
        if not room:
            return

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return

        try:
            deduct_coins(
                db,
                user_id=user_id,
                amount=AntiCheatService.AFK_FINE_COINS,
                reason="AFK penalty"
            )
        except Exception:
            pass

        AntiCheatService._apply_strike(
            db,
            user,
            reason="AFK during match"
        )

    # ───────────────────────── UNBAN CHECK ─────────────────────────

    @staticmethod
    def check_auto_unban(db: Session, user: User):
        """
        Auto unban user after temp ban expires
        """
        if user.is_banned and user.ban_until:
            if datetime.utcnow() >= user.ban_until:
                user.is_banned = False
                user.ban_until = None
                user.cheat_strikes = 0
                db.commit()
              
