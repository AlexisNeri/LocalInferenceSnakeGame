"""Smoke tests for the snake game.

They run the real game loop with SDL's dummy video driver, so no window is
opened. Run them with ``python test_snake_game.py``.
"""

import json
import os
import tempfile
import threading
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from snake_game import config, events  # noqa: E402
from snake_game.game import Game  # noqa: E402
from snake_game.game_loop import main  # noqa: E402
from snake_game.highscores import (  # noqa: E402
    ScoreEntry,
    add_score,
    best,
    load_scores,
    qualifies,
    save_scores,
)
from snake_game.menu import Menu  # noqa: E402
from snake_game.renderer import (  # noqa: E402
    SnakeView,
    draw_food,
    draw_game_over,
    draw_grid,
    draw_high_scores,
    draw_menu,
    draw_score,
)
from snake_game.snake import Snake  # noqa: E402


def test_initial_state() -> None:
    game = Game()
    assert game.score == 0
    assert not game.game_over
    assert len(game.snake.body) == 3
    assert game.food not in game.snake.body


def test_cannot_reverse() -> None:
    snake = Snake(start_position=(10, 10), start_direction=Snake.EAST)
    snake.turn(Snake.WEST)
    assert snake.direction == Snake.EAST
    snake.turn(Snake.NORTH)
    assert snake.direction == Snake.NORTH


