# services/match_service.py
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from engine.engine import LudoEngine
from engine.room import GameRoom
from engine.models import Player
from services.reward_service import RewardService
from services.room_store import ROOMS
from utils.logger import setup_logger

log = setup_logger("match")


class MatchServiceError(Exception):
    pass


class MatchService:
    """
    Coordinates a match lifecycle:
    - validate room
    - start match
    - build ranking
    - finalize & distribute rewards
    """

    def __init__(self, engine: Optional[LudoEngine] = None):
        self.engine = engine or LudoEngine()

    # ───────────────────────── START MATCH ─────────────────────────

    def start_match(self, room: GameRoom) -> None:
        """
        Start a match if room is valid
        """
        if room.started:
            raise MatchServiceError("Match already started")

        if len(room.players) < 2:
            raise MatchServiceError("Not enough players to start")

        room.start_game()
        log.info(
            f"Match started | room={room.room_id} "
            f"players={[p.user_id for p in room.players]}"
        )

    # ───────────────────────── FINISH CHECK ─────────────────────────

    @staticmethod
    def is_match_finished(room: GameRoom) -> bool:
        """
        Match is finished when room.finished is set.
        """
        return room.finished

    # ───────────────────────── BUILD RANKING ─────────────────────────

    @staticmethod
    def build_ranking(room: GameRoom) -> List[int]:
        """
        Build ranking based on:
        1) finished tokens count (desc)
        2) active status (active > inactive)
        """
        scored = []

        for p in room.players:
            finished_tokens = sum(1 for t in p.tokens if t.finished)
            scored.append((p.user_id, finished_tokens, p.active))

        # Sort by finished tokens, then active flag
        scored.sort(key=lambda x: (x[1], x[2]), reverse=True)

        ranking = [uid for uid, _, _ in scored]

        log.info(
            f"Ranking built | room={room.room_id} ranking={ranking}"
        )

        return ranking

    # ───────────────────────── FINALIZE MATCH ─────────────────────────

    def finalize_match(
        self,
        db: Session,
        room: GameRoom
    ) -> Dict:
        """
        Finalize match:
        - compute ranking
        - distribute rewards
        - persist match
        - cleanup room
        """
        if not room.started:
            raise MatchServiceError("Match not started")

        log.info(f"Finalizing match | room={room.room_id}")

        # Build ranking
        ranking = self.build_ranking(room)

        # Player IDs
        player_ids = [p.user_id for p in room.players]

        # Distribute rewards
        result = RewardService.distribute(
            db=db,
            room_id=room.room_id,
            player_ids=player_ids,
            ranking=ranking,
            entry_fee=room.entry_fee
        )

        log.info(
            f"Rewards distributed | room={room.room_id} result={result}"
        )

        # Mark room finished & cleanup
        room.finished = True
        room.started = False
        ROOMS.pop(room.room_id, None)

        log.info(f"Room cleaned up | room={room.room_id}")

        return {
            "room_id": room.room_id,
            "ranking": ranking,
            **result
        }
      
