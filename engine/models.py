# engine/models.py
from dataclasses import dataclass, field
from typing import List

HOME_FINISH_POS = 57


@dataclass
class Token:
    """
    -1 = at home
     0..51 = main path
    52..57 = home path
    finished = True when position == 57
    """
    position: int = -1
    finished: bool = False

    def move_to(self, pos: int):
        """
        Update token position and finished flag
        """
        self.position = pos
        if pos >= HOME_FINISH_POS:
            self.position = HOME_FINISH_POS
            self.finished = True


@dataclass
class Player:
    user_id: int
    color: str
    tokens: List[Token] = field(default_factory=list)
    active: bool = True  # False if eliminated / left

    def __post_init__(self):
        if not self.tokens:
            self.tokens = [Token() for _ in range(4)]

    def finished_tokens_count(self) -> int:
        return sum(1 for t in self.tokens if t.finished)

    def is_finished(self) -> bool:
        """
        Player is finished when all tokens reached home
        """
        return self.finished_tokens_count() == len(self.tokens)


@dataclass
class GameState:
    players: List[Player]
    current_turn: int = 0
    dice_value: int = 0
    consecutive_six: int = 0

    def next_turn(self):
        """
        Move turn to next active player.
        Returns False if no active players remain.
        """
        n = len(self.players)
        if n == 0:
            return False

        for _ in range(n):
            self.current_turn = (self.current_turn + 1) % n
            if self.players[self.current_turn].active:
                return True

        # No active players
        return False

    def active_players(self) -> List[Player]:
        return [p for p in self.players if p.active]

    def finished_players(self) -> List[Player]:
        return [p for p in self.players if p.is_finished()]
