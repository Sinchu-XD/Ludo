# services/match_service.py (FIXED)

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from engine.engine import LudoEngine
from engine.room import GameRoom
from services.reward_service import RewardService
from services.room_store import ROOMS
from utils.logger import setup_logger

log = setup_logger("match")


class MatchServiceError(Exception):
    pass


class MatchService:
    """
    Coordinates a match lifecycle safely:
    - start match
    - build fair ranking
    - finalize exactly once
    """

    def __init__(self, engine: Optional[LudoEngine] = None):
        self.engine = engine or LudoEngine()

    # ───────────────────────── START MATCH ─────────────────────────

    def start_match(self, room: GameRoom) -> None:
        if room.started or room.finished:
            raise MatchServiceError("Match already started or finished")

        if len(room.players) < 2:
            raise MatchServiceError("Not enough players to start")

        room.start_game()

        log.info(
            f"Match started | room={room.room_id} "
            f"players={[p.user_id for p in room.players]}"
        )

    # ───────────────────────── BUILD RANKING ─────────────────────────

    @staticmethod
    def build_ranking(room: GameRoom) -> List[int]:
        """
        Ranking rules:
        1) Finished players first
        2) More finished tokens
        3) Active players > inactive (AFK/left go last)
        """
        scored = []

        for p in room.players:
            finished_tokens = sum(1 for t in p.tokens if t.finished)
            finished_all = finished_tokens == len(p.tokens)

            scored.append((
                p.user_id,
                finished_all,        # winner first
                finished_tokens,
                p.active              # AFK players go down
            ))

        scored.sort(
            key=lambda x: (x[1], x[2], x[3]),
            reverse=True
        )

        ranking = [uid for uid, *_ in scored]

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
        Finalize match EXACTLY ONCE (idempotent)
        """
        if room.finished:
            log.warning(
                f"Finalize skipped (already finished) | room={room.room_id}"
            )
            return {}

        if not room.started:
            raise MatchServiceError("Match not started")

        log.info(f"Finalizing match | room={room.room_id}")

        try:
            ranking = self.build_ranking(room)
            player_ids = [p.user_id for p in room.players]

            result = RewardService.distribute(
                db=db,
                room_id=room.room_id,
                player_ids=player_ids,
                ranking=ranking,
                entry_fee=room.entry_fee
            )

            room.finished = True
            room.started = False

            log.info(
                f"Rewards distributed | room={room.room_id} result={result}"
            )

            return {
                "room_id": room.room_id,
                "ranking": ranking,
                **result
            }

        except SQLAlchemyError as e:
            log.exception(
                f"DB error during finalize | room={room.room_id}"
            )
            raise MatchServiceError("Match finalize failed") from e

        finally:
            # Cleanup ALWAYS
            ROOMS.pop(room.room_id, None)
            log.info(f"Room cleaned up | room={room.room_id}")
            
