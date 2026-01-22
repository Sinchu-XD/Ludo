# services/reward_service.py (FIXED & HARDENED)

from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.wallet import add_coins
from db.models import Match, User
from config import GAME_BONUS_PERCENT
from utils.logger import setup_logger

log = setup_logger("reward")


class RewardServiceError(Exception):
    pass


class RewardService:
    """
    Handles reward distribution.
    MUST be called inside a DB transaction.
    """

    # ───────────────────────── WINNER COUNT ─────────────────────────

    @staticmethod
    def calculate_winners(players_count: int) -> int:
        if players_count == 2:
            return 1
        if players_count == 3:
            return 2
        if players_count == 4:
            return 3
        raise RewardServiceError("Invalid player count")

    # ───────────────────────── DISTRIBUTE ─────────────────────────

    @staticmethod
    def distribute(
        db: Session,
        room_id: str,
        player_ids: List[int],
        ranking: List[int],
        entry_fee: int
    ) -> Dict:
        """
        Atomic reward distribution.
        NO commit here — caller controls transaction.
        """

        # ───── Validation ─────
        if not player_ids or not ranking:
            raise RewardServiceError("Invalid match data")

        if entry_fee <= 0:
            raise RewardServiceError("Invalid entry fee")

        if GAME_BONUS_PERCENT < 0 or GAME_BONUS_PERCENT > 100:
            raise RewardServiceError("Invalid bonus percent")

        # ───── Idempotency check ─────
        existing = (
            db.query(Match)
            .filter(Match.room_id == room_id)
            .first()
        )
        if existing:
            log.warning(
                f"Reward already distributed | room={room_id}"
            )
            return {
                "winners": existing.winners,
                "reward_per_winner": 0,
                "total_pot": existing.total_pot,
                "bonus": existing.bonus,
            }

        total_players = len(player_ids)
        winners_count = RewardService.calculate_winners(total_players)

        winners = ranking[:winners_count]

        total_pot = entry_fee * total_players
        bonus = int(total_pot * GAME_BONUS_PERCENT / 100)
        reward_pool = total_pot + bonus
        reward_per_winner = reward_pool // winners_count

        log.info(
            f"Reward calc | room={room_id} "
            f"players={total_players} winners={winners} "
            f"pot={total_pot} bonus={bonus}"
        )

        try:
            # ───── Add coins ─────
            for uid in winners:
                add_coins(
                    db,
                    user_id=uid,
                    amount=reward_per_winner,
                    reason=f"Ludo match win ({room_id})"
                )

            # ───── Update stats ─────
            users = (
                db.query(User)
                .filter(User.user_id.in_(player_ids))
                .with_for_update()
                .all()
            )

            found_ids = {u.user_id for u in users}
            missing = set(player_ids) - found_ids
            if missing:
                raise RewardServiceError(
                    f"Users not found: {missing}"
                )

            for user in users:
                user.total_games += 1
                if user.user_id in winners:
                    user.wins += 1
                else:
                    user.losses += 1

            # ───── Save match ─────
            match = Match(
                room_id=room_id,
                players=player_ids,
                winners=winners,
                entry_fee=entry_fee,
                total_pot=total_pot,
                bonus=bonus,
            )
            db.add(match)

            log.info(
                f"Reward distributed | room={room_id} "
                f"reward={reward_per_winner}"
            )

            return {
                "winners": winners,
                "reward_per_winner": reward_per_winner,
                "total_pot": total_pot,
                "bonus": bonus,
            }

        except SQLAlchemyError as e:
            log.exception(
                f"Reward distribution failed | room={room_id}"
            )
            raise RewardServiceError("Reward distribution failed") from e
            
