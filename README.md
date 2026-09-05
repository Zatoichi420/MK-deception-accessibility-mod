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

- **Verified live:** the character-select roster read (fighter names as you move
  across the roster).
- **Resolved, needs a 30-second confirm on first play:** the main-menu cursor —
  see [docs/CALIBRATION.md](docs/CALIBRATION.md).
- **Not yet wired:** pause menu, arena / fighting-style / difficulty sub-screens,
  Chess Kombat and Puzzle Kombat board cursors, Konquest. The V key / R3 OCR
  narrator (if you set it up, as in the DA project) covers those meanwhile.

## Requirements

- **RetroArch** with the **Dolphin** core.
- *Mortal Kombat: Deception*, **USA release** (disc id `GQNE5D`) — your own
  legally-obtained copy, any dump format (ISO / RVZ / NKit).
- **Python 3.8+**.
- TTS: built in on macOS (`say`) and Windows (SAPI); on Linux
  `sudo apt install speech-dispatcher espeak-ng` (or your distro's equivalent).

## Setup — step by step

Assumes RetroArch + the Dolphin core + your disc image are already working.

**1. Turn on RetroArch's network command interface (once).**
RetroArch → **Settings → Network → Network Commands → ON** (port `55355`). Or, with
RetroArch closed, set `network_cmd_enable = "true"` in `retroarch.cfg`.

**2. Check Python and a voice.** `python --version`; on Linux test `spd-say hello`.

**3. Get the code and install the daemon.**
```bash
git clone https://github.com/Zatoichi420/MK-deception-accessibility-mod
cd MK-deception-accessibility-mod
```
Then, for your OS (each takes an `uninstall` argument):

| OS | command |
|---|---|
| macOS | `install/macos/install.sh` |
| Linux | `install/linux/install.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File install\windows\install.ps1` |

Or skip the installer and just run `python deception_reader.py` in a terminal when you play.

**4. Play.** Start MK: Deception in RetroArch. The daemon notices it within a
second or two (silent during the logos). Press Start to the main menu — you'll
hear "Arcade, 1 of 6", "Puzzle Kombat, 2 of 6", … as you move. In a character
select, moving across the roster speaks the fighter names.

**5. Check / troubleshoot.**
```bash
python deception_reader.py --once     # should print a state line
python deception_reader.py --probe    # live raw state, no speech
```
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
