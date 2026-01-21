# engine/room.py
import uuid
from engine.models import GameState


class GameRoom:
    def __init__(self, owner_id, entry_fee, max_players):
        self.room_id = str(uuid.uuid4())
        self.owner_id = owner_id
        self.entry_fee = entry_fee
        self.max_players = max_players

        self.players = []          # List[Player]
        self.state = None          # GameState
        self.started = False
        self.finished = False

    # ───────────────────────── UTILS ─────────────────────────

    def is_full(self):
        return len(self.players) >= self.max_players

    def can_start(self):
        return len(self.players) >= 2

    def has_player(self, user_id):
        return any(p.user_id == user_id for p in self.players)

    # ───────────────────────── PLAYER MGMT ─────────────────────────

    def add_player(self, player):
        """
        Add player to room.
        Prevent duplicates & joining after start.
        """
        if self.started or self.is_full():
            return False

        if self.has_player(player.user_id):
            return False

        # Ensure active flag exists
        if not hasattr(player, "active"):
            player.active = True
        else:
            player.active = True

        self.players.append(player)
        return True

    def remove_player(self, user_id):
        """
        Mark player inactive (used by anti-cheat / leave)
        """
        for p in self.players:
            if p.user_id == user_id:
                p.active = False
                return True
        return False

    # ───────────────────────── GAME FLOW ─────────────────────────

    def start_game(self):
        """
        Initialize GameState and start match
        """
        if self.started or not self.can_start():
            return False

        self.started = True
        self.finished = False

        # Ensure all players active at start
        for p in self.players:
            p.active = True

        self.state = GameState(self.players)
        return True

    def end_game(self):
        """
        Mark match finished (cleanup handled by services)
        """
        self.finished = True
        self.started = False
        return True
