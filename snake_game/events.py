"""Input handling: the only module besides ``game_loop`` that reads pygame events.

Key presses are mapped to snake directions so the rest of the code base never
has to reason about which key means what.
"""

from __future__ import annotations

import pygame

from .game import Game
from .snake import Snake

#: Keys that end the application.
QUIT_KEYS = (pygame.K_ESCAPE,)

#: Keys that start a new game on the game-over screen.
RESTART_KEYS = (pygame.K_SPACE, pygame.K_r)

#: Direction keys, mapped to the ``Snake`` direction vectors.
DIRECTION_KEYS = {
    pygame.K_UP: Snake.NORTH,
    pygame.K_w: Snake.NORTH,
    pygame.K_RIGHT: Snake.EAST,
    pygame.K_d: Snake.EAST,
    pygame.K_DOWN: Snake.SOUTH,
    pygame.K_s: Snake.SOUTH,
    pygame.K_LEFT: Snake.WEST,
    pygame.K_a: Snake.WEST,
}


def _letter_of(event: pygame.event.Event) -> str | None:
    """Return the upper-case letter of a letter-key event, if any.

    Uses the ``unicode`` payload, which pygame fills in for letter keys
    without a modifier, so the result works on any keyboard layout.
    """
    char = getattr(event, "unicode", "")
    if char:
        upper = char.upper()
        if upper.isalpha() and len(upper) == 1:
            return upper
    return None


def handle_events(
    running: bool,
    game: Game,
    initials: list[str] | None = None,
) -> tuple[bool, Game, list[str] | None]:
    """Poll one batch of pygame events and apply their effects.

    Args:
        running: whether the application should keep running.
        game: the game to receive direction changes and restarts.
        initials: the letters collected so far while the player is entering
            their initials for the high-score table; ``None`` when no entry
            is in progress.

    Returns:
        A ``(running, game, initials)`` tuple with the updated state. A
        letter key is appended to ``initials`` (up to three letters);
        ``BACKSPACE`` removes the last one; ``ENTER`` confirms the entry.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in QUIT_KEYS:
                running = False
            elif initials is not None and len(initials) < 3:
                letter = _letter_of(event)
                if letter:
                    initials.append(letter)
                elif event.key == pygame.K_BACKSPACE and initials:
                    initials.pop()
            elif event.key in DIRECTION_KEYS:
                game.snake.turn(DIRECTION_KEYS[event.key])
            elif event.key in RESTART_KEYS and game.game_over:
                game.restart()
    return running, game, initials
