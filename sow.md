# Statement of Work — Tic-Tac-Toe: Critter Clash

**Version:** 2.0 · **Date:** June 2026 · **Status:** Final
> **Tier:** Hard · **Category:** GUI / generated-asset showcase · **Verifies:** generated image-asset production at scale, asset↔code integration, reactive character state, animation + particle systems, cohesive visual identity — over a still-deterministic, unit-testable game core

> You are building a new, standalone project from this specification. You are tasked with
> completing this Statement of Work **fully and completely**. While working, keep these key
> facts in mind:
>
> - This is a **greenfield project** — there is no existing code. Build it from scratch, exactly as the Project Structure specifies. Do not add files, modules, or features beyond the spec.
> - Use **Poetry** to run Python, always.
> - **Verify the real pygame API before writing code** — confirm the installed version and that the calls you use exist. Never code against a remembered API.
> - **Separate the `Board` logic from rendering, assets, and the coach** so win/draw detection and the coach's event mapping are testable without a display.
> - **The image generation IS the work here.** A correct but plain tic-tac-toe is a failing result for this fixture — the asset catalog, the coach, and the feedback systems are the point.
> - **Tests must exercise real behavior**, and every visual feature must be confirmed against the running app — unit tests alone cannot satisfy the cuteness criteria.
> - **Verify your own work** — run the app and tests, and capture screenshots plus scripted key/mouse presses for every scene and Visual Feature.
> - **Complete every acceptance criterion.** Partial completion is not "done."
> - If the spec is genuinely ambiguous, make a reasonable choice, note it in the README, and continue.
> - Maintain a calm and professional demeanor.


## Overview

The cutest, most kid-friendly tic-tac-toe imaginable: two teams of adorable cartoon animals
face off on a playful board, narrated and cheered on by a friendly animal **Coach** who greets
the players, calls whose turn it is, celebrates every move with sparkles, and throws confetti
for the winner. The bar is unapologetically high — *a five-year-old should squeal to play it.*

As an eval, this fixture is the visual-generation counterpart to 2048's mechanical creativity.
The game logic is trivial and stays trivial on purpose; the stress is on producing a **large,
cohesive catalog of generated sprite assets**, wiring them into a reactive character system,
and layering animation and particle feedback into a single consistent identity — all of which
must hold together and be demonstrable on screen. The standard discipline still applies: the
`Board` is deterministic and unit-tested, the asset catalog is verified against a manifest, and
the Coach's reactions are a pure, testable mapping.

## Pre-Implementation Research

Before generating the full catalog or writing rendering code, do a discovery pass:

1. **Art-style spike.** Generate a few candidate styles and character casts (e.g. soft pastel
   storybook vs. chunky kawaii vs. felt/plush), evaluate them against the cuteness and
   cohesion bar, then **commit to one** style guide — palette, line/shape language, character
   roster — and record it (with the rejected alternatives) in the README. This style guide is a
   required output, not a private step; every later asset must obey it.
2. **Generation-pipeline spike.** Confirm the image-generation capability can produce a sprite
   with transparency at the needed size, and stand up the reproducible generation step (script +
   manifest) on a single asset before generating the whole catalog.
3. **Asset-budget sanity.** Confirm pygame can load and composite the planned number of sprites
   (cast + coach expressions + backgrounds + effect frames) at 60 FPS in the target window.

## Requirements

### Functional Requirements

- The app opens a single window with a deterministic title and fixed size, and moves through
  three scenes: **team select**, **game**, and **celebration**.
- On **team select**, each player picks an animal team by clicking its portrait; the Coach
  greets them by team. A start control begins the game. (A typed nickname per player is optional
  and, if present, is shown by the Coach.)
- On the **game** scene, a 3×3 board is shown. Clicking an empty cell places the current
  player's animal in that cell with a pop-in animation and a sparkle burst, then switches turns.
  An occupied cell cannot be claimed. Keyboard play is also supported (arrow keys move a cute
  selector, Enter places).
