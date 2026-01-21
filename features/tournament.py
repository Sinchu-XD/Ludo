# features/tournament.py
from sqlalchemy.orm import Session
from datetime import datetime

from db.models import Match, User
from db.wallet import deduct_coins, add_coins


class TournamentError(Exception):
    pass


class Tournament:
    """
    Simple tournament model (knockout / pool based).
    High-level logic – match engine se integrate hota hai.
    """

    def __init__(self, name: str, entry_fee: int, max_players: int):
        self.name = name
        self.entry_fee = entry_fee
        self.max_players = max_players
        self.players = []          # list of user_ids
        self.started = False
        self.finished = False
        self.created_at = datetime.utcnow()

    # ───────── Join tournament ─────────
    def join(self, db: Session, user_id: int):
        if self.started:
            raise TournamentError("Tournament already started")

        if user_id in self.players:
            raise TournamentError("Already joined")

        if len(self.players) >= self.max_players:
            raise TournamentError("Tournament is full")

        # Deduct entry fee
        deduct_coins(
            db,
            user_id=user_id,
            amount=self.entry_fee,
            reason=f"Tournament entry: {self.name}"
        )

        self.players.append(user_id)

    # ───────── Start tournament ─────────
    def start(self):
        if self.started:
            raise TournamentError("Tournament already started")

        if len(self.players) < 2:
            raise TournamentError("Not enough players")

        self.started = True

    # ───────── Finish & distribute prizes ─────────
    def finish(self, db: Session, winners: list[int]):
        """
        winners: list of user_ids (order = rank)
        """
        if self.finished:
            raise TournamentError("Tournament already finished")

        total_pot = self.entry_fee * len(self.players)
        bonus = int(total_pot * 0.10)
        prize_pool = total_pot + bonus

        if not winners:
            raise TournamentError("No winners provided")

        share = prize_pool // len(winners)

        for uid in winners:
            add_coins(
                db,
                user_id=uid,
                amount=share,
                reason=f"Tournament win: {self.name}"
            )

        self.finished = True

        # Optional: store as a Match record
        match = Match(
            room_id=f"tournament:{self.name}",
            players=self.players,
            winners=winners,
            entry_fee=self.entry_fee,
            total_pot=total_pot,
            bonus=bonus,
            started_at=self.created_at,
            ended_at=datetime.utcnow(),
        )
        db.add(match)
        db.commit()