def test_direction_away_from_wall() -> None:
    # Left half faces east, right half faces west.
    assert Snake._direction_away_from_wall(0) == Snake.EAST
    assert Snake._direction_away_from_wall(config.GRID_WIDTH // 2 - 1) == Snake.EAST
    assert Snake._direction_away_from_wall(config.GRID_WIDTH // 2) == Snake.WEST
    assert Snake._direction_away_from_wall(config.GRID_WIDTH - 1) == Snake.WEST


def test_spawn_always_faces_away_from_nearest_wall() -> None:
    for _ in range(500):
        snake = Snake()
        head, direction = snake.head, snake.direction
        # The spawn sits in the correct half...
        if direction == Snake.EAST:
            assert 2 <= head[0] < config.GRID_WIDTH // 2
        else:
            assert config.GRID_WIDTH // 2 <= head[0] < config.GRID_WIDTH - 2
        # ...and always has at least half the board of runway before the wall.
        wall_run = (
            config.GRID_WIDTH - 1 - head[0]
            if direction == Snake.EAST
            else head[0]
        )
        assert wall_run >= config.GRID_WIDTH // 2 - 2
        # The body must stay on the board.
        for cell in snake.body:
            assert 0 <= cell[0] < config.GRID_WIDTH
            assert 0 <= cell[1] < config.GRID_HEIGHT


def test_explicit_start_direction_still_respected() -> None:
    snake = Snake(start_position=(5, 5), start_direction=Snake.NORTH)
    assert snake.direction == Snake.NORTH
    assert snake.body[0] == (5, 5)
    assert snake.body[1] == (5, 6)


def test_move_keeps_length_unless_growing() -> None:
    snake = Snake(start_position=(10, 10), start_direction=Snake.EAST)
    head = snake.move()
    assert head == (11, 10)
    assert len(snake.body) == 3
    head = snake.move(grow=True)
    assert head == (12, 10)
    assert len(snake.body) == 4


def test_wall_collision() -> None:
    snake = Snake(start_position=(config.GRID_WIDTH - 1, 10), start_direction=Snake.EAST)
    assert not snake.collides(snake.head)
    assert snake.collides((config.GRID_WIDTH, 10))
    assert snake.collides((-1, 10))
    assert snake.collides((5, -1))
    assert snake.collides((5, config.GRID_HEIGHT))


def test_self_collision() -> None:
    snake = Snake(start_position=(5, 5), start_direction=Snake.EAST)
    # A valid four-cell snake coiled in a 2×2 box: head (5,5), neck (5,6),
    # then (6,6) and tail (6,5).
    snake.body = [(5, 5), (5, 6), (6, 6), (6, 5)]
    # Facing the neck is always fatal.
    assert snake.collides((5, 6), grow=False)
    # The tail cell is safe when the snake does not grow (it moves away in
    # the same tick), but fatal when it does.
    assert not snake.collides((6, 5), grow=False)
    assert snake.collides((6, 5), grow=True)


def test_difficulty_speeds() -> None:
    """Each level has a fixed speed and points, easy the lowest and hard the highest."""
    speeds = {name: speed for name, speed, _ in config.DIFFICULTIES}
    points = {name: pts for name, _, pts in config.DIFFICULTIES}
    assert len(config.DIFFICULTIES) == 3
    assert speeds["Easy"] < speeds["Medium"] < speeds["Hard"]
    assert points == {"Easy": 10, "Medium": 20, "Hard": 30}
    # The speed is constant for the whole run: eating never changes it.
    game = Game("Easy")
    before = game.speed
    game.score = 10_000
    assert game.speed == before


def test_points_per_food_by_difficulty() -> None:
    """Eating awards points according to the selected difficulty."""
    for name, _, pts in config.DIFFICULTIES:
        game = Game(name)
        # Put the food one cell in front of the head: next tick is an "ate".
        game.food = (
            game.snake.head[0] + game.snake.direction[0],
            game.snake.head[1] + game.snake.direction[1],
        )
        assert game.tick() == "ate"
        assert game.score == pts


def test_full_game_and_restart() -> None:
    game = Game()
    # Put the food one cell in front of the head: the next tick must be a
    # guaranteed, deterministic "ate".
    game.food = (
        game.snake.head[0] + game.snake.direction[0],
        game.snake.head[1] + game.snake.direction[1],
    )
    assert game.tick() == "ate"
    assert game.score == 10
    assert len(game.snake.body) == 4
    assert game.food != game.snake.head
    game.restart()
    assert game.score == 0
    assert not game.game_over
    assert len(game.snake.body) == 3
    assert game.food not in game.snake.body


def test_highscores_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scores.json"
        table = add_score(120, "abc", [])
        assert table == [{"initials": "ABC", "score": 120}]
        save_scores(table, path)
        loaded = load_scores(path)
        assert loaded == table
        assert json.loads(path.read_text(encoding="utf-8")) == table


def test_highscores_order_and_truncation() -> None:
    table: list[ScoreEntry] = []
    for score in (10, 90, 50):
        table = add_score(score, "XYZ", table)
    assert [entry["score"] for entry in table] == [90, 50, 10]
    table = add_score(100, "ZZZ", table)
    assert [entry["score"] for entry in table] == [100, 90, 50, 10]
    # Filling the table past the limit keeps only the best entries.
    for i in range(config.HIGH_SCORE_LIMIT):
        table = add_score(10_000 + i, "AAA", table)
    assert len(table) == config.HIGH_SCORE_LIMIT
    assert table[0]["score"] == 10_019
    assert table[-1]["score"] == 10_000
    assert best(table) == table[0]


def test_highscores_load_rejects_bad_entries() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scores.json"
        bad_entries = [
            {"initials": "AB", "score": 5},        # too short
            {"initials": "ABCD", "score": 5},      # too long
            {"initials": "123", "score": 5},       # not letters
            {"initials": "ABC", "score": "five"},  # not an int
            {"initials": "ABC", "score": True},    # bool is not a score
            {"initials": "ABC", "score": -1},      # negative
            "just a string",                        # not even a dict
            {"initials": "abc", "score": 40},      # valid
        ]
        path.write_text(json.dumps(bad_entries), encoding="utf-8")
        assert load_scores(path) == [{"initials": "ABC", "score": 40}]
        # Missing file and malformed JSON both give an empty table.
        assert load_scores(Path(tmp) / "missing.json") == []
        path.write_text("not json {", encoding="utf-8")
        assert load_scores(path) == []


def test_highscores_qualifies() -> None:
    assert qualifies(0, [])
    assert qualifies(0, [ScoreEntry(initials="ABC", score=0)])
    table = [ScoreEntry(initials="AAA", score=s) for s in range(1, config.HIGH_SCORE_LIMIT + 1)]
    assert not qualifies(1, table)
    assert not qualifies(0, table)
    assert qualifies(2, table)
    assert qualifies(100, table)


def test_events_restart_on_game_over() -> None:
    pygame.init()
    game = Game()
    game.game_over = True
    pygame.event.clear()
    pygame.event.post(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" ", mod=0, scancode=32)
    )
    running, returned_game, initials = events.handle_events(True, game)
    assert running is True
    assert returned_game is game
    assert initials is None
    assert not game.game_over
    assert len(game.snake.body) == 3


def test_menu_selection() -> None:
    pygame.init()
    menu = Menu()
    assert menu.options == ("Easy", "Medium", "Hard")
    assert menu.selected == 0

    # Down moves the selection, wrapping around at the end.
    pygame.event.clear()
    _post_key(pygame.K_DOWN, "")
    running, choice = menu.handle_events(True)
    assert running is True and choice is None
    assert menu.selected == 1
    _post_key(pygame.K_DOWN, "")
    menu.handle_events(True)
    assert menu.selected == 2
    _post_key(pygame.K_DOWN, "")
    menu.handle_events(True)
    assert menu.selected == 0  # wrapped around

    # Up moves the selection the other way, also wrapping.
    _post_key(pygame.K_UP, "")
    menu.handle_events(True)
    assert menu.selected == 2

    # ENTER confirms the selected option.
    _post_key(pygame.K_RETURN, "")
    running, choice = menu.handle_events(True)
    assert running is True
    assert choice == "Hard"

    # ESC quits without a choice.
    pygame.event.clear()
    _post_key(pygame.K_ESCAPE, "")
    running, choice = menu.handle_events(True)
    assert running is False
    assert choice is None


def _post_key(key: int, letter: str) -> None:
    """Post a KEYDOWN event for the given key and unicode payload."""
    pygame.event.post(
        pygame.event.Event(pygame.KEYDOWN, key=key, unicode=letter, mod=0, scancode=0)
    )


def test_events_collect_initials() -> None:
    pygame.init()
    game = Game()
    game.game_over = True
    pygame.event.clear()
    _post_key(pygame.K_a, "a")
    _post_key(pygame.K_b, "b")
    _, _, initials = events.handle_events(True, game, [])
    assert initials == ["A", "B"]
    _post_key(pygame.K_c, "c")
    _, _, initials = events.handle_events(True, game, ["A", "B"])
    assert initials == ["A", "B", "C"]
    # No more letters are accepted once three are in.
    _post_key(pygame.K_d, "d")
    _, _, initials = events.handle_events(True, game, ["A", "B", "C"])
    assert initials == ["A", "B", "C"]
    # Backspace removes the last letter (only while fewer than three are in:
    # in the real loop the third letter is committed on the very next frame).
    pygame.event.clear()
    _post_key(pygame.K_BACKSPACE, "")
    _, _, initials = events.handle_events(True, game, ["A", "B"])
    assert initials == ["A"]
    # Letters keep being collected until the third one completes the entry.
    pygame.event.clear()
    _post_key(pygame.K_x, "x")
    running, returned_game, initials = events.handle_events(True, game, ["A", "B"])
    assert running is True
    assert returned_game is game
    assert initials == ["A", "B", "X"]


def test_snake_view_interpolation() -> None:
    view = SnakeView([(10, 10), (9, 10), (8, 10)])
    # After a step the head is halfway between old and new cells.
    view.update([(11, 10), (10, 10), (9, 10)])
    view.draw(pygame.Surface((100, 100)), 0.5)  # smoke: must not raise
    # With a 3-cell body, the tail segment keeps its old cell while growing.
    view.reset([(10, 10), (9, 10), (8, 10)])
    view.update([(11, 10), (10, 10), (9, 10), (8, 10)])
    view.draw(pygame.Surface((100, 100)), 1.0)


def test_rendering_smoke() -> None:
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    font = pygame.font.Font(None, config.FONT_SIZE)
    game = Game()
    snake_view = SnakeView(game.snake.body)
    draw_grid(screen)
    draw_food(screen, game.food)
    snake_view.draw(screen, 0.5)
    draw_score(screen, game.score, 42, font)
    draw_menu(screen, 0, font)
    draw_game_over(screen, font)
    draw_game_over(screen, font, is_high_score=True)
    draw_high_scores(screen, [], font)
    draw_high_scores(screen, [{"initials": "ABC", "score": 100}], font)
    pygame.display.flip()


def test_main_smoke() -> None:
    pygame.init()
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    main()  # the posted QUIT event ends the loop immediately


def test_main_highscore_flow() -> None:
    """Run the real main loop: die, type initials, watch them get persisted."""
    import snake_game.game_loop as game_loop

    pygame.init()
    with tempfile.TemporaryDirectory() as tmp:
        saved: list[list[dict]] = []

        original = (game_loop.load_scores, game_loop.save_scores, game_loop.Game)
        game_loop.load_scores = lambda: []

        def fake_save(table, _default=None):
            saved.append([dict(entry) for entry in table])

        game_loop.save_scores = fake_save

        class DeadGame(Game):
            """A game that records 50 points and dies on its first tick."""

            def tick(self):
                self.score = 50
                self.game_over = True
                return "died"

        game_loop.Game = DeadGame

        def play_and_quit() -> None:
            # Confirm the menu first, then wait for the snake to die (the
            # stub dies on its first tick, ~0.2 s after play starts) so the
            # initials screen is open before the letters are posted.
            time.sleep(0.3)
            pygame.event.post(
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0, scancode=0)
            )
            time.sleep(0.8)
            for letter, key in (("a", pygame.K_a), ("b", pygame.K_b), ("c", pygame.K_c)):
                pygame.event.post(
                    pygame.event.Event(pygame.KEYDOWN, key=key, unicode=letter, mod=0, scancode=0)
                )
            time.sleep(1.0)
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        pygame.event.clear()
        threading.Thread(target=play_and_quit, daemon=True).start()
        game_loop.main()
        game_loop.load_scores, game_loop.save_scores, game_loop.Game = original

        assert saved, "the high score was never saved"
        assert saved[-1] == [{"initials": "ABC", "score": 50}]


if __name__ == "__main__":
    test_full_game_and_restart()
    test_initial_state()
    test_cannot_reverse()
    test_direction_away_from_wall()
    test_spawn_always_faces_away_from_nearest_wall()
    test_explicit_start_direction_still_respected()
    test_move_keeps_length_unless_growing()
    test_wall_collision()
    test_self_collision()
    test_difficulty_speeds()
    test_points_per_food_by_difficulty()
    test_menu_selection()
    test_highscores_roundtrip()
    test_highscores_order_and_truncation()
    test_highscores_load_rejects_bad_entries()
    test_highscores_qualifies()
    test_events_restart_on_game_over()
    test_events_collect_initials()
    test_rendering_smoke()
    test_snake_view_interpolation()
    test_main_smoke()
    test_main_highscore_flow()
    print("All smoke tests passed.")