- After each move the app checks for a win (row/column/diagonal) or a draw and transitions to
  the celebration scene.
- On **celebration**, the winning team's animals cheer, confetti rains, the winning line is
  drawn as a playful trail, and the Coach delivers a congratulations line (or a gentle "great
  game, it's a tie!" with a consoling animation on a draw). A clearly labeled, kid-readable
  "Play again" control (and pressing `R`) returns to team select.
- The **Coach** is present on every scene and reacts to events (greeting, turn calls,
  encouragement, win, draw) with a matching generated expression and a short speech-bubble line.
- Pressing `Escape` on any scene closes the window gracefully.

### Technical Requirements

- Python 3.11+.
- Pygame 2.x (the only graphical runtime dependency).
- The image-generation capability used to produce the sprite catalog (see Reference Documents).
- Poetry + `pyproject.toml` for dependencies and build.
- Window title: exactly `Favur Tic-Tac-Toe`.
- Window size: 960×720, non-resizable.
- Each scene has a visually distinct, on-theme background so screenshots differentiate easily.
- The current scene name is drawn small in a fixed corner as a test-mode overlay.
- **Generated assets only** — every sprite, character, background, and effect frame is produced
  by the project's own generation step. No stock images, no clip-art, no third-party sprite
  packs. (This inverts the old "programmatic shapes only" rule: here the imagery must be
  *generated assets*, not `pygame.draw` primitives.)

### Asset Catalog (required, minimum)

All assets are generated, transparent where appropriate, and listed in `assets/manifest.json`:

- **Two animal teams** (player marks), e.g. Kittens vs. Puppies — for each team: a board-cell
  sprite, an idle "wiggle" frame or two, and a celebration pose.
- **The Coach** — one friendly animal character with at least five expressions: *greeting/wave,
  thinking/pointing (turn call), cheering (win), aww/consoling (draw),* and *idle.*
- **Three scene backgrounds** — team select, game board, celebration — in the committed style.
- **Effect sprites** — sparkle, confetti, and at least one extra delight (hearts/stars).
- **UI chrome** — rounded, kid-readable buttons and the board frame rendered on-theme (a garden
  fence, a toy shelf, etc.) rather than plain lines.

## Project Structure

```
├── assets/
│   ├── manifest.json          # every asset: key, file, generation prompt/spec, size
│   └── sprites/               # generated PNGs (teams, coach, backgrounds, effects, ui)
├── tools/
│   └── generate_assets.py     # reproducible asset-generation step that writes assets/ + manifest
├── src/
│   ├── __init__.py
│   ├── game.py                # pure Board logic, no pygame
│   ├── assets.py              # loads + validates the catalog against the manifest
│   ├── coach.py               # pure event→(expression, line) mapping for the Coach
│   ├── effects.py             # animation + particle systems
│   ├── scenes.py              # TeamSelectScene, GameScene, CelebrationScene
│   └── main.py                # pygame init, window, loop, event dispatch, Escape-to-quit
├── tests/
│   ├── __init__.py
│   ├── test_game.py           # board logic
│   ├── test_assets.py         # manifest completeness + load
│   └── test_coach.py          # event→reaction mapping
├── pyproject.toml
└── README.md
```

## Implementation Details

- `src/game.py`: Pure-Python `Board` with `place(row, col, mark)`, `winner()` (`"X"`, `"O"`,
  `"draw"`, or `None`), `is_full()`, `winning_cells()` (the three winning coordinates or empty),
  and `reset()`. Internally still uses `"X"`/`"O"`; rendering maps `X`→player 1's team sprite and
  `O`→player 2's. No pygame.
- `src/assets.py`: Loads `assets/manifest.json`, loads every referenced sprite, and exposes them
  by key. On a missing or unreadable asset it raises a clear error naming the missing key.
- `src/coach.py`: A pure function (or small class) mapping a game event
  (`greeting`, `turn:X`, `turn:O`, `move_placed`, `win:X`, `win:O`, `draw`) to an
  `(expression_key, line_text)` pair. No pygame, no randomness that isn't seeded.
- `src/effects.py`: Pop-in/scale animations for placed marks, the idle wiggle, sparkle bursts on
  placement, and confetti on win — time-based and frame-rate independent.
- `src/scenes.py`: The three scenes, each `handle_event(event)`/`draw(surface)`; `GameScene`
  owns the keyboard selector and the last-move position; `CelebrationScene` receives
  `winning_cells()` to draw the celebratory winning trail.
- `src/main.py`: Initializes pygame, creates the 960×720 `Favur Tic-Tac-Toe` window, runs the
  loop, dispatches events, and handles global Escape-to-quit.
- `tools/generate_assets.py`: The reproducible generation step that produces every catalog asset
  and writes `assets/manifest.json`. Documented so the catalog can be regenerated.
- `README.md`: Title, overview, the committed art style guide (and rejected alternatives),
  installation, run instructions, controls, how assets are generated, and how to run the tests.

## Visual Features

Each feature can only be confirmed against the running app and has its own lettered acceptance.

### Feature A: Generated Sprite Catalog
**Deliverable:** Every required asset in the catalog is generated, listed in the manifest, and
actually used in the app — teams on the board, the Coach, three backgrounds, effect sprites, and
on-theme UI chrome. Nothing is a `pygame.draw` stand-in for a missing sprite.

**A1.** Both animal teams render as generated sprites in the cells they occupy.
**A2.** All three scenes use their distinct generated backgrounds.
**A3.** The board frame and buttons are on-theme generated chrome, not plain lines/rectangles.
**A4.** Every key in `assets/manifest.json` resolves to a real, loadable file (also checked in tests).

### Feature B: The Coach
**Deliverable:** A friendly animal Coach is visible on every scene with a speech bubble, and its
expression + line change to match the current event (greeting, turn calls, encouragement after a
move, win, draw).

**B1.** On team select, the Coach greets the players with the greeting expression and a welcome line.
**B2.** During play, the Coach shows the turn-call expression and names whose turn it is; the
line updates when the turn switches.
**B3.** After a placement, the Coach gives a short encouragement reaction.
**B4.** On a win, the Coach shows the cheering expression; on a draw, the consoling expression —
each with a fitting line.
**B5.** The Coach's expression always matches the event (verified against the pure mapping in tests, and on screen).

### Feature C: Placement Delight
**Deliverable:** Placing a mark plays a pop-in/scale animation on the animal and emits a sparkle
particle burst at that cell.

**C1.** A newly placed animal visibly animates in (scale/bounce) rather than appearing instantly.
**C2.** A sparkle burst is emitted at the placed cell and fades out.
**C3.** The most recent move is gently highlighted until the next move (a friendly "last move" glow).

### Feature D: Winning Celebration
**Deliverable:** On a win, confetti rains, the winning team's animals play their celebration
pose, and the winning line is drawn as a playful trail through the three cells.

**D1.** Confetti particles animate across the celebration scene on a win.
**D2.** The winning team's celebration sprite is shown.
**D3.** A playful winning trail passes through the three winning cells (correct orientation for
row / column / each diagonal).
**D4.** On a draw, no winning trail is drawn; a friendly tie celebration plays instead.

### Feature E: Cohesive Cute Identity
**Deliverable:** Every generated asset obeys one committed style guide — palette, shape language,
character cast — so the whole app reads as a single adorable world.

**E1.** All sprites share the committed palette and style (no off-style or mismatched asset).
**E2.** The overall result clearly meets the kid-friendly bar described in the Overview.

## Error Handling Strategy

- A missing or unreadable asset fails **loudly at startup** with a message naming the missing
  manifest key — never a silent blank sprite, and never a mid-game crash.
- An occupied-cell click or an Enter on a filled cell is a friendly no-op (optionally a tiny
  "oops" wobble), not an error.
- The app must never show a raw traceback to the player; startup is the only place a hard failure
  is acceptable, and it must be legible.

## Testing Requirements

Per the Favur testing architecture, logic is unit-tested headlessly with no pygame display:

- `test_game.py`: placing marks, rejecting occupied cells, win detection on every
  row/column/diagonal, draw detection, `winning_cells()` correctness per win type, and `reset()`.
- `test_assets.py`: `assets/manifest.json` contains every required catalog key, and each entry
  points to a file that exists and loads.
- `test_coach.py`: the event→(expression, line) mapping returns a valid, known expression for
  every game event and is a pure function (same event → same reaction).

The five Visual Features are verified against the running app via screenshots and scripted
key/mouse presses, per their lettered criteria — they cannot be satisfied by unit tests alone.

## Implementation Phases

1. **Research & style spike** — exit when the art style guide is committed and recorded, and the
   generation pipeline produces one valid transparent sprite.
2. **Game core + tests** — `Board` and its tests green, headless, no rendering yet.
3. **Asset generation** — produce the full catalog and `manifest.json`; `test_assets.py` green.
4. **Coach + scenes + rendering** — wire assets into the three scenes and the Coach mapping;
   `test_coach.py` green; game playable end-to-end.
5. **Animation, particles & polish** — pop-ins, sparkles, confetti, identity polish to the
   cuteness bar.
6. **Visual proof** — capture screenshots and scripted presses demonstrating Features A–E.

## Acceptance Criteria

1. The window opens with the exact title `Favur Tic-Tac-Toe` at 960×720 and is not resizable.
2. Team select lets each player pick an animal team by click and the Coach greets them; a start control begins the game.
3. Clicking an empty cell places the current team's animal (with pop-in + sparkle) and switches turns; an occupied cell does nothing.
4. Completing any row, column, or diagonal transitions to the celebration scene with the winning team celebrating.
5. A full board with no winner transitions to the celebration scene with a friendly tie celebration.
6. `R` (and the on-screen control) returns to team select.
7. Pressing `Escape` on any scene closes the window without errors.
8. All five Visual Features satisfy their lettered acceptance criteria (A1–A4, B1–B5, C1–C3, D1–D4, E1–E2).
9. Every asset is generated by the project's own generation step and listed in the manifest — no external/stock imagery and no `pygame.draw` stand-ins for missing sprites.
10. The committed art style is recorded in the README and obeyed by every asset.
11. The project is generated with the specified file structure.
12. All Python files are free of syntax errors.
13. `poetry run pytest` passes with **0 failures — mandatory**.
14. `poetry run python -m src.main` launches the game without errors.
15. Visual proof is captured and verified via screenshots and scripted key/mouse presses for every scene and every Visual Feature.

## Appendix A — Coach reaction table (worked example)

A model for the `coach.py` mapping; the exact lines are the implementer's to make charming:

| Event | Expression key | Example line |
|---|---|---|
| `greeting` | `wave` | "Hiii! Pick your team and let's play!" |
| `turn:X` | `point` | "Kittens' turn — where will you go?" |
| `turn:O` | `point` | "Puppies' turn — you've got this!" |
| `move_placed` | `cheer_small` | "Ooh, nice spot!" |
| `win:X` | `cheer` | "Kittens win! Hooray! 🎉" |
| `draw` | `aww` | "It's a tie — great game, friends!" |

## Document Control

| Version | Date | Change |
|---|---|---|
| 1.0 | June 2026 | Standardized scene-managed tic-tac-toe with cursor/halo/winning-line visual features. |
| 2.0 | June 2026 | Repurposed to stress **image/asset generation**: generated sprite catalog, reactive Coach, animation + particle systems, cohesive cute identity. Game core kept deterministic and unit-tested; old keyboard-cursor/halo features superseded by the asset-generation feature set. |
