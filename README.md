# Mortal Kombat: Deception — talking menus (screen-reader accessibility)

Makes the **GameCube** version of *Mortal Kombat: Deception* usable without sight.
With the game running in RetroArch's Dolphin core, it speaks the highlighted main
-menu item (Arcade, Puzzle Kombat, Konquest, MK Chess, Versus, Go Online) and the
fighter you're hovering on the character-select screen.

It reads the game's memory over RetroArch's network command interface and speaks
through the OS's text-to-speech. **It never modifies or writes to the game.**

Sister project (same technique, more mature):
[**mortal-kombat-deadly-alliance-accessibility**](https://github.com/Zatoichi420/mortal-kombat-deadly-alliance-accessibility).
`ra_client.py` and `speak.py` here are byte-identical to that repo.

Works on **Windows, macOS and Linux** — the addresses are GameCube addresses,
identical on every host. See [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md).

## Status

- **Working, tested live:**
  - **Main menu** — "Kombat, 1 of 8" … "Game Options, 8 of 8" as you move up/down.
  - **Character select** — the hovered fighter for both players, on the Versus,
    Arcade and Puzzle Kombat select screens ("Player 1: Scorpion").
  - Keypress → speech is fast (single small memory read per poll once the screen
    is known).
- **How it knows which screen you're on:** it reads the game's active
  screen-procedure pointer (`func_addr$283` at `0x80510204`) and matches it
  against the symbol map — see [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md).
- **Not yet wired:** the Kombat submenu (Arcade / Versus / Practice list), Chess
  Kombat character select, the Options screens, the pause menu, match-start
  "X versus Y", arena / fighting-style pick. See
  [CONTRIBUTING.md](CONTRIBUTING.md) — several of these just need one calibration
  trace. The V key / R3 OCR narrator (as in the DA project) covers them meanwhile.
- **Deliberately out of scope:** online play, Profiles, the Krypt, Konquest —
  see [CONTRIBUTING.md](CONTRIBUTING.md) if you'd like to add them.

## Requirements

- **RetroArch** with the **Dolphin** core.
- *Mortal Kombat: Deception*, **USA release** (disc id `GQNE5D`) — your own
  legally-obtained copy, any dump format (ISO / RVZ / NKit).
- TTS: built in on macOS (`say`) and Windows (SAPI); on Linux
  `sudo apt install speech-dispatcher espeak-ng` (or your distro's equivalent).
- Python is **not** required if you use the downloaded binary below. It is only
  needed to run from source (Python 3.8+).

## Setup — step by step

Assumes RetroArch + the Dolphin core + your disc image are already working.

**1. Turn on RetroArch's network command interface (once).**
RetroArch → **Settings → Network → Network Commands → ON** (port `55355`). Or, with
RetroArch closed, set `network_cmd_enable = "true"` in `retroarch.cfg`.

**2. Download the reader for your system** from the
[**Releases**](https://github.com/Zatoichi420/MK-deception-accessibility-mod/releases)
page — one file, nothing to install:

| System | File |
|---|---|
| Windows | `mkdeception-reader-windows-x86_64.exe` |
| macOS (Apple Silicon) | `mkdeception-reader-macos-arm64` |
| Linux | `mkdeception-reader-linux-x86_64` |

**3. Run it.** Two ways:

- **Just run it when you play** — double-click it, or from a terminal
  `./mkdeception-reader` (`mkdeception-reader-windows-x86_64.exe` on Windows).
  Leave it running while you play; close it when you're done.
- **Or have it start on its own:** run it once with `--install`. It registers a
  hidden per-user background service (launchd / systemd / Task Scheduler) and
  starts every time you log in. `--uninstall` removes it, `--status` reports it.

  ```
  ./mkdeception-reader --install
  ```

  On macOS the first run may be blocked by Gatekeeper — right-click → Open, or
  `xattr -d com.apple.quarantine ./mkdeception-reader`.

<details>
<summary>Run from source instead (for contributors)</summary>

```bash
git clone https://github.com/Zatoichi420/MK-deception-accessibility-mod
cd MK-deception-accessibility-mod
python deception_reader.py            # run it now
python deception_reader.py --install  # or register the background service
```

The repo's `install/{macos,linux,windows}/` scripts do the same thing plus
fix RetroArch's network settings for you.
</details>

**4. Play.** Start MK: Deception in RetroArch. The daemon notices it within a
second or two (silent during the logos). Press Start to the main menu — you'll
hear "Arcade, 1 of 6", "Puzzle Kombat, 2 of 6", … as you move. In a character
select, moving across the roster speaks the fighter names.

**5. Check / troubleshoot.**
```bash
./mkdeception-reader --once     # should print a state line
./mkdeception-reader --probe    # live raw state, no speech
```
(`python deception_reader.py --once` etc. from a source checkout.)
Logs: `~/Library/Logs/mkdeception-menu-reader.log` (macOS) ·
`journalctl --user -u mkdeception-menu-reader` (Linux) ·
`%LOCALAPPDATA%\mkdeception-talking-menu\deception_reader.log` (Windows).

Env vars: `MK_RA_HOST`, `MK_RA_PORT`, `MK_VOICE`, `MK_RATE_WPM`, `MK_SPEAK_BACKEND`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Especially wanted: the main-menu cursor
confirmation, the pause menu, and Windows/Linux testing.
Be kind: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Legal

This repository contains **no game code, assets, or data**. It is an independent
accessibility / interoperability tool: it reads values from memory at runtime and
speaks them. You supply your own copy of the game.

*Mortal Kombat* and related marks are trademarks of Warner Bros. Entertainment
Inc.; this project is not affiliated with or endorsed by Warner Bros. or
NetherRealm Studios. See [LICENSE](LICENSE) (MIT).
