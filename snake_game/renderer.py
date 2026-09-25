"""All drawing for the snake game.

This module is the only place that knows about pygame surfaces: it blits the
board, the snake, the food and the score onto the screen.
"""

from __future__ import annotations

from collections.abc import Sequence

import pygame

from .config import (
    DIFFICULTIES,
    FOOD,
    GRID,
    GRID_HEIGHT,
    GRID_SIZE,
    GRID_WIDTH,
    HIGH_SCORE_LIMIT,
    SNAKE_BODY_DARK,
    SNAKE_BODY_LIGHT,
    SNAKE_HEAD,
    TEXT,
    TEXT_DIM,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    cell_to_pixel,
)
from .highscores import ScoreEntry

BOARD_TOP = 40
FONT_SIZE = 28
PADDING = 6


def _lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """Blend two RGB colours, ``t=0`` gives ``a`` and ``t=1`` gives ``b``."""
    return tuple(int(ch_a + (ch_b - ch_a) * t) for ch_a, ch_b in zip(a, b))  # type: ignore[return-value]


def draw_score(screen: pygame.Surface, score: int, best: int, font: pygame.font.Font) -> None:
    """Render the current score and the top score in the bar above the board."""
    label = font.render(f"Score: {score}", True, TEXT)
    screen.blit(label, (12, (BOARD_TOP - label.get_height()) // 2))
    best_label = font.render(f"Best: {best}", True, TEXT_DIM)
    screen.blit(
        best_label,
        (WINDOW_WIDTH - best_label.get_width() - 12, (BOARD_TOP - best_label.get_height()) // 2),
    )


def draw_grid(screen: pygame.Surface) -> None:
    """Draw a faint grid of one-cell squares across the whole board."""
    for x in range(GRID_WIDTH + 1):
        pygame.draw.line(screen, GRID, (cell_to_pixel(x), BOARD_TOP), (cell_to_pixel(x), BOARD_TOP + GRID_HEIGHT * GRID_SIZE))
    for y in range(GRID_HEIGHT + 1):
        pygame.draw.line(screen, GRID, (0, BOARD_TOP + cell_to_pixel(y)), (WINDOW_WIDTH, BOARD_TOP + cell_to_pixel(y)))


class SnakeView:
    """Smooth renderer for the snake.

    The simulation moves the snake in discrete cells, but the renderer
    interpolates between the last two positions so the snake glides from
    cell to cell. Because the on-screen position is derived from the
    simulation time rather than from the display refresh rate, a frame
    that takes longer than one simulation step (a hiccup) can never make
    the snake jump forward.
    """

    def __init__(self, body: Sequence[tuple[int, int]]) -> None:
        """Create a view that starts rendering ``body" with no motion in flight."""
        self.reset(body)

    def reset(self, body: Sequence[tuple[int, int]]) -> None:
        """Start rendering from ``body`` with no interpolation in flight.

        Used after a restart, when the body is replaced wholesale and the
        previous positions no longer make sense.
        """
        self._body: list[tuple[int, int]] = list(body)
        self._old: list[tuple[int, int]] = list(body)

    def update(self, body: Sequence[tuple[int, int]]) -> None:
        """Record the positions before a step so they can be interpolated.

        Each segment keeps the cell it occupied before the step; while the
        snake is growing, the extra tail segment starts from the old tail
        cell, so it stays still while the head advances.
        """
        self._old = list(self._body)
        while len(self._old) < len(body):
            self._old.append(self._old[-1])
        self._body = list(body)

    def draw(self, screen: pygame.Surface, alpha: float) -> None:
        """Draw the snake with each segment ``alpha`` of the way to its new cell.

        ``alpha`` is the fraction of the current simulation step that has
        elapsed; values outside 0-1 are clamped so the view never
        extrapolates (e.g. when the snake has just died and the loop stops
        stepping). The body colour fades from bright at the head to dark
        at the tail so the direction of travel reads at a glance.
        """
        alpha = max(0.0, min(1.0, alpha))
        length = max(len(self._body) - 1, 1)
        for index in range(len(self._body)):
            new_x, new_y = self._body[index]
            old_x, old_y = self._old[index]
            px = (old_x + (new_x - old_x) * alpha) * GRID_SIZE + PADDING // 2
            py = BOARD_TOP + (old_y + (new_y - old_y) * alpha) * GRID_SIZE + PADDING // 2
            colour = SNAKE_HEAD if index == 0 else _lerp_color(SNAKE_BODY_LIGHT, SNAKE_BODY_DARK, index / length)
            rect = pygame.Rect(px, py, GRID_SIZE - PADDING, GRID_SIZE - PADDING)
            pygame.draw.rect(screen, colour, rect, border_radius=PADDING // 2)


def draw_food(screen: pygame.Surface, cell: tuple[int, int]) -> None:
    """Draw the food as a small filled circle centred on its cell."""
    centre = (
        cell_to_pixel(cell[0]) + GRID_SIZE // 2,
        BOARD_TOP + cell_to_pixel(cell[1]) + GRID_SIZE // 2,
    )
    pygame.draw.circle(screen, FOOD, centre, GRID_SIZE // 2 - PADDING)


def draw_game_over(
    screen: pygame.Surface,
    font: pygame.font.Font,
    is_high_score: bool = False,
) -> None:
    """Paint a semi-transparent overlay with a game-over message.

    When ``is_high_score`` is true, a celebratory line is shown above the
    title to tell the player they set a new record.
    """
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    title = font.render("Game Over", True, TEXT)
    hint = pygame.font.Font(None, FONT_SIZE - 8).render("Press SPACE or R to restart", True, TEXT_DIM)

    if is_high_score:
        new_record = font.render("New High Score!", True, SNAKE_HEAD)
        overlay.blit(new_record, new_record.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 56)))
    overlay.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))
    overlay.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 24)))
    screen.blit(overlay, (0, 0))


