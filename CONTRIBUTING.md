# Contributing

Thanks for helping make this game playable without sight. Contributions of every
size are welcome — a typo fix, a tested set of addresses for the PAL disc, a new
screen wired up, or just a report that it did or didn't work on your setup.

This is a small project maintained in spare time. Please be patient with review,
and be kind in issues and PRs — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Things that would genuinely help

| Area | What's needed |
|---|---|
| **Testing on Windows / Linux** | The daemon and installers are written for all three OSes but only macOS is verified. A "it works" or a bug report from Windows/Linux is valuable. |
| **The Kombat submenu** | The play-mode list (Arcade / Versus / Practice / …) that opens from "Kombat" isn't read yet — its screen-proc and cursor need a live `tools/proc_log.py` trace. |
| **Chess Kombat character select** | Reads nothing today — it uses a screen-proc not yet in the daemon's `_CS_PROCS` set. Needs one `proc_log.py` capture on that screen. |
| **The Options screens** | `p_game_options` (0x801ad198) is identified but its cursor + row labels + the Gameplay / Audio / Video / Controller sub-screens are unmapped. This is the top request — it's what stops a blind player changing settings alone. |
| **The pause menu** | `p_pause_menu` (0x801ad2d0) — identified, not wired. |
| **Match start** | Announce "\<left fighter\> versus \<right fighter\>" once when a round begins (MK:DA already does this — port the pattern). |
| **Other regions** | Addresses for PAL (`GQNP5D`), German (`GQND5D`), Japan (`GQNJ5D`). The method is in [docs/CALIBRATION.md](docs/CALIBRATION.md) §2 — it's reading a symbol table, not guessing. |
| **Speech backends** | Better interruption on Linux, a `pyttsx3` path, NVDA/Tolk on Windows for people who already run a screen reader. |
| **Other GameCube games** | The whole approach (`ra_client.py` + a per-game `*_addrs.py`) generalises. A sibling repo or a `games/` folder — open an issue to discuss. |

### Out of scope for this repo — but a contributor is welcome to take them on

The maintainer plays this game offline with no profile, so the following are **not
being worked on here**. If you want them, they'd make great standalone contributions —
open an issue first so we can point you at the right screen-procs:

- **Online / network play** — anything behind "Go Online".
- **Profiles** — the profile create / load / name-entry keyboard screens.
- **The Krypt** — the koin-spend unlock grid (needs a profile).
- **Konquest** — the story mode (`p_konquest_*` procs; its own pause menu at `p_konquest_pause_menu` 0x801800d0).

## Development setup

You need RetroArch + the Dolphin core + a legally-obtained MK:DA **USA** disc
(any dump format). See the setup steps in the [README](README.md#setup).

```bash
git clone https://github.com/Zatoichi420/MK-deception-accessibility-mod
cd MK-deception-accessibility-mod

# run the daemon straight from the checkout (no install needed for dev)
python deception_reader.py --probe        # live state, no speech
python deception_reader.py                # with speech

# print what it would say, without speaking:
MK_SPEAK_BACKEND=log python deception_reader.py
```

The reverse-engineering / calibration helpers in `tools/` need
`pip install pyelftools capstone` and, for `nav.py`/`calibrate.py`/`verify.py`,
`network_remote_enable = "true"` in `retroarch.cfg`. See [tools/README.md](tools/README.md).

There are no build steps and no dependencies for the daemon itself — it's plain
Python 3.8+ stdlib.

## How the code is organised

- `deception_reader.py` — the daemon: classify the screen, resolve the label, speak on change.
- `ra_client.py` — RetroArch UDP client. Pure sockets, no game knowledge.
- `deception_addrs.py` — **all** game-specific numbers: addresses, the menu label
  tables, the roster. If you're retargeting a region, this is the only file that changes.
- `speak.py` — cross-platform TTS.
- `tools/` — how the addresses were found (documented, reproducible).
- `docs/` — how it works, calibration, and the raw research.

Keep game-specific constants in `deception_addrs.py`, host-specific behaviour in
`speak.py` / `install/`, and generic RetroArch plumbing in `ra_client.py`.

## Style

- Match the surrounding code. It's plain Python, `from __future__ import annotations`,
  standard library only in the daemon.
- No new runtime dependencies for `deception_reader.py` / `ra_client.py` / `speak.py`
  without discussing it first.
- Comment *why*, and cite the source when you add an address — a symbol name, a
  disassembly line, or "verified live pressing Down on screen X". Every number in
  `deception_addrs.py` should be traceable.

## Submitting changes

1. Fork, branch off `main`.
2. Make the change. Test it against a running game if it touches the daemon —
   say what you tested in the PR ("navigated the main menu and Options submenu,
   heard the right labels" / "ran `--probe` on the PAL disc").
3. Open a PR. Fill in the template. Small, focused PRs merge faster.
4. New addresses: include how you verified them, and ideally a short
   `--probe` transcript.

By contributing you agree your work is licensed under the project's
[MIT License](LICENSE).

## Reporting bugs / asking for a screen

Use the issue templates. For a bug, the daemon log
(`~/Library/Logs/mkdeception-menu-reader.log` / `journalctl --user -u mkdeception-menu-reader` /
`%LOCALAPPDATA%\mkda-talking-menu\menu_reader.log`) and a `--probe` snippet from
the screen where it went wrong are the most useful things you can attach.

## A note on scope and the game

This project ships **no game code or assets** and never will. It reads values from
memory at runtime. Please don't attach ROMs, disc images, or extracted game files
to issues or PRs — they'll be removed. See the legal note in the [README](README.md#legal).
