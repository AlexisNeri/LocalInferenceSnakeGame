"""The core game simulation.

``Game`` owns the snake, the food, the score and the game-over state. It is
deliberately screen-agnostic: all rendering lives in :mod:`snake_game.renderer`
and all input in :mod:`snake_game.events`.
"""

from __future__ import annotations

from .config import DIFFICULTIES
from .food import spawn_food
from .snake import Snake


class Game:
    """A single run of the snake game.

    The snake moves at a fixed speed (in grid cells per second) and each
    piece of food is worth a fixed number of points; both are determined
    by the difficulty level chosen on the start screen.
    Advance the simulation with :meth:`tick`; it returns an event string the
    game loop can react to: ``"ate"`` when food was eaten and ``"died"`` when
    the snake crashed. Any other tick returns ``None``.
    """

    def __init__(self, difficulty: str = "Easy") -> None:
        """Start a fresh game at the given difficulty.

        ``difficulty`` is one of the labels in :data:`config.DIFFICULTIES`
        (``"Easy"``, ``"Medium"`` or ``"Hard"``); an unknown label falls
        back to easy.
        """
        speeds = {label: speed for label, speed, _ in DIFFICULTIES}
        points = {label: pts for label, _, pts in DIFFICULTIES}
        self.speed = speeds.get(difficulty, speeds["Easy"])
        self.points_per_food = points.get(difficulty, points["Easy"])
        self.snake = Snake()
        self.food: tuple[int, int] = spawn_food(self.snake)
        self.score = 0
        self.game_over = False

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def tick(self) -> str | None:
        """Move the snake one cell and update the game state.

        Returns:
            ``"ate"`` if the new head landed on the food, ``"died"`` if it
            hit a wall or the snake's own body, otherwise ``None``.
        """
        if self.game_over:
            return None
        new_head = (
            self.snake.head[0] + self.snake.direction[0],
            self.snake.head[1] + self.snake.direction[1],
        )
        if self.snake.collides(new_head, grow=new_head == self.food):
            self.game_over = True
            return "died"
        self.snake.move(grow=new_head == self.food)
        if new_head == self.food:
            self.score += self.points_per_food
            self.food = spawn_food(self.snake)
            return "ate"
        return None

    def restart(self) -> None:
        """Reset the run state but keep the chosen difficulty."""
        self.snake = Snake()
        self.food = spawn_food(self.snake)
        self.score = 0
        self.game_over = False

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Game(score={self.score}, speed={self.speed}, game_over={self.game_over})"
