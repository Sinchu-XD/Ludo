# services/match_service.py
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from engine.engine import LudoEngine
from engine.room import GameRoom
from engine.models import Player
from services.reward_service import RewardService
from services.room_store import ROOMS

class MatchServiceError(Exception):
    pass


class MatchService:
    """
    Coordinates a match lifecycle:
    - validate room
    - start match
    - record finish order
    - finalize & distribute rewards
    """

    def __init__(self, engine: Optional[LudoEngine] = None):
        self.engine = engine or LudoEngine()

    # ───────────────────────── START MATCH ─────────────────────────

    def start_match(self, room: GameRoom) -> None:
        if room.started:
            raise MatchServiceError("Match already started")
        if len(room.players) < 2:
            raise MatchServiceError("Not enough players to start")

        room.start_game()

    # ───────────────────────── FINISH CHECK ─────────────────────────

    @staticmethod
    def is_match_finished(room: GameRoom) -> bool:
        """
        Match is finished when:
        - required winners are decided OR
        - only required number of active players remain
        """
        active_players = [p for p in room.players if p.active]
        # Simple rule: when all but winners are finished/inactive,
        # engine/models marks token.finished; room.finished set elsewhere
        return room.finished

    # ───────────────────────── BUILD RANKING ─────────────────────────

    @staticmethod
    def build_ranking(room: GameRoom) -> List[int]:
        """
        Build ranking based on tokens finished count.
        Higher finished tokens = higher rank.
        """
        # Score players by finished tokens, then by active flag
        scored = []
        for p in room.players:
            finished_tokens = sum(1 for t in p.tokens if t.finished)
            scored.append((p.user_id, finished_tokens, p.active))

        # Sort:
        # 1) finished_tokens desc
        # 2) active desc (active > inactive)
        scored.sort(key=lambda x: (x[1], x[2]), reverse=True)

        return [uid for uid, _, _ in scored]

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

        # Build ranking
        ranking = self.build_ranking(room)

        # Player ids
        player_ids = [p.user_id for p in room.players]

        # Distribute rewards
        result = RewardService.distribute(
            db=db,
            room_id=room.room_id,
            player_ids=player_ids,
            ranking=ranking,
            entry_fee=room.entry_fee
        )

        # Mark room finished & cleanup
        room.finished = True
        ROOMS.pop(room.room_id, None)

        return {
            "room_id": room.room_id,
            "ranking": ranking,
            **result
        }
      
