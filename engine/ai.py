# engine/ai.py
import random
from engine.constants import SAFE_CELLS, MAIN_PATH_LEN


class LudoAI:
    def choose_token(self, player, dice, players):
        """
        Decide which token AI should move.
        Priority:
        1. Kill
        2. Spawn (dice == 6)
        3. Safe move
        4. Any valid move
        """

        valid_moves = []

        for i, token in enumerate(player.tokens):
            if self._can_move(token, dice):
                valid_moves.append(i)

        if not valid_moves:
            return None

        # 1️⃣ Try kill
        for i in valid_moves:
            if self._can_kill(player, i, dice, players):
                return i

        # 2️⃣ Spawn preference (real ludo behaviour)
        if dice == 6:
            spawn_moves = [
                i for i in valid_moves
                if player.tokens[i].position == -1
            ]
            if spawn_moves:
                return random.choice(spawn_moves)

        # 3️⃣ Safe move
        safe_moves = [
            i for i in valid_moves
            if self._is_safe_move(player.tokens[i], dice)
        ]
        if safe_moves:
            return random.choice(safe_moves)

        # 4️⃣ Any valid move
        return random.choice(valid_moves)

    def _can_move(self, token, dice):
        """
        Check if token can legally move
        """
        if token.finished:
            return False

        # Spawn
        if token.position == -1:
            return dice == 6

        new_pos = token.position + dice

        # Do not overflow home path
        max_pos = MAIN_PATH_LEN + 5
        return new_pos <= max_pos

    def _is_safe_move(self, token, dice):
        """
        Check if move lands on safe cell
        """
        if token.position == -1:
            return False

        new_pos = token.position + dice
        return new_pos in SAFE_CELLS

    def _can_kill(self, player, token_index, dice, players):
        """
        Check if this move kills any opponent token
        """
        token = player.tokens[token_index]

        if token.position == -1:
            return False

        new_pos = token.position + dice

        # Cannot kill on safe cells
        if new_pos in SAFE_CELLS:
            return False

        for p in players:
            if p is player or not getattr(p, "active", True):
                continue

            for t in p.tokens:
                if t.position == new_pos:
                    return True

        return False