def draw_menu(
    screen: pygame.Surface,
    selected: int,
    font: pygame.font.Font,
) -> None:
    """Draw the start screen with the difficulty selector.

    The three options from :data:`config.DIFFICULTIES` are listed vertically
    in the centre of the board; the one at index ``selected`` is highlighted
    with a marker and the brightest colour.
    """
    title = pygame.font.Font(None, FONT_SIZE + 12).render("Snake", True, TEXT)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, BOARD_TOP + 48)))

    subtitle = pygame.font.Font(None, FONT_SIZE - 8).render("Choose a difficulty", True, TEXT_DIM)
    screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, BOARD_TOP + 92)))

    option_font = pygame.font.Font(None, FONT_SIZE + 4)
    line_height = FONT_SIZE + 12
    top = BOARD_TOP + 150
    for index, (label, speed, points) in enumerate(DIFFICULTIES):
        is_selected = index == selected
        colour = TEXT if is_selected else TEXT_DIM
        marker = "> " if is_selected else "  "
        line = option_font.render(
            f"{marker}{label}   ({speed} cells/s, {points} pts/food)", True, colour
        )
        screen.blit(line, line.get_rect(center=(WINDOW_WIDTH // 2, top + index * line_height)))

    hint = pygame.font.Font(None, FONT_SIZE - 8).render("Use the arrows or W/S, then press ENTER", True, TEXT_DIM)
    screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, top + len(DIFFICULTIES) * line_height + 12)))


def draw_high_scores(
    screen: pygame.Surface,
    entries: list[ScoreEntry],
    font: pygame.font.Font,
    top: int = BOARD_TOP + 40,
) -> None:
    """Draw the high-score table centred on the screen.

    ``entries`` is the persistent table, already sorted from highest to
    lowest. Up to twenty entries are shown in two columns (ranks 1-10 and
    11-20); an empty table shows a placeholder line instead. ``top`` is the
    pixel offset of the title line, so the table can be pushed down to
    make room for other text above it.
    """
    title = font.render("High Scores", True, TEXT)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, top)))

    line_font = pygame.font.Font(None, FONT_SIZE - 4)
    if not entries:
        placeholder = line_font.render("No scores yet — be the first!", True, TEXT_DIM)
        screen.blit(placeholder, placeholder.get_rect(center=(WINDOW_WIDTH // 2, top + 80)))
        return

    line_height = FONT_SIZE + 4
    first_row = top + 40
    column_gap = 220
    for index, entry in enumerate(entries[:HIGH_SCORE_LIMIT]):
        rank = index + 1
        column_x = WINDOW_WIDTH // 2 - column_gap // 2 if index < 10 else WINDOW_WIDTH // 2 + column_gap // 2
        row = index % 10
        line = line_font.render(f"{rank:>2}.  {entry['initials']}   {entry['score']:<6}", True, TEXT)
        screen.blit(line, (column_x - line.get_width() // 2, first_row + row * line_height))
