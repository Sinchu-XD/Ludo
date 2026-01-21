# renderer/board.py
from PIL import Image, ImageDraw

BOARD_IMAGE_PATH = "assets/board.png"
OUTPUT_IMAGE_PATH = "assets/board_render.png"

TOKEN_COLORS = {
    "red": (220, 20, 60),
    "green": (0, 180, 0),
    "yellow": (255, 215, 0),
    "blue": (30, 144, 255),
}

TOKEN_RADIUS = 10
STACK_OFFSET = 6  # multiple tokens ek cell pe ho to thoda shift

# ⚠️ IMPORTANT:
# Ye coordinates tumhare board.png ke hisaab se adjust honge
CELL_COORDS = {
    0: (300, 40), 1: (340, 40), 2: (380, 40), 3: (420, 40),
    4: (460, 40), 5: (500, 40),
    # ... (6–51 complete karna hoga same pattern)
    52: (300, 80), 53: (300, 120), 54: (300, 160),
    55: (300, 200), 56: (300, 240), 57: (300, 280),
}

class BoardRenderer:
    def __init__(self, board_path: str = BOARD_IMAGE_PATH):
        self.board_path = board_path

    def render(self, players, output_path: str = OUTPUT_IMAGE_PATH):
        board = Image.open(self.board_path).convert("RGBA")
        draw = ImageDraw.Draw(board)

        # Map: position -> list of (color)
        position_map = {}

        for player in players:
            for token in player.tokens:
                if token.position < 0 or token.finished:
                    continue
                position_map.setdefault(token.position, []).append(player.color)

        for position, colors in position_map.items():
            coord = CELL_COORDS.get(position)
            if not coord:
                continue

            base_x, base_y = coord

            for i, color in enumerate(colors):
                offset = i * STACK_OFFSET
                x = base_x + offset
                y = base_y + offset
                r = TOKEN_RADIUS

                draw.ellipse(
                    (x - r, y - r, x + r, y + r),
                    fill=TOKEN_COLORS[color],
                    outline=(0, 0, 0),
                    width=2
                )

        board.save(output_path)
        return output_path
