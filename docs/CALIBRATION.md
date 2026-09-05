# Calibration

Addresses in `deception_addrs.py` are for the **USA disc, `GQNE5D`**. They don't
depend on your OS, RetroArch build, ROM filename or dump format — only on the game
build.

## What's confirmed vs what needs a live check

| thing | status |
|---|---|
| Character-select fighter names (`p1_selbox_pos`/`p2_selbox_pos` → `pselect_char_tbl` → `global_player_data`) | **verified live** — reading the tables on the running game returned KENSHI / SCORPION / RANDOM / LIU KANG for slots 0/2/13/26 |
| `menu_string_matrix` labels (Arcade / Puzzle Kombat / Konquest / MK Chess / Versus / Go Online) | **verified** — resolved from the ELF |
| `menu_mode_sub_var` is *the* main-menu cursor index | **needs a 30-second check** (below) |
| Pause menu, arena/style/difficulty sub-screens, Chess/Puzzle board cursors | not wired yet |

## Confirming the main-menu cursor (30 seconds, first play)

1. Start MK: Deception, get to the main menu (Arcade / Puzzle Kombat / …).
2. `python deception_reader.py --probe` in a terminal.
3. Move up/down and watch `menu_sub=`.
   - If it counts 0..5 with the highlight and the daemon speaks the right label →
     done.
   - If a different field moves (`menu_mode`, `arena_sub`), set `MENU_MODE_SUB_VAR`
     in `deception_addrs.py` to that address and restart the daemon.
4. While you're there, note the `menu_mode=` value on each menu screen (main menu,
   Kombat submenu, Options) and open an issue / PR with them — it lets the daemon
   tell which menu you're on.

Finding the address by hand if the guess is wrong: it's a small int (0..5) that
changes ±1 on up/down. `tools/diffscan.py` automates the search (needs
`network_remote_enable = "true"` too), or use RetroArch's built-in Cheat Search.

## A different region (PAL `GQNP5D`, etc.)

Same as the Deadly Alliance project: extract that disc's `mk6gc_release.elf`
(`python tools/gc_extract.py "<disc>" extract mk6gc_release.elf .`), read its
symbol table (`pip install pyelftools capstone`; the snippet in the DA repo's
`docs/research/elf-symbols.md` works unchanged — symbol names are identical across
regions), and put the new numbers in `deception_addrs.py`. The mechanism doesn't
change.
