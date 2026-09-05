# How it works

Same technique as the [Deadly Alliance
project](https://github.com/Zatoichi420/mortal-kombat-deadly-alliance-accessibility) —
see its `docs/HOW-IT-WORKS.md` for the long version. In short:

```
  RetroArch (Dolphin core, MK: Deception running)
      │  UDP :55355   "READ_CORE_MEMORY <addr> <n>"
      ▼
  deception_reader.py  — read the menu cursor / hovered fighter, speak it on change
      ▼
   say / spd-say / SAPI
```

Nothing is written to the game. The addresses are GameCube addresses (a property
of the game, not your PC), so it works identically on Windows, macOS and Linux —
only `speak.py` and the `install/` scripts are OS-specific.

## Why Deception was straightforward to add

The disc ships **`mk6gc_release.elf`** — the game executable, **unstripped**
(25,669 symbols) — and **`mk6gc_release.MAP`**, the full CodeWarrior linker map.
So the work was reading the game's own symbol names and disassembling two
functions, not guessing. Details + every address: `docs/research/`.

## Main menu

Deception's front-end is the data-driven `mkScreenEngine`. The 6 choices are a
fixed table `menu_string_matrix` (`0x8034fbc0`):

**Arcade · Puzzle Kombat · Konquest · MK Chess · Versus · Go Online**

The highlighted index is held as an `mkGameVariables` int — `menu_mode_sub_var`
(`0x80510e48`) is the strong candidate; `menu_mode_var` (`0x80510e44`) is which
menu screen. The daemon speaks `menu_string_matrix[menu_mode_sub_var]` + "N of 6".
(The `menu_mode_sub_var` binding wants a 30-second live check — see
[CALIBRATION.md](CALIBRATION.md).)

## Character select

Decompiled straight out of `pselect_get_player_name` (`0x800883c8`):

```
slot = p1_selbox_pos [0x8051082c]   (or p2_selbox_pos [0x80510828]),  0..0x2b
tbl  = pselect_mode==2 ? pselect_pz_char_tbl [0x8033ea94] : pselect_char_tbl [0x8033e65c]
id   = *(int*)(tbl + slot*0x28)
name = *(char**)(global_player_data [0x8033c408] + id*0x10)
```

Roster slot order (verified live): Kenshi, Jade, Scorpion, Mileena, Goro, Baraka,
Sub-Zero, Havik, Sindel, Raiden, Hotaru, Kabal, Ermac, Random, Nightwolf, Bo' Rai
Cho, Noob-Smoke, Tanya, Shujinko, Li Mei, Ashrah, Dairou, Shao Kahn, Kobra,
Darrius, Kira, Liu Kang.

`pselect_get_arena_name` / `pselect_get_style_name` / `pselect_get_difficulty_level`
are ready for the arena-, style- and difficulty-select sub-screens (not yet wired).

## Files

| file | role |
|---|---|
| `deception_reader.py` | the daemon |
| `ra_client.py` | RetroArch UDP client — **byte-identical to the Deadly Alliance repo** |
| `speak.py` | cross-platform TTS — **byte-identical to the Deadly Alliance repo** |
| `deception_addrs.py` | all game-specific addresses + the menu / roster tables |
| `tools/` | the disc extractor + PPC disassembler used to find the addresses |
| `docs/research/` | static analysis + community / decomp / cheat-code research |
