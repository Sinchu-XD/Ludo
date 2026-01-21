# engine/room.py
import uuid
from engine.models import GameState

class GameRoom:
    def __init__(self, owner_id, entry_fee, max_players):
        self.room_id = str(uuid.uuid4())
        self.owner_id = owner_id
        self.entry_fee = entry_fee
        self.max_players = max_players

        self.players = []          # Player objects
        self.state = None          # GameState
        self.started = False
        self.finished = False

    def is_full(self):
        return len(self.players) >= self.max_players

    def add_player(self, player):
        if self.started or self.is_full():
            return False
        self.players.append(player)
        return True

    def remove_player(self, user_id):
        for p in self.players:
            if p.user_id == user_id:
                p.active = False
                return True
        return False

    def can_start(self):
        return len(self.players) >= 2

    def start_game(self):
        if self.started or not self.can_start():
            return False
        self.started = True
        self.state = GameState(self.players)
        return True

    def end_game(self):
        self.finished = True
      
