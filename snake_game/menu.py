"""The start-screen (difficulty selector) state.

The menu is a tiny state machine: it tracks which option is selected and
answers to key events, returning the chosen difficulty label once the
player confirms with ENTER.
"""

from __future__ import annotations

import pygame

from .config import DIFFICULTIES


class Menu:
    """A three-option difficulty selector.

    Options are the labels of :data:`config.DIFFICULTIES` (``"Easy"``,
    ``"Medium"``, ``"Hard"``); the selection starts on the first one.
    """

    def __init__(self) -> None:
        """Create a menu with the first option pre-selected."""
        self.options: tuple[str, ...] = tuple(label for label, _, _ in DIFFICULTIES)
        self.selected = 0

    # ------------------------------------------------------------------ #
    # input
    # ------------------------------------------------------------------ #
    def handle_events(self, running: bool) -> tuple[bool, str | None]:
        """Poll one batch of pygame events and update the selection.

        Up/down arrows (or W/S) move the selection, and ENTER or SPACE
        confirms it.

        Args:
            running: whether the application should keep running.

        Returns:
            A ``(running, choice)`` tuple where ``choice`` is the selected
            difficulty label if the player confirmed, else ``None``.
        """
        choice: str | None = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    choice = self.options[self.selected]
        return running, choice
