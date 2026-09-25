"""Food spawning.

Food appears on one random free grid cell — i.e. a cell the snake does not
currently occupy.
"""

from __future__ import annotations

import random

from .config import GRID_HEIGHT, GRID_WIDTH
from .snake import Snake


def spawn_food(snake: Snake, occupied: set[tuple[int, int]] | None = None) -> tuple[int, int]:
    """Choose a random free cell for the next piece of food.

    ``occupied`` lists extra cells (e.g. a waiting food) that should stay
    free as well.

    Raises:
        ValueError: if every cell of the board is occupied — the player won.
    """
    taken = set(snake.body)
    if occupied:
        taken.update(occupied)
    free_cells = [
        (x, y)
        for x in range(GRID_WIDTH)
        for y in range(GRID_HEIGHT)
        if (x, y) not in taken
    ]
    if not free_cells:
        raise ValueError("the board is completely full")
    return random.choice(free_cells)
