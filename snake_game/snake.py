"""The snake itself: position, direction and movement.

The snake is represented as a list of grid cells ordered head-first, so the
head is always ``snake.body[0]``. Moving is done by inserting a new head
cell; the tail cell is dropped unless the snake is growing.
"""

from __future__ import annotations

import random

from .config import GRID_HEIGHT, GRID_WIDTH


class Snake:
    """A snake moving on a square grid."""

    #: The four allowed directions, in clockwise order.
    NORTH = (0, -1)
    EAST = (1, 0)
    SOUTH = (0, 1)
    WEST = (-1, 0)

    #: Exact opposites — a snake may never reverse into itself.
    OPPOSITES = {NORTH: SOUTH, EAST: WEST, SOUTH: NORTH, WEST: EAST}

    def __init__(
        self,
        start_position: tuple[int, int] | None = None,
        start_direction: tuple[int, int] | None = None,
    ) -> None:
        """Create a snake three cells long.

        ``start_position`` is the cell the head begins on; by default the
        snake spawns in one of the board's halves facing away from the
        nearest wall, so it always starts with half a board of runway.
        When a position is given without a direction, the same
        wall-aware rule picks one.
        """
        if start_position is None:
            start_position = self._random_spawn_position()
        if start_direction is None:
            start_direction = self._direction_away_from_wall(start_position[0])
        # The body trails the head: segment ``i`` sits ``i`` cells back,
        # against the direction of travel.
        self.body: list[tuple[int, int]] = [
            (start_position[0] - i * start_direction[0], start_position[1] - i * start_direction[1])
            for i in range(3)
        ]
        self.direction = start_direction

    @staticmethod
    def _random_spawn_position() -> tuple[int, int]:
        """Pick a random spawn cell in one of the board's two halves.

        The x coordinate stays at least two cells from the side walls so
        the initial body always fits on the board; the y coordinate is
        uniform across the board.
        """
        half = GRID_WIDTH // 2
        left_half = random.random() < 0.5
        x = (
            random.randrange(2, half + 1)
            if left_half
            else random.randrange(half, GRID_WIDTH - 2)
        )
        return x, random.randrange(GRID_HEIGHT)

    @staticmethod
    def _direction_away_from_wall(x: int) -> tuple[int, int]:
        """Return the horizontal direction pointing away from the nearest wall.

        A head in the left half faces east (away from the left wall) and a
        head in the right half faces west, guaranteeing at least half of
        the board between the head and the wall ahead.
        """
        return Snake.EAST if x < GRID_WIDTH // 2 else Snake.WEST

    @property
    def head(self) -> tuple[int, int]:
        """The cell the snake's head currently occupies."""
        return self.body[0]

    def turn(self, direction: tuple[int, int]) -> None:
        """Change direction, ignoring 180° reversals.

        Reversing into the cell the neck currently occupies would be an
        instant collision, so the current direction is kept in that case.
        """
        if direction != self.OPPOSITES[self.direction]:
            self.direction = direction

    def collides(self, cell: tuple[int, int], grow: bool = False) -> bool:
        """Return ``True`` if moving the head to ``cell`` would be fatal.

        A move is fatal when the cell lies outside the grid or is occupied
        by the body. When the snake is not growing the tail cell is exempt,
        because it vacates its cell at the same moment the head moves; when
        it is growing the tail stays in place and is checked too.
        """
        x, y = cell
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            return True
        occupied = self.body[1:] if grow else self.body[1:-1]
        return cell in occupied

    def move(self, grow: bool = False) -> tuple[int, int]:
        """Advance one cell in the current direction and return the new head.

        When ``grow`` is false the tail cell is dropped, keeping the length
        constant; otherwise an extra segment is kept for this step.
        """
        new_head = (
            self.head[0] + self.direction[0],
            self.head[1] + self.direction[1],
        )
        self.body.insert(0, new_head)
        if not grow:
            self.body.pop()
        return new_head

    def reset(self) -> None:
        """Move the snake back to a fresh random starting position."""
        self.__init__()
