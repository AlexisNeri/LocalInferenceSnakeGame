"""The top-level application: window, clock and the main loop.

The application starts on a difficulty-selector screen (easy, medium,
hard); each level sets the snake's fixed speed for the whole session.
Everything screen- and timing-related lives here; the simulation in
:mod:`snake_game.game` is advanced on a fixed time base so the game speed is
independent of the display refresh rate.
"""

from __future__ import annotations

import pygame

from .config import (
    BACKGROUND,
    FONT_SIZE,
    FPS,
    TEXT,
    TEXT_DIM,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .events import handle_events
from .game import Game
from .highscores import (
    ScoreEntry,
    add_score,
    best,
    load_scores,
    qualifies,
    save_scores,
)
from .menu import Menu
from .renderer import (
    BOARD_TOP,
    SnakeView,
    draw_food,
    draw_game_over,
    draw_grid,
    draw_high_scores,
    draw_menu,
    draw_score,
)

#: A frame that takes longer than this is a hiccup (sleep, focus loss, a
#: stalled window manager). Its delta is clamped to this value, so a single
#: slow frame can make the snake advance by at most a couple of cells
#: instead of jumping across the board (at the cost of the snake "losing"
#: the hiccup's time, which reads as a brief, gentle pause).
MAX_FRAME_SECONDS = 0.1


def main() -> None:
    """Create the window and run the game until it is quit."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Snake")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)

    scores = load_scores()

    # --- Start screen: choose the difficulty -------------------------------
    difficulty = run_menu(screen, font, clock)
    if difficulty is None:
        pygame.quit()
        return

    # --- Play ----------------------------------------------------------------
    game = Game(difficulty)
    snake_view = SnakeView(game.snake.body)
    move_timer = 0.0
    running = True
    # High-score-entry state. ``run_ended`` mirrors the game-over flag from
    # the previous frame so a restart can be detected; ``initials`` collects
    # the three typed letters; ``pending_score`` is the score being entered;
    # ``high_score_set`` remembers that this run's record was saved so it is
    # not offered again after a restart.
    run_ended = False
    initials: list[str] | None = None
    pending_score: int | None = None
    high_score_set = False

    while running:
        delta = clock.tick(FPS) / 1000.0
        running, game, initials = handle_events(running, game, initials)
        if not running:
            break

        # Detect a restart (game-over -> running) and reset the entry state.
        if run_ended and not game.game_over:
            initials = None
            pending_score = None
            high_score_set = False
            snake_view.reset(game.snake.body)
        run_ended = game.game_over

        # A completed entry is committed to the table and persisted.
        if initials is not None and len(initials) >= 3 and pending_score is not None:
            scores = add_score(pending_score, "".join(initials[:3]), scores)
            save_scores(scores)
            pending_score = None
            initials = None
            high_score_set = True

        # If this run set a record and it has not been entered yet, open
        # the initials screen exactly once.
        if (
            game.game_over
            and initials is None
            and pending_score is None
            and not high_score_set
            and qualifies(game.score, scores)
        ):
            pending_score = game.score
            initials = []

        # Advance the simulation on a fixed time base so the snake speed is
        # in cells/second rather than cells/frame. A hiccup frame (e.g. the
        # window was covered or the system slept) is clamped to
        # MAX_FRAME_SECONDS, so a single slow frame can make the snake
        # advance by at most a couple of cells instead of jumping across
        # the board (the hiccup's time is simply "lost" and reads as a
        # brief, gentle pause).
        #
        # ``snake_view.update`` runs *after* each tick, so it captures the
        # pre-move positions: the renderer then interpolates from those to
        # the new body for this frame, and the snake never renders more
        # than one cell ahead of where the simulation actually is.
        move_timer += min(delta, MAX_FRAME_SECONDS)
        step_time = 1.0 / game.speed
        while move_timer >= step_time and not game.game_over:
            move_timer -= step_time
            game.tick()
            snake_view.update(game.snake.body)

        screen.fill(BACKGROUND)
        if initials is not None:
            draw_initials_prompt(screen, initials, scores, font)
        else:
            draw_grid(screen)
            draw_food(screen, game.food)
            # Once the snake has died, snap the view to its final position
            # so the head is drawn exactly on the wall that ended the run.
            alpha = 1.0 if game.game_over else move_timer / step_time
            snake_view.draw(screen, alpha)
            draw_score(screen, game.score, _best_score(scores), font)
            if game.game_over:
                draw_game_over(screen, font, is_high_score=high_score_set)
        pygame.display.flip()

    pygame.quit()


def run_menu(
    screen: pygame.Surface,
    font: pygame.font.Font,
    clock: pygame.time.Clock,
) -> str | None:
    """Run the difficulty-selector screen until a level is chosen.

    Args:
        screen: the window surface to draw the menu on.
        font: the base font used for the menu text.
        clock: the frame clock, used to keep the screen at a steady rate.

    Returns:
        The chosen difficulty label (``"Easy"``, ``"Medium"`` or ``"Hard"``),
        or ``None`` if the player quit before choosing.
    """
    menu = Menu()
    running = True
    while running:
        clock.tick(FPS)
        running, choice = menu.handle_events(running)
        if not running:
            return None
        if choice is not None:
            return choice
        screen.fill(BACKGROUND)
        draw_grid(screen)
        draw_menu(screen, menu.selected, font)
        pygame.display.flip()
    return None


def _best_score(scores: list[ScoreEntry]) -> int:
    """Return the top score of the table, or zero when it is empty."""
    entry = best(scores)
    return entry["score"] if entry else 0


def draw_initials_prompt(
    screen: pygame.Surface,
    initials: list[str],
    scores: list[ScoreEntry],
    font: pygame.font.Font,
) -> None:
    """Draw the initials-entry screen while the player types three letters.

    The table is shown below the prompt so the player can see where the new
    score is about to land; it is pushed down with ``top`` so the "High
    Scores" title never overlaps the "New High Score!" heading.
    """
    title = font.render("New High Score!", True, TEXT)
    prompt = pygame.font.Font(None, FONT_SIZE - 4).render(
        "Enter your initials:", True, TEXT_DIM
    )
    # Show the three slots, filling in the letters typed so far.
    slots = " ".join(
        letter if index < len(initials) else "_" for index, letter in enumerate(initials)
    )
    slots_line = font.render(f"[ {slots} ]", True, TEXT)

    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, BOARD_TOP + 60)))
    screen.blit(prompt, prompt.get_rect(center=(WINDOW_WIDTH // 2, BOARD_TOP + 96)))
    screen.blit(slots_line, slots_line.get_rect(center=(WINDOW_WIDTH // 2, BOARD_TOP + 132)))

    draw_high_scores(screen, scores, font, top=BOARD_TOP + 176)
