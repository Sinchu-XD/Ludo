# engine/engine.py
import random
from engine.constants import (
    SAFE_CELLS,
    MAIN_PATH_LEN,
    HOME_PATH_LEN,
    START_POSITIONS,
    MAX_CONSECUTIVE_SIX,
)

class LudoEngine:

    # 🎲 Dice
    def roll_dice(self):
        return random.randint(1, 6)

    # ✅ Check if a token can move with given dice
    def can_move(self, token, dice):
        if token.finished:
            return False

        # Spawn from home
        if token.position == -1:
            return dice == 6

        # Main path
        if 0 <= token.position < MAIN_PATH_LEN:
            # entering home path requires exact
            if token.position + dice > MAIN_PATH_LEN + HOME_PATH_LEN - 1:
                return False
            return True

        # Home path
        if MAIN_PATH_LEN <= token.position < MAIN_PATH_LEN + HOME_PATH_LEN:
            return token.position + dice <= MAIN_PATH_LEN + HOME_PATH_LEN - 1

        return False

    # ▶️ Move token and apply rules
    def move_token(self, player, token_index, dice, players):
        token = player.tokens[token_index]

        if not self.can_move(token, dice):
            return {"result": "invalid"}

        # Spawn
        if token.position == -1 and dice == 6:
            token.position = START_POSITIONS[player.color]
            return {"result": "spawn", "bonus": True}

        old_pos = token.position
        token.position += dice

        # Finish
        finish_pos = MAIN_PATH_LEN + HOME_PATH_LEN - 1
        if token.position == finish_pos:
            token.finished = True
            return {"result": "finish", "bonus": True}

        # Kill check (only on main path & non-safe)
        if 0 <= token.position < MAIN_PATH_LEN and token.position not in SAFE_CELLS:
            for p in players:
                if p is player or not p.active:
                    continue
                for t in p.tokens:
                    if t.position == token.position:
                        t.position = -1  # send home
                        return {"result": "kill", "bonus": True}

        return {"result": "move", "bonus": False}

    # 🔁 Handle dice rules (3 six penalty)
    def handle_dice_rules(self, state, dice):
        if dice == 6:
            state.consecutive_six += 1
            if state.consecutive_six >= MAX_CONSECUTIVE_SIX:
                state.consecutive_six = 0
                state.next_turn()
                return {"extra_turn": False, "penalty": True}
            return {"extra_turn": True, "penalty": False}
        else:
            state.consecutive_six = 0
            state.next_turn()
            return {"extra_turn": False, "penalty": False}
                      
