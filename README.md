# Snake

A classic snake game clone built with [pygame](https://www.pygame.org/).

This project is a **proof of concept (POC)** demonstrating the capabilities
of local inference tools. It was developed with the following local
stack:

1. [Zed Code Editor](https://zed.dev/) and its built-in Zed Agent
2. [Ollama](https://ollama.com/), a runtime for running models locally
3. [Qwen 3.8 27B](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF) (Unsloth
   UD-IQ4_XS quantization)

## Features

- Fixed-timestep simulation: snake speed is in *cells per second*, independent
  of the display refresh rate.
- **Difficulty selector on the start screen**: Easy (6 cells/s, 10 pts/food),
  Medium (12 cells/s, 20 pts/food) and Hard (18 cells/s, 30 pts/food); each
  level uses a fixed speed and point value for the whole session, with Easy
  the slowest/lowest and Hard the fastest/highest.
- The snake glides smoothly between cells, so a slow frame can never make
  it jump forward.
- Arrow keys or WASD to steer; 180° reversals are ignored automatically.
- **Persistent high scores**: the top 20 scores with a three-letter initial
  are kept in `snake_game/scores.json`, ordered from highest to lowest.
  After a record-breaking run the game pauses and asks for your initials.
- Score display, game-over overlay and instant restart (`SPACE` or `R`).
- Clean module layout so the simulation can be tested without opening a
  window.

## Project layout

```
snake/
├── main.py                  # entry point
├── requirements.txt
├── test_snake_game.py       # smoke tests (no display required)
└── snake_game/
    ├── __init__.py
    ├── config.py            # all tunables: size, grid, speeds, colours
    ├── snake.py             # Snake: body, direction, movement, collisions
    ├── food.py              # random food spawning on free cells
    ├── game.py              # Game: state, scoring, tick(), restart()
    ├── menu.py              # start-screen difficulty selector state
    ├── highscores.py        # persistent top-20 table (JSON-backed)
    ├── renderer.py          # all pygame drawing (board, snake, HUD, tables)
    ├── events.py            # pygame event handling (keys, quit, initials)
    └── game_loop.py         # window, clock, menu phase and the main loop
```

The high-score table is stored in `snake_game/scores.json`, created on the
first qualifying run. Malformed files are ignored (the game falls back to an
empty table) so a corrupted file can never prevent the game from starting.

## How to run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key                    | Action                          |
| ---------------------- | ------------------------------- |
| Arrow keys / WASD      | change direction                |
| `UP` / `DOWN` / W / S  | choose difficulty (start screen) |
| `ENTER` / `SPACE`      | start game (start screen)       |
| A–Z                   | type initials (after a record)  |
| `BACKSPACE`            | delete last initial typed       |
| `SPACE` or `R`         | restart (on game over)          |
| `ESC`                  | quit                            |

## Tests

The smoke tests run the game with SDL's dummy video driver, so no window is
needed:

```bash
python test_snake_game.py
```

## Ideas for extension

- A pause key and sound effects.
- Wrapping walls or a "solid wall" mode toggle.
- An AI player that follows a simple wall-following rule, for a demo mode.
- A high-score screen toggle (e.g. `F2`) instead of showing the table only
  while typing initials.
