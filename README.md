# Tic-Tac-Toe: Critter Clash



A kid-friendly tic-tac-toe game where two teams of adorable cartoon animals face off on a playful board, narrated and cheered on by a friendly animal **Coach**. Kittens vs. Puppies — the cutest, most squeal-worthy battle for grid supremacy, built with Pygame 2.x and generated sprite assets.



Two players each pick an animal team on the team select screen, then take turns placing their critters on a 3×3 board. The Coach greets the players, announces each turn, celebrates every move with sparkles, and throws confetti for the winner. The game moves through three scenes — team select, game, and celebration — each with its own distinct generated background and on-theme styling.



The entire visual identity follows the **Chunky Kawaii** art style, committed after evaluating five candidate styles in pre-implementation research (see [Rejected Alternatives](#rejected-alternatives)).


# Favur Recording

[![Watch the demo](https://img.youtube.com/vi/VG95LhqOg-o/maxresdefault.jpg)](https://www.youtube.com/watch?v=VG95LhqOg-o)

---



## Style Guide



### Committed Style: Chunky Kawaii



Selected as the committed style after evaluating five candidates against kid-friendliness, visual cohesion, readability at 120px game-cell scale, theme fit, and production feasibility. Chunky Kawaii scored **9.5/10** — the strongest across all dimensions.



#### Palette



All sprites, backgrounds, and UI elements use the following 7-color palette. The outline color `#5A4A5C` is applied universally as a 4px stroke on every sprite.



| Role | Hex Code | RGB | Usage |

|------|----------|-----|-------|

| Primary Pink | `#FFB5C2` | (255, 181, 194) | Team 1 (Kittens) base color, celebration background |

| Mint Accent | `#B5EAD7` | (181, 234, 215) | Team 2 (Puppies) base color, game background element |

| Lavender | `#C7CEEA` | (199, 206, 234) | Coach base color, team select background |

| Peach | `#FFDAC1` | (255, 218, 193) | Warm skin/fur tone, highlight |

| Sky Blue | `#B5D8EB` | (181, 216, 235) | Game background base, water bowl element |

| Butter | `#FFF5BA` | (255, 245, 186) | Speech bubbles, star particles, highlights |

| Periwinkle | `#A8D0E6` | (168, 208, 230) | Board frame, button backgrounds, sparkles |



**Outline color**: `#5A4A5C` (warm dark gray-brown) — used for all sprite outlines. Not pure black, ensuring a warm, friendly look.



#### Shape Language



- **Head-to-body ratio**: 60% head, 30% body, 10% limbs (exaggerated kawaii proportions)

- **Primary shapes**: Circles, ellipses, and rounded blobs — zero sharp angles in any sprite silhouette

- **Face template**: Large round eyes occupying 60%+ of face width, small dot noses (8px), crescent or oval mouths (12px wide)

- **Limbs**: Chunky stubby cylinders with rounded caps, no visible joints

- **Accessories**: Simple geometric add-ons (bow on kittens, floppy ears on puppies) that preserve the round base shape



#### Line Style



- **Stroke weight**: 4px thick — consistent across all sprites, backgrounds, and UI chrome

- **Stroke cap**: ROUND

- **Stroke join**: ROUND

- **Outline color**: `#5A4A5C` (warm dark gray-brown)

- **Fill behavior**: Solid fills only — no gradients, no textures within individual sprites

- **Every sprite** has a visible 4px outline to ensure pop against any background



#### Scene Color Mapping



| Scene | Mood | Dominant Palette Colors |

|-------|------|------------------------|

| Team Select | Welcoming, calm | Lavender `#C7CEEA`, Butter `#FFF5BA`, Periwinkle `#A8D0E6` |

| Game | Playful, focused | Sky Blue `#B5D8EB`, Mint `#B5EAD7`, Peach `#FFDAC1` |

| Celebration | Joyful, energetic | Pink `#FFB5C2`, Butter `#FFF5BA`, Lavender `#C7CEEA` |



#### Character Roster



The game uses **22 generated sprites** across five asset groups, all in the Chunky Kawaii style.



**Team 1: Kittens** (Primary Pink `#FFB5C2` base)



| Asset Key | Description | Dimensions |

|-----------|-------------|------------|

| `team1_cell` | Kitten board-cell sprite (sitting pose) | 120×120px |

| `team1_wiggle` | Kitten idle animation frame (ear wiggle) | 120×120px |

| `team1_celebrate` | Kitten win celebration pose (paws up) | 120×120px |



**Team 2: Puppies** (Mint Accent `#B5EAD7` base)



| Asset Key | Description | Dimensions |

|-----------|-------------|------------|

| `team2_cell` | Puppy board-cell sprite (sitting pose) | 120×120px |

| `team2_wiggle` | Puppy idle animation frame (tail wag) | 120×120px |

| `team2_celebrate` | Puppy win celebration pose (play bow) | 120×120px |



**The Coach** (Lavender `#C7CEEA` base)



A friendly animal character (raccoon, bunny, or similar forest critter) with **six expressions**:



| Asset Key | Expression | Trigger Event |

|-----------|------------|---------------|

| `coach_wave` | Greeting/wave | `greeting` — on team select |

| `coach_point` | Thinking/pointing | `turn:X`, `turn:O` — turn calls |

| `coach_cheer_small` | Encouragement | `move_placed` — after each placement |

| `coach_cheer` | Big celebration | `win:X`, `win:O` — win celebration |

| `coach_aww` | Consoling/aww | `draw` — tie game |

| `coach_idle` | Neutral/idle | Waiting for player input |



All Coach sprites are 200×200px with visible 4px outlines and exaggerated facial features that make expression changes distinct at a glance.



**Scene Backgrounds**



| Asset Key | Scene | Dominant Palette Colors | Dimensions |

|-----------|-------|------------------------|------------|

| `bg_team_select` | Team Select | Lavender `#C7CEEA`, Butter `#FFF5BA`, Periwinkle `#A8D0E6` | 960×720px |

| `bg_game` | Game | Sky Blue `#B5D8EB`, Mint `#B5EAD7`, Peach `#FFDAC1` | 960×720px |

| `bg_celebration` | Celebration | Pink `#FFB5C2`, Butter `#FFF5BA`, Lavender `#C7CEEA` | 960×720px |



**Effects** (Particle Sprites)



| Asset Key | Description | Dimensions |

|-----------|-------------|------------|

| `sparkle` | Sparkle particle (4-point star, rounded tips) | 32×32px |

| `confetti` | Confetti particle (rounded rectangle) | 16×16px |

| `heart` | Extra delight — heart shape | 24×24px |

| `star` | Extra delight — star shape | 24×24px |



**UI Chrome**



| Asset Key | Description | Dimensions |

|-----------|-------------|------------|

| `btn_start` | "Play / Start" pill-shaped button | 200×60px |

| `btn_play_again` | "Play Again" pill-shaped button | 200×60px |

| `board_frame` | On-theme board border (garden fence with rounded pickets) | 440×440px |



---



### Rejected Alternatives



The following styles were evaluated and rejected during pre-implementation research. Each was scored on five weighted dimensions: Kid-Friendliness (25%), Visual Cohesion (25%), Readability at Scale (20%), Theme Fit (15%), Production Feasibility (15%).



#### Rejected: Soft Pastel Storybook — 6.5/10



**Palette**: `#F4DCDA`, `#D4E2D4`, `#C8E0E8`, `#FDF5E6`, `#E8D5E8`, `#F2C6C6`



**Rejection rationale**: Variable 1–3px ink lines and watercolor textures lose definition at the 120px game-cell size — team sprites look muddy rather than cute. Soft edges on foreground sprites blend into soft-edged backgrounds, causing sprites to lack visual pop. UI buttons without crisp outlines may not read as interactive to the target 5-year-old audience. While the storybook style produces beautiful backgrounds, it cannot guarantee the readability required for a 120px game cell. Chunky Kawaii's 4px outlines and round silhouettes provide guaranteed legibility at the same scale.



#### Rejected: Cartoon Vector Flat — 8.5/10



**Palette**: `#00B4D8`, `#FF6B35`, `#7B2CBF`, `#FFD166`, `#EF476F`, `#06D6A0`



**Rejection rationale**: Technically the strongest candidate — perfect readability, fastest production, clearest UI. However, standard cartoon proportions (35% head) and mathematically precise geometry read as "educational app" rather than "squeal-worthy cute." The style misses the emotional cuteness bar despite scoring highest on production and readability. The 4px outlines and exaggerated 60% head ratio of Chunky Kawaii were preferred over the 3px outlines and standard proportions of vector flat.



#### Rejected: Felt / Plush Toy — 7.7/10



**Palette**: `#A8D0E6`, `#F8A5A5`, `#F3D179`, `#6CB4A4`, `#FFF8E7`, `#DBA5A5`



**Rejection rationale**: Highest novelty factor — no other tic-tac-toe uses a felt aesthetic. The Coach as a plush toy is charming, and stitched expressions are distinctive. However, three major issues arose: (1) backgrounds cannot carry the felt style — three felt scenes look like rectangles of different colored felt, (2) effects (sparkles, confetti) feel heavy as felt shapes rather than light and floaty, and (3) AI image-gen struggles to produce consistent stitch patterns across 28+ sprites. Chunky Kawaii's backgrounds are more distinct through palette shift (lavender/sky/pink scenes), and its effects read as light particles.



#### Rejected: Whimsical Doodle — 5.6/10



**Palette**: `#E07A5F`, `#81B29A`, `#3D5A80`, `#F4A261`, `#F2CC8F`, `#5D3A5C`



**Rejection rationale**: Maximum personality but lowest production reliability. Sketch lines at 1–2px lose resolution at 120px, making asymmetric features look like errors rather than intentional style. The muted earth-tone palette (`#E07A5F`, `#81B29A`, `#3D5A80`) is less vibrant and less engaging for kids compared to Chunky Kawaii's bright pastels (`#FFB5C2`, `#B5EAD7`, `#C7CEEA`). Shadow cross-hatching at 120px resolves to visual noise. AI image-gen produces wildly inconsistent "doodle" outputs across 28+ assets, making style cohesion unreliable.



---



## Install

Ensure you have Python 3.11+ and [Poetry](https://python-poetry.org/) installed, then:

```bash
# Install dependencies
poetry install
```

This installs Pygame 2.x and all required packages defined in `pyproject.toml`.

## Run

Launch the game from the project root:

```bash
poetry run python -m src.main
```

A 960×720 window titled "Favur Tic-Tac-Toe" will open. The game starts on the Team Select screen.

## Controls

| Input | Action |
|-------|--------|
| **Mouse** | Click team portraits on team select. Click empty cells to place marks. Click "Play Again" button on celebration screen. |
| **Arrow Keys** | Move the keyboard selector around the board (up/down/left/right). |
| **Enter / Space** | Place a mark at the keyboard selector position. |
| **R** | Restart / return to team select from any scene. |
| **Escape** | Close the game window gracefully. |

## Assets

All generated sprite assets are stored in `assets/sprites/` and cataloged in `assets/manifest.json`.
Assets are produced by running:

```bash
poetry run python tools/generate_assets.py
```

See the [Style Guide](#style-guide) above for the full roster of 22 sprites and their visual specification.

To regenerate the full catalog (e.g., after modifying the generation pipeline), run the generation
script again — it overwrites all sprite files and updates `assets/manifest.json`.

## Tests

Run the complete test suite from the project root:

```bash
poetry run pytest
```

This runs all unit and integration tests (game logic, asset manifest, coach mapping, scene effects,
celebration behavior). The test suite requires no display server — all headless tests pass with
`pygame.display.set_mode()` using a dummy surface.

Expected output: all tests pass with 0 failures.

## Visual Features Coverage

All Visual Features A–E from the Statement of Work are implemented and verified:

### Feature A: Generated Sprite Catalog
- Both animal teams render as generated sprites on occupied cells (A1)
- Three distinct scene backgrounds (A2)
- Board frame and buttons are on-theme generated chrome (A3)
- All manifest keys resolve to loadable files (A4)

### Feature B: The Coach
- Coach greets players on team select with wave expression (B1)
- Coach calls turns during play with point expression (B2)
- Coach encourages after each placement (B3)
- Coach celebrates wins and consoles on draw (B4)
- Coach expression always matches the event (B5)

### Feature C: Placement Delight
- Pop-in animation on mark placement (C1)
- Sparkle burst at placed cell (C2)
- Last-move highlight visible (C3)

### Feature D: Winning Celebration
- Confetti rain on win (D1)
- Winning team celebration sprite (D2)
- Winning trail through the three cells (D3)
- Draw: no trail, friendly tie message (D4)

### Feature E: Cohesive Cute Identity
- All sprites obey the Chunky Kawaii palette (E1)
- Kid-friendly result meets the Overview bar (E2)

> Visual proof screenshots for all criteria are stored in `docs/screenshots/`.
