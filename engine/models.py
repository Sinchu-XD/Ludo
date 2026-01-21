# engine/models.py
from dataclasses import dataclass, field
from typing import List

@dataclass
class Token:
    # -1 = at home, 0..51 main path, 52..57 home path, finished=True at 57
    position: int = -1
    finished: bool = False

@dataclass
class Player:
    user_id: int
    color: str
    tokens: List[Token] = field(default_factory=list)
    active: bool = True  # false if eliminated / left

    def __post_init__(self):
        if not self.tokens:
            self.tokens = [Token() for _ in range(4)]

@dataclass
class GameState:
    players: List[Player]
    current_turn: int = 0
    dice_value: int = 0
    consecutive_six: int = 0

    def next_turn(self):
        n = len(self.players)
        for _ in range(n):
            self.current_turn = (self.current_turn + 1) % n
            if self.players[self.current_turn].active:
                break
              
