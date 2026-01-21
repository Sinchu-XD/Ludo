# services/reward_service.py
from typing import List
from sqlalchemy.orm import Session

from db.wallet import add_coins
from db.models import Match, User
from config import GAME_BONUS_PERCENT


class RewardServiceError(Exception):
    pass


class RewardService:
    """
    Handles reward distribution after a match ends
    """

    @staticmethod
    def calculate_winners(players_count: int) -> int:
        """
        Decide how many winners based on players
        """
        if players_count == 2:
            return 1
        elif players_count == 3:
            return 2
        elif players_count == 4:
            return 3
        else:
            raise RewardServiceError("Invalid player count")

    @staticmethod
    def distribute(
        db: Session,
        room_id: str,
        player_ids: List[int],
        ranking: List[int],
        entry_fee: int
    ):
        """
        ranking: list of user_ids ordered by finish position (1st -> last)
        """

        total_players = len(player_ids)
        winners_count = RewardService.calculate_winners(total_players)

        winners = ranking[:winners_count]

        total_pot = entry_fee * total_players
        bonus = int(total_pot * GAME_BONUS_PERCENT / 100)
        reward_pool = total_pot + bonus

        reward_per_winner = reward_pool // winners_count

        # ───── Distribute coins ─────
        for uid in winners:
            add_coins(
                db,
                user_id=uid,
                amount=reward_per_winner,
                reason=f"Ludo match win ({room_id})"
            )

        # ───── Update user stats ─────
        for uid in player_ids:
            user = db.query(User).filter(User.user_id == uid).first()
            if not user:
                continue

            user.total_games += 1
            if uid in winners:
                user.wins += 1
            else:
                user.losses += 1

        # ───── Save match record ─────
        match = Match(
            room_id=room_id,
            players=player_ids,
            winners=winners,
            entry_fee=entry_fee,
            total_pot=total_pot,
            bonus=bonus,
        )

        db.add(match)
        db.commit()

        return {
            "winners": winners,
            "reward_per_winner": reward_per_winner,
            "total_pot": total_pot,
            "bonus": bonus,
        }
      
