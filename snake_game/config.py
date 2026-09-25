"""Central configuration for the snake game.

Every tunable value of the game (window size, board dimensions, colours,
speeds) lives here so that behaviour can be tweaked without touching the
game logic or the rendering code.
"""

from __future__ import annotations

# --- Window -----------------------------------------------------------------
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 720
FPS = 60
FONT_SIZE = 28

# --- Board ------------------------------------------------------------------
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = (WINDOW_HEIGHT - 40) // GRID_SIZE

# --- Difficulty -----------------------------------------------------------
# Each level pairs the snake's fixed speed (in grid cells per second) with
# the points awarded per food item: faster levels are worth more.
EASY_SPEED, EASY_POINTS = 6, 10
MEDIUM_SPEED, MEDIUM_POINTS = 12, 20
HARD_SPEED, HARD_POINTS = 18, 30

#: Difficulty levels shown on the start screen, slowest to fastest, as
#: ``(label, speed, points per food)``.
DIFFICULTIES = (
    ("Easy", EASY_SPEED, EASY_POINTS),
    ("Medium", MEDIUM_SPEED, MEDIUM_POINTS),
    ("Hard", HARD_SPEED, HARD_POINTS),
)

# --- High scores ------------------------------------------------------------
# How many entries the persistent table keeps.
HIGH_SCORE_LIMIT = 20

# --- Colours (R, G, B) ------------------------------------------------------
BACKGROUND = (24, 26, 34)
GRID = (32, 35, 45)
FOOD = (214, 69, 65)
TEXT = (230, 230, 230)
TEXT_DIM = (140, 140, 150)

# Head colour, then the body fades towards the tail.
SNAKE_HEAD = (76, 175, 80)
SNAKE_BODY_LIGHT = (46, 125, 50)
SNAKE_BODY_DARK = (27, 74, 33)


def cell_to_pixel(cell: int) -> int:
    """Return the pixel offset of the top-left corner of a grid cell."""
    return cell * GRID_SIZE
