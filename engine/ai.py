# engine/ai.py
import random
from engine.constants import SAFE_CELLS, MAIN_PATH_LEN

class LudoAI:
    def choose_token(self, player, dice, players):
        """
        Decide which token AI should move.
        Priority:
        1. Kill
        2. Safe move
        3. Spawn
        4. Any valid move
        """

        valid_moves = []

        for i, token in enumerate(player.tokens):
            if not self._can_move(token, dice):
                continue
            valid_moves.append(i)

        if not valid_moves:
            return None

        # 1️⃣ Try kill
        for i in valid_moves:
            if self._can_kill(player, i, dice, players):
                return i

        # 2️⃣ Safe move
        safe = [i for i in valid_moves if self._is_safe_move(player.tokens[i], dice)]
        if safe:
            return random.choice(safe)

        # 3️⃣ Spawn preference
        for i in valid_moves:
            if player.tokens[i].position == -1 and dice == 6:
                return i

        # 4️⃣ Any move
        return random.choice(valid_moves)

    def _can_move(self, token, dice):
        if token.finished:
            return False
        if token.position == -1:
            return dice == 6
        return token.position + dice <= MAIN_PATH_LEN + 5

    def _is_safe_move(self, token, dice):
        if token.position == -1:
            return False
        new_pos = token.position + dice
        return new_pos in SAFE_CELLS

    def _can_kill(self, player, token_index, dice, players):
        token = player.tokens[token_index]
        if token.position == -1:
            return False

        new_pos = token.position + dice
        if new_pos in SAFE_CELLS:
            return False

        for p in players:
            if p is player or not p.active:
                continue
            for t in p.tokens:
                if t.position == new_pos:
                    return True
        return False
      
