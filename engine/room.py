# engine/room.py (FIXED & HARDENED)

import uuid
from typing import List, Optional
from engine.models import GameState, Player


class RoomError(Exception):
    pass


class GameRoom:
    """
    In-memory room state.
    NOT thread-safe by design — higher layer must guard calls.
    """

    def __init__(self, owner_id: int, entry_fee: int, max_players: int):
        self.room_id = str(uuid.uuid4())
        self.owner_id = owner_id
        self.entry_fee = entry_fee
        self.max_players = max_players

        self.players: List[Player] = []
        self.state: Optional[GameState] = None

        self.started = False
        self.finished = False

    # ───────────────────────── UTILS ─────────────────────────

    def is_full(self) -> bool:
        return len(self.players) >= self.max_players

    def can_start(self) -> bool:
        return len(self.players) >= 2

    def has_player(self, user_id: int) -> bool:
        return any(p.user_id == user_id for p in self.players)

    # ───────────────────────── PLAYER MGMT ─────────────────────────

    def add_player(self, player: Player):
        if self.finished:
            raise RoomError("Room already finished")

        if self.started:
            raise RoomError("Match already started")

        if self.is_full():
            raise RoomError("Room is full")

        if self.has_player(player.user_id):
            raise RoomError("Player already in room")

        player.active = True
        self.players.append(player)

        return {
            "room_id": self.room_id,
            "players": [p.user_id for p in self.players]
        }

    def remove_player(self, user_id: int):
        """
        Mark player inactive.
        If owner leaves before start → transfer ownership.
        """
        for p in self.players:
            if p.user_id == user_id:
                p.active = False

                # Owner left before start → migrate owner
                if not self.started and user_id == self.owner_id:
                    for other in self.players:
                        if other.user_id != user_id and other.active:
                            self.owner_id = other.user_id
                            break

                return True

        raise RoomError("Player not in room")

    # ───────────────────────── GAME FLOW ─────────────────────────

    def start_game(self):
        if self.finished:
            raise RoomError("Room already finished")

        if self.started:
            raise RoomError("Match already started")

        if not self.can_start():
            raise RoomError("Not enough players")

        # Ensure active players only
        active_players = [p for p in self.players if p.active]
        if len(active_players) < 2:
            raise RoomError("Not enough active players")

        self.players = active_players

        self.started = True
        self.finished = False
        self.state = GameState(self.players)

        return {
            "room_id": self.room_id,
            "players": [p.user_id for p in self.players]
        }

    def end_game(self):
        """
        Only marks flags.
        Cleanup handled by MatchService.
        """
        self.finished = True
        self.started = False
        return True
