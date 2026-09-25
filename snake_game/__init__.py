"""Classic snake game built with pygame.

The package is organised into small, focused modules:

- ``config``: constants that define the game's size, speed and palette.
- ``food``: food spawning.
- ``game``: the simulation itself (movement, collisions, scoring).
- ``renderer``: everything drawn to the screen.
- ``events``: keyboard input handling.
- ``game_loop``: the top-level application, wiring all the pieces together.
"""

from .config import FPS, GRID_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH
from .game import Game

__all__ = ["FPS", "GRID_SIZE", "WINDOW_HEIGHT", "WINDOW_WIDTH", "Game"]
