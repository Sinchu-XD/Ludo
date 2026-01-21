# engine/constants.py

# Classic Ludo safe/star cells (0–51 main path)
SAFE_CELLS = {0, 8, 13, 21, 26, 34, 39, 47}

# Main circular path length
MAIN_PATH_LEN = 52

# Home path length (after entering)
HOME_PATH_LEN = 6  # indices: 52..57 (finish at 57)

# Player color start indices on main path
START_POSITIONS = {
    "red": 0,
    "green": 13,
    "yellow": 26,
    "blue": 39,
}

# Max tokens per player
TOKENS_PER_PLAYER = 4

# Dice rules
MAX_CONSECUTIVE_SIX = 3

