# engine/engine.py
import random
from engine.constants import (
    SAFE_CELLS,
    MAIN_PATH_LEN,
    HOME_PATH_LEN,
    START_POSITIONS,
    MAX_CONSECUTIVE_SIX,
)
from engine.models import HOME_FINISH_POS


class LudoEngine:

    # ───────────────────────── DICE ─────────────────────────

    def roll_dice(self) -> int:
        return random.randint(1, 6)

    # ───────────────────────── MOVE CHECK ─────────────────────────

    def can_move(self, token, dice: int) -> bool:
        if token.finished:
            return False

        # Spawn
        if token.position == -1:
            return dice == 6

        new_pos = token.position + dice
        return new_pos <= HOME_FINISH_POS

    # ───────────────────────── MOVE TOKEN ─────────────────────────

    def move_token(self, player, token_index: int, dice: int, players):
        token = player.tokens[token_index]

        if not self.can_move(token, dice):
            return {
                "result": "invalid",
                "bonus": False,
                "player_finished": False,
            }

        # Spawn
        if token.position == -1 and dice == 6:
            token.move_to(START_POSITIONS[player.color])
            return {
                "result": "spawn",
                "bonus": True,
                "player_finished": False,
            }

        # Normal move
        new_pos = token.position + dice
        token.move_to(new_pos)

        # Finish token
        if token.finished:
            return {
                "result": "finish",
                "bonus": True,
                "player_finished": player.is_finished(),
            }

        # Kill check (main path & non-safe)
        if 0 <= token.position < MAIN_PATH_LEN and token.position not in SAFE_CELLS:
            for p in players:
                if p is player or not p.active:
                    continue
                for t in p.tokens:
                    if t.position == token.position and not t.finished:
                        t.position = -1
                        t.finished = False
                        return {
                            "result": "kill",
                            "bonus": True,
                            "player_finished": False,
                        }

        return {
            "result": "move",
            "bonus": False,
            "player_finished": False,
        }

    # ───────────────────────── DICE RULES ─────────────────────────

    def handle_dice_rules(self, state, dice: int):
        """
        Handles 3 consecutive six rule & turn switching.
        """
        if dice == 6:
            state.consecutive_six += 1
            if state.consecutive_six >= MAX_CONSECUTIVE_SIX:
                state.consecutive_six = 0
                state.next_turn()
                return {
                    "extra_turn": False,
                    "penalty": True,
                }
            return {
                "extra_turn": True,
                "penalty": False,
            }

        # Non-6
        state.consecutive_six = 0
        state.next_turn()
        return {
            "extra_turn": False,
            "penalty": False,
        }
