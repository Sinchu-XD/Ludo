# renderer/board.py
from PIL import Image, ImageDraw

# 🔹 Board base image path
BOARD_IMAGE_PATH = "assets/board.png"

# 🔹 Token colors (RGB)
TOKEN_COLORS = {
    "red": (220, 20, 60),
    "green": (0, 180, 0),
    "yellow": (255, 215, 0),
    "blue": (30, 144, 255),
}

# 🔹 Token size
TOKEN_RADIUS = 10

# 🔹 Cell → (x, y) mapping
# NOTE: Ye example mapping hai.
# Tum apne board.png ke hisaab se coordinates adjust karoge.
CELL_COORDS = {
    # Main path (0–51)
    0: (300, 40),
    1: (340, 40),
    2: (380, 40),
    3: (420, 40),
    4: (460, 40),
    5: (500, 40),
    # ...
    # 6–51 complete karna hoga (same pattern)
    
    # Home path (52–57)
    52: (300, 80),
    53: (300, 120),
    54: (300, 160),
    55: (300, 200),
    56: (300, 240),
    57: (300, 280),
}

class BoardRenderer:
    def __init__(self, board_path: str = BOARD_IMAGE_PATH):
        self.board_path = board_path

    def render(self, players, output_path="board_render.png"):
        """
        players: List[Player]
        output_path: where rendered image will be saved
        """
        board = Image.open(self.board_path).convert("RGBA")
        draw = ImageDraw.Draw(board)

        for player in players:
            color = TOKEN_COLORS.get(player.color, (0, 0, 0))

            for token in player.tokens:
                if token.position < 0:
                    continue  # token still at home

                coord = CELL_COORDS.get(token.position)
                if not coord:
                    continue

                x, y = coord
                r = TOKEN_RADIUS

                draw.ellipse(
                    (x - r, y - r, x + r, y + r),
                    fill=color,
                    outline=(0, 0, 0),
                    width=2
                )

        board.save(output_path)
        return output_path
      
