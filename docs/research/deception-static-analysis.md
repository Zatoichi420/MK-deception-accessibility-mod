# MK: Deception (GameCube, GQNE5D) — static analysis

Method identical to the Deadly Alliance project: the disc ships an **unstripped**
copy of the game executable, so the addresses below come from its symbol table +
its linker map + disassembling its own menu/character-select functions, not from
guessing.

Extracted (local only, never committed — copyrighted):
- `mk6gc_release.elf` — ELF32 PPC BE, **not stripped, 25,669 symbols** (22,733 named+addressed)
- `mk6gc_release.MAP` — CodeWarrior linker map (symbol → address, call tree, object files)

ELF: entry `0x80003154`; `.text` `0x800055e0`; `_SDA_BASE_` `0x80517840`,
`_SDA2_BASE_` `0x805197a0`. The disc's `main.dol` entry matches, i.e. same program.

## Front-end architecture

Deception's menus are the **data-driven `mkScreenEngine`** (RTTI symbols
`ScreenNode`, `ScreenObject`, `ScreenControl`, `TextItem`, `ScreenText`,
`ScreenActionOnline*`, …). Menu screens are described by resource files; a
`ScreenControl` holds an `mkGameVariables` bag of ints. The menu cursor position
is one of those ints, written only by `mkGameVariables::SetInt` and read by
`mkGameVariables::GetInt` / `get_menu_mode_sub_var`.

Menu code lives in `menu.o` (`p_main_menu`, `set_menu_mode`, `get_pause_menu_name`,
`get_num_modeselect_portraits`, `get_modeselect_portrait_list`, `p_pause_menu`,
`p_game_options`, `p_controller_config`, `p_soundtrack`, …) and
`mwScreenEngineGlue.o` (`get_menu_mode_sub_var`).

## Main menu — CONFIRMED tables, cursor needs a live check

| addr | symbol | meaning |
|---|---|---|
| `0x80510e44` | `menu_mode_var` | which menu screen is active (values TBD live) |
| `0x80510e48` | `menu_mode_sub_var` | **highlighted item index** — strong candidate, verify live |
| `0x80510e54` | `arena_sub_menu_var` | arena-select sub-menu cursor |
| `0x8034fbc0` | `menu_string_matrix` | 6 `char*`: the top-level choices |
| `0x80510d48` / `0x80510d4c` | `main_menu_timeout_ticks` / `do_main_menu_timeout` | attract timeout |

`menu_string_matrix` resolved (in order):
**Arcade · Puzzle Kombat · Konquest · MK Chess · Versus · Go Online**

So the daemon speaks `menu_string_matrix[menu_mode_sub_var]` + "N of 6". The one
thing not yet nailed is that `menu_mode_sub_var` is *the* index (vs a sibling
var) — a 30-second `--probe` check on the main menu settles it (see CALIBRATION.md).

## Character select — CONFIRMED (roster deref verified live)

`pselect_get_player_name(player)` @ `0x800883c8`, fully disassembled:

```
r4 = (player==0) ? p1_selbox_pos [0x8051082c] : p2_selbox_pos [0x80510828]
if r4 < 0 or r4 >= 0x2c: return 0
tbl  = (pselect_mode [0x80510834] == 2) ? pselect_pz_char_tbl [0x8033ea94]
                                        : pselect_char_tbl     [0x8033e65c]
char_id = *(int*)(tbl + r4 * 0x28)                 # entry[0]
name    = *(char**)(global_player_data [0x8033c408] + char_id * 0x10)   # field 0
```

| addr | symbol | meaning |
|---|---|---|
| `0x8051082c` / `0x80510828` | `p1_selbox_pos` / `p2_selbox_pos` | **hovered roster slot (0..0x2b)** |
| `0x80510834` | `pselect_mode` | 2 = Puzzle Kombat select (different roster table) |
| `0x805107f8` | `f_arena_select_active` | on the arena-select sub-screen |
| `0x8033e65c` | `pselect_char_tbl` | normal roster, stride `0x28`, `[0]` = char id |
| `0x8033ea94` | `pselect_pz_char_tbl` | Puzzle Kombat roster |
| `0x8033c408` | `global_player_data` | stride `0x10`, `[0]` = name string ptr, indexed by char id |

**Roster slot order** — resolved from the tables, then re-checked **live on the
running game** (slots 0/2/13/26 → KENSHI / SCORPION / RANDOM / LIU KANG, matches):

```
 0 Kenshi     1 Jade        2 Scorpion    3 Mileena    4 Goro
 5 Baraka     6 Sub-Zero    7 Havik       8 Sindel     9 Raiden
10 Hotaru    11 Kabal      12 Ermac      13 Random    14 Nightwolf
15 Bo' Rai Cho  16 Noob-Smoke  17 Tanya   18 Shujinko  19 Li Mei
20 Ashrah    21 Dairou     22 Shao Kahn  23 Kobra     24 Darrius
25 Kira      26 Liu Kang
```

Bonus: `pselect_get_arena_name` (`0x80088314`), `pselect_get_style_name`
(`0x8008826c`), `pselect_get_difficulty_level` (`0x800882c4`) are ready-made
getters for the arena-select, fighting-style-select and difficulty sub-screens.

## Verdict

**Yes — the exact same daemon applies.** `ra_client.py` and `speak.py` are byte
-identical to the Deadly Alliance project; only `deception_addrs.py` +
`deception_reader.py` (the classify/label logic) are Deception-specific.

Easier than Deadly Alliance:
- The `.MAP` linker file (DA didn't have one) names the object file for every symbol.
- Menu labels are real strings in `menu_string_matrix` (DA's were in menu structs).
- `pselect_get_player_name` gave the entire character-select recipe in one 124-byte function.
- The roster deref is already verified against the live game.

Still needs a live check:
- Confirm `menu_mode_sub_var` is the main-menu cursor (and learn the `menu_mode_var`
  value for each menu screen).
- Pause menu (`get_pause_menu_name` / `p_pause_menu`) not yet wired.
- Konquest is a free-roam adventure, not a menu — out of scope, like DA's.
- Chess Kombat / Puzzle Kombat have their own board cursors (`mk_chess.o`,
  `move_cursor_based_on_quadrant` etc.) — separate future work.
