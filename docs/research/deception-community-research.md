# Mortal Kombat: Deception — Community / Reverse-Engineering Research

Feasibility research for a screen-reader / talking-menu accessibility tool.
Primary target: **GameCube USA, disc ID `GQNE5D`** (internal build `0.142_gc`).
Secondary: PS2 USA and Xbox USA.

Compiled 2026-09-05. Every source is linked inline. No code in this document.

---

## 0. Corrections to the brief (verify before building)

| Assumption in brief | What the sources actually say |
|---|---|
| PS2 serial `SLUS-20984` | **No such serial.** MK: Deception PS2 NTSC-U is **`SLUS-20881`**. Variants: `SLUS-21081` / `SLUS-21101` (Premium Pack), `SLUS-20881GH` (Greatest Hits). PAL = `SLES-52705` / `SLES-52706`. `psxdatacenter.com/psx2/games2/SLUS-20984.html` is 404. (Sources: [PCSX2 Wiki](https://wiki.pcsx2.net/Mortal_Kombat:_Deception), [psxdatacenter SLUS-20881](https://psxdatacenter.com/psx2/games2/SLUS-20881.html)) |
| "Deception GC had online play" | **The GameCube version has no online play.** Online (GameSpy-backed, matches + tournaments + online Chess/Puzzle) shipped **only on PS2 and Xbox**, Oct 2004. GameSpy servers died 2014-05-31. GC shipped ~4 months later with Goro + Shao Kahn as playable-character compensation *for* the missing online. (Sources: [GameSpot hands-on](https://www.gamespot.com/articles/mortal-kombat-deception-hands-on/1100-6117091/), [Eurogamer](https://www.eurogamer.net/news231204mkdeceptioncube), [VGDB](https://www.vgdb.co/games/mortal-kombat-deception)) |
| `github.com/ermaccer/MK-Deception-Decompilation` | Does not exist under that name. The decomp is **`github.com/cScarletter/MK-3D-Era-Decompilation`** (originally created as `cScarletter/MK-Deception-Decompilation`, later renamed). ermaccer is the *tool* author, not the decomp owner. |

---

## 1. Decompilation / reverse-engineering projects

### 1a. cScarletter/MK-3D-Era-Decompilation (the "MK 3D-era decomp")
<https://github.com/cScarletter/MK-3D-Era-Decompilation>
(repo description: "Investigating and studying Mortal Kombat: Deadly Alliance, Deception, and Armageddon for all platforms"; created 2024-11-06, last push 2025-06-10, ~5 stars, ~40 commits)

- **It is primarily a *Deception* project.** Original repo name was `MK-Deception-Decompilation`; the README still says *"Mortal Kombat Deception Decompilation … Investigating and decompiling Mortal Kombat Deception for PS2, Gamecube, and Xbox."* Deadly Alliance / Armageddon are only along for the ride because they share the engine.
- **Maturity: very low.** The repo is essentially: extracted `.dff` models converted to `.dae` (under `PS2/models`), a reorganised dump of disc contents (`PS2/disc content (original organization)` and `PS2/reorganized/data`), plus two short text notes. **No Ghidra output, no function map, no struct headers, no address tables are committed.** "NO usable game assets, only decompiled files and extracted models."
- Tools it declares: Ghidra, [SSFExplorer](https://github.com/ermaccer/SSFExplorer), [mkoasm](https://github.com/ermaccer/mkoasm), PSound.
- The only structural documentation in the repo is the file **`General game notes`** (308 bytes, full contents):

  ```
  Main Menu
    > Kombat            > Arcade / Versus / Practice
    > Chess Kombat
    > Puzzle Kombat
    > Konquest
    > MK Online
    > The Krypt
    > Kontent
    > Profiles
    > Game Options      > Gameplay ( > Blood Level: OFF/LOW/MEDIUM/MAX, default MAX )
                        > Audio
                        > Video
                        > Controller
  ```

  and **`Interesting finds`** (points at the leftover E3 "THANK YOU FOR PLAYING E3 DEMO" screen in `MKDA.PAK/art/_ssf unpacked/attract.ssf/1`). `Navigation.md` is an empty 0-byte file.

**Takeaway:** the "decomp" gives you the confirmed top-level menu tree and nothing more. It is not a code-level resource yet.

### 1b. ermaccer's toolchain (this is where the real structural knowledge lives)

Profile: <https://github.com/ermaccer> · blog <https://ermaccer.github.io>

| Repo | What it does | Relevance to Deception |
|---|---|---|
| [`mkoasm`](https://github.com/ermaccer/mkoasm) | `.MKO` script assembler/disassembler/decompiler | **Full support for Deception** (view/extract/**decompile**/**compile**), PS2+GC+Xbox. Ships a definition table `data/mkd_def.txt`. |
| [`SSFExplorer`](https://github.com/ermaccer/SSFExplorer) | GUI to view/extract/**build** `.ssf` archives (and nested archives) + export textures | Deception, Armageddon, Unchained, Deadly Alliance. `.ssf` is the container the menu/Konquest/string data lives in. |
| [`MortalKombat.PAKTool`](https://github.com/ermaccer/MortalKombat.PAKTool) | Extract/create `MKDA.PAK` (the master archive on the disc) | DA / Deception / Armageddon, PS2. (GC/Xbox use a slightly different packaging.) |
| [`MortalKombat.Tools`](https://github.com/ermaccer/MortalKombat.Tools) | Grab-bag CLI: `ssfx`, `paktool`, **`toceditor`** (dump/inject TOC tables — D/A/U, PS2/PSP/Xbox), `texconv` | `toceditor` is how the file-table that gates arena loading is edited. |
| [`MKDHook`](https://github.com/ermaccer/MKDHook) / blog [post](https://ermaccer.github.io/posts/mkdhook/) | PCSX2 (fork-with-plugins) runtime plugin | **PS2 `SLUS20881` only.** In-game debug menu (camera, HUD toggle, player-size), NPC select screen, Konquest first-person + free-cam, **expanded stage select** that restores the cut *Katakombs* stage. Note: "due to the expanded stage select, Chess Kombat and Puzzle Kombat modes are glitched." |
| [`ultimate-mkd`](https://github.com/ermaccer/ultimate-mkd) | Content mod built on MKDHook | Not RE documentation; roster/moveset/palette mod for PS2. |
| [`RandomLaddersMKA`](https://github.com/ermaccer/RandomLaddersMKA) | Armageddon ladder randomiser | Peripheral. |

Other MK-family repos by ermaccer (not Deception-relevant): `MKGExplorer` (MK Gold), `mksftool` (Special Forces), `MKTHook` (Trilogy), `MKGExplorer`, `MK9Hook`/`MKXHook`/`MK11Hook`/`MK1Hook`, `wgwiffx` (War Gods).

### 1c. `.MKO` / `.cmo` script format — what Deception changed (from the [`mkoasm` README](https://github.com/ermaccer/mkoasm/blob/master/README.md))

The engine is script-driven. `mkoasm`'s own "MKO Overview" documents the generational jump:

- **Deadly Alliance** — first version (`.cmo`). *Functions only, no variables.* Almost everything is a call into an executable-resident function. Roster / stage / fightstyle data is hardcoded in the ELF.
- **Deception** — the format grows a lot:
  - static variables + local variables + arithmetic on both
  - script→script function calls **with parameters** and dynamic/variable arguments
  - limited procedure creation from scripts
  - **"Most executable objects exported into MKO (fightstyle, character, stage data and more)"**
  - "FX fully moved to MKO"
- **Armageddon** — adds variable *links*, multiple function sets (FX/game/core), and **ID-based string variables instead of raw data offsets**.

**Consequence for an accessibility tool:** in Deception a lot of the roster / stage / style tables that were compiled constants in Deadly Alliance are now data inside `.MKO` scripts packed in `.ssf`. Strings, however, are still referenced by **data offset** (the ID-based string-var scheme doesn't arrive until Armageddon), which is good — a string table dumped once from the disc stays valid.

### 1d. `mkd_def.txt` — the Deception opcode dictionary
<https://github.com/ermaccer/mkoasm/blob/master/data/mkd_def.txt>
Format per line: `name  id  numArgs  argTypes`. It enumerates on the order of ~2,000 script functions. Menu/flow-relevant named opcodes seen include:
`sleep` (0), `true_branch` (1), `branch` (2), `script_return` (8), `script_exit` (9), `was_button_pressed` (24), **`get_mode_of_play` (178)**, `am_i_flipped` (15), plus large blocks for animation/collision/FX/fatality. `get_mode_of_play` is the sort of hook that tells you *which* mode (Arcade / Versus / Konquest / Chess / Puzzle / Krypt) the engine currently thinks it is in.

### 1e. Other file-format tooling worth knowing
- [`leeao/MortalKombat`](https://github.com/leeao/MortalKombat) — Noesis plugin for MK PS2/PSP `.DFF` and `MKA` models.
- decomp tooling that would be used against the GC build: [`encounter/decomp-toolkit`](https://github.com/encounter/decomp-toolkit) (`dtk map …` parses CodeWarrior `.MAP` files — directly relevant, see §7/§3).

---

## 2. Cheat codes as a RAM map

### 2a. GameCube — `GQNE5D` (CRC32 `AA45D0B6`)

GC codes are shown in "raw" GameShark/AR form. `04xxxxxx yyyyyyyy` = write 32-bit word `yyyyyyyy` to `0x80xxxxxx`; `00xxxxxx 000000yy` = write byte. GC main RAM base is `0x80000000`.

Primary source: [GameHacking.org game 55021](https://gamehacking.org/game/55021), [Ethereal Games GCN AR list](https://etherealgames.com/gcn/m/mortal-kombat-deception/action-replay-codes-us/), [TCRF](https://tcrf.net/Mortal_Kombat:_Deception).

| Address (raw) | GC RAM addr | Width | Meaning | Source |
|---|---|---|---|---|
| `003AE747` | `0x803AE747` | byte | **Player-1 active character ID.** TCRF's "replace P1" codes write this: Nitara `0x27`, Frost `0x29`, Kitana `0x2A`, Drahmin `0x2B`. This is the single most useful address for the tool — read it to announce who P1 is. | [TCRF](https://tcrf.net/Mortal_Kombat:_Deception) |
| `041AD0C0` | `0x801AD0C0` | word | Instruction patch. Code `041AD0C0 41820048` **re-enables the hidden on-screen version/debug string** (disabled by default only on GC). `0x41820048` is a PPC `beq +0x48`; the stock GC build has a branch here that skips the draw. | [TCRF](https://tcrf.net/Mortal_Kombat:_Deception) |
| `040C9BB8` | `0x800C9BB8` | word | `60000000` = PPC `nop`. Part of nolberto82 "Hit Anywhere Both Players" — NOPs a hit-region / range check in the fight code. | [GameHacking 55021](https://gamehacking.org/game/55021) |
| `040B10E0` | `0x800B10E0` | word | `60000000` = `nop`. Same "Hit Anywhere" set. | as above |
| `040B0D38` | `0x800B0D38` | word | `60000000` = `nop`. Same "Hit Anywhere" set. | as above |

Encrypted ARMax codes (need an ARMax device or `ar_crypt`/`omniconvert` to decrypt into the `04…` form above — worth decrypting for the tool, since they contain the real addresses):

| Effect | ARMax (encrypted) | Source |
|---|---|---|
| Master / "Must Be On" | `H6D7-C7JW-ZPHY3` , `1W3Z-V038-8W1TJ` | [Ethereal](https://etherealgames.com/gcn/m/mortal-kombat-deception/action-replay-codes-us/) |
| Max / Infinite Koins | `12NP-NZY4-WDEJR` , `AT50-KD1T-5XUX9` , `KC3Y-UXDX-V01N8` | Ethereal / GH |
| Infinite Round Time | `NP18-TEAN-4FRF9` , `0U85-8D81-WVANR` | Ethereal / GH |
| Everything Unlocked | `UXAT-RDZA-HXXEW` , `0900-5022-NK2U9` , `99YW-9PF1-HYW1Z` | Ethereal / GH |
| P1 Infinite Health | `XHNE-7Z6C-MPM0K` , `ZWJ2-E9FR-NF664` | Ethereal |
| P2 Infinite Health | `YJFB-GZJE-F8CAZ` , `DQQC-EJV7-KG2H9` | Ethereal |
| "P1 Character Modifiers" header | `GF1X-WXMZ-UD15Z` (then one 2-line pair per character) | Ethereal |
| "P2 Character Modifiers" header | `U72Q-KG4V-F163N` | Ethereal |

**Character-ID enum (GameCube), derived from the order of Ethereal's "Player 1: Play As …" list.** Nitara is `0x27` (39), Frost `0x29`, Kitana `0x2A`, Drahmin `0x2B` all check out against TCRF, so ID = 1-based position in this list:

| ID (hex) | Character | ID (hex) | Character |
|---|---|---|---|
| 01 | Jade | 17 | Kenshi |
| 02 | Scorpion | 18 | Sindel |
| 03 | Mileena | 19 | Tanya |
| 04 | Goro *(GC-exclusive)* | 1A | Raiden (dark) |
| 05 | Baraka | 1B | Old Shujinko |
| 06 | Sub-Zero | 1C | Boy Shujinko |
| 07 | Havik | 1D | Noob *(pre-merge)* |
| 08 | Hotaru | 1E | Smoke *(pre-merge)* |
| 09 | Kabal | 1F | Monster |
| 0A | Ermac | 20 | Onaga |
| 0B | Nightwolf | 21 | Jax |
| 0C | Bo' Rai Cho | 22 | Raiden (light) |
| 0D | Noob-Smoke | 23 | Quan Chi |
| 0E | Li Mei | 24 | Kung Lao |
| 0F | Ashrah | 25 | Johnny Cage |
| 10 | Dairou | 26 | Sonya |
| 11 | Shao Kahn *(GC-exclusive)* | 27 | Nitara *(unused in fights)* |
| 12 | Kobra | 28 | Shang Tsung |
| 13 | Darrius | 29 | Frost *(unused)* |
| 14 | Kira | 2A | Kitana *(unused)* |
| 15 | "Ghost" | 2B | Drahmin *(unused)* |
| 16 | Liu Kang | | |

(Treat exact numeric base as "confirm with a memory watch" — the *ordering* is solid, the offset-by-one is inferred.)

### 2b. PS2 — `SLUS-20881`

Source: [GameHacking.org game 104314](https://gamehacking.org/game/104314) (note: that page mislabels the serial as `SLUS-20881` region "USA" — correct), plus [PS2 widescreen cheat collections](https://github.com/PS2-Widescreen/OPL-Widescreen-Cheats).

PS2 published codes are almost all **encrypted** (CodeBreaker v7+ and GameShark v3/v4). To turn them into EE addresses you must run them through `omniconvert` (raw/CB/GS ↔ raw). Raw items found:

| Code (raw) | EE addr | Meaning | Source |
|---|---|---|---|
| `902231BC 0C04620A` | `0x002231BC` | DNAS / online-auth bypass (`.cht` for OPL/CheatDevice, file `SLUS_208.81.cht`) | [PS2 Online Gaming forum](https://ps2onlinegaming.com/viewtopic.php?t=1999) |
| `203F7638 10000540` | `0x003F7638` | DNAS bypass, 2nd line | as above |
| `9838E76D 78D0502A` | (encrypted) | GameShark v3 "[M] Must Be On" (MadCatz) | [GH 104314](https://gamehacking.org/game/104314) |

Encrypted CodeBreaker "everything/character" blocks all share the header
`B4336FA9 4DFEFB79 / 352BA795 CF074F86 / 6F456B84 D6D359A2` then one distinguishing line (`E3956DBB 6FABD13F`, `CCA4623C D9991FFA`, `D9991FFA`, …) — decrypt these to recover the PS2 equivalents of the GC `003AE747` character slot and the unlock flags.

There is a **PS2 widescreen pnach** (`SLUS_208.81` / CRC — game is flagged "widescreen supported natively" + "widescreen patch available" on the [PCSX2 Wiki](https://wiki.pcsx2.net/Mortal_Kombat:_Deception)); the `.pnach` in the PCSX2 `cheats_ws` set contains commented EE addresses for the camera/projection matrices and is a good seed for locating the render/camera struct.

### 2c. Cheat-source index (for follow-up mining)
- gamehacking.org: [GC 55021](https://gamehacking.org/game/55021), [PS2 104314](https://gamehacking.org/game/104314); forum thread on [PAL codes](https://forum.gamehacking.org/forum/video-game-hacking-and-development/retro-hacking/6302-pal-codes-for-mortal-kombat-deception)
- [Ethereal Games GCN AR list](https://etherealgames.com/gcn/m/mortal-kombat-deception/action-replay-codes-us/) — cleanest full "Play As" enumeration
- [MK Secrets — Kodes & Secrets (MKD)](https://mksecrets.net/index.php?section=mkd&lang=eng&contentID=5515) and forum threads: [koins/skip-fight](https://www.mksecrets.net/forums/eng/viewtopic.php?f=95&t=7855), [characters via cheat devices](https://www.mksecrets.net/forums/eng/viewtopic.php?t=6585)
- [Mortal Kombat Online — "AR MAX Codes, And More"](https://www.mortalkombatonline.com/t/classic2/mortal-kombat-deception-ar-max-codes-and-more/54VP4HLnaQpm)
- supercheats / cheatcc / cheathappens / codejunkies (mostly the same ARMax set)

---

## 3. The Cutting Room Floor
<https://tcrf.net/Mortal_Kombat:_Deception> · prerelease: <https://tcrf.net/Prerelease:Mortal_Kombat:_Deception>

### 3a. Development leftovers — the important part for this project

- **`mk6gc_release.elf`** — *"an executable with debug symbols … present inside the root folder from the GameCube release."* (Deadly Alliance's GC disc likewise ships `mk5gc_release.elf` with ~5,864 symbols — [RetroReversing](https://www.retroreversing.com/gamecube-debug-symbols) — which is presumably what the existing Deadly Alliance accessibility tool leaned on.)
- **`mk6gc_release.MAP`** — *"a linker map for the ELF executable … present **only in the GameCube release**."* TCRF hosts it directly: **`MKDeception_LinkerMap.zip` (629 KB)**, linked from the "Linker Map" section of the TCRF page. This is a CodeWarrior link map = **named functions + named global/static symbols + their addresses and sizes** for the exact GC retail build. Parse with [`decomp-toolkit`](https://github.com/encounter/decomp-toolkit) `dtk map`. **This is the single biggest asset for the GC build** — it likely names the menu state machine, the string-table loader, the character/arena select cursors, `get_mode_of_play`, etc., with real addresses.

### 3b. Debug functions
- **On-screen version / debug string.** Game Options → Gameplay, hold **L + Attack 1 ~6 s** → build string bottom-right. Disabled on GC by default; re-enable with AR `041AD0C0 41820048`. Build strings: Xbox `0.098`, PS2 `0.098`, **GC `0.142_gc`**.
- **`pfx_debug`** — a test arena `.ssf` (checkerboard floor, green cube). Its startup script is empty; not normally loadable.
- **`Katakombs.ssf`** — complete ice arena, unreachable because the executable's file table omits it; restorable via `toceditor`/MKDHook.
- No full "debug menu" (level-select / cheat menu) is documented for Deception the way one is for some titles — the debug surface here is the version string + the two test arenas + the leftover script/asset text below.

### 3c. Leftover strings / text (useful for a string-scanner sanity check)

Internal→display name map (in files & code):

| Internal | Display |
|---|---|
| `cassius` | Darrius |
| `freak` | Monster |
| `kollapsing_kliffs` | Falling Cliffs |
| `monk` | Shujinko |
| `netherbelly` | Nethership Interior |
| `skab` | Havik |

- **Placeholder move-list text** shown when playing as an NPC: `STYLE ONE ATTACK ONE`, `STYLE ONE COMBO ONE`, … `SPECIAL MOVES NAME`.
- **Partial script output, GC only** — most characters carry leftover strings like `isc\menu\buttons\gc\eng\buttoncancel.tga not found`, `isc\konquest\eng\outstanding.tga not found` (confirms a `menu/buttons/gc/eng/` and `konquest/eng/` art/string layout with per-language subfolders).
- `permanent_strings.ssf` contains `ACIDBATH` (cut returning arena). `konquest_common.ssf`: `NIS NEEDED`, scrapped item descriptions (`Artifact`, `Cyborg CPU`, `Treasure Note`). `kq_*_fight.ssf`: generic mission placeholder text with `WEAPON1` tokens.
- **Menu sounds `shell_1/2/3`** are leftovers from Deadly Alliance — i.e. the front-end audio bank ("shell") name carried over; the menu system is a direct descendant of DA's "shell."
- **Xbox executable**: RenderWare 3.6 SDK repo-log fragments from `0x39D7C0`; build-date string at `0x39DDE0` = `Core built at May 31 2004 18:49:12`. `MK6BANKS.mmb` (Xbox only) lists early sound banks incl. `announcr_names.msb`, `shell.msb`, `chess.msb`, `puzzle.msb`, `konquest_mk6.msb`.

### 3d. Unused characters (present in files, not in the fight roster)
Drahmin, Frost, Kitana, Nitara — GC "replace P1" AR codes: `003AE747 0000002B / 29 / 2A / 27` respectively. Dairou/Kabal/Kobra have unused *locked* icons (they're unlocked by default in the retail game).

---

## 4. Engine differences from Deadly Alliance that matter for a memory-reading tool

| Area | Deadly Alliance | Deception | Implication |
|---|---|---|---|
| Front-end | "shell" menu system | Same lineage (`shell_*` sounds carried over verbatim), but more top-level items: adds **Chess Kombat, Puzzle Kombat, MK Online, Kontent, Profiles**; Konquest promoted from tutorial to main mode. | A DA menu-hook strategy ports conceptually; item indices/enum values will differ. Expect a "current shell screen" enum + a "cursor index" per screen. |
| Roster / arena / fightstyle tables | Compiled constants in the ELF | **Exported into `.MKO` scripts** (`mkoasm` README: "most executable objects exported into MKO (fightstyle, character, stage data and more)") packed in `.ssf` | The *names* you display may need to come from a string table dumped off-disc rather than from a fixed ELF array. Live "who is selected" is still a small integer in RAM (see `003AE747`). |
| Script variables | none | static + local vars, script→script calls with params | The engine keeps a script VM state; menu logic may partly run in script. `get_mode_of_play` (opcode 178) is a clean "what mode am I in" signal. |
| Strings | data-offset references | **still data-offset references** (ID/hash string vars only arrive in Armageddon) | Good: a one-time string-table dump stays address-stable within a build. |
| FX | mix of exe + script | "FX fully moved to MKO" | Irrelevant to menus, but means less lives in the ELF generally. |
| Konquest | small hub + lesson rooms (Bo' Rai Cho's dojo) | **large free-roam multi-realm adventure** following Shujinko across 6 realms, day/night clock, houses/NPCs, item pickups, Krypt-key drops | Much bigger surface if the tool ever tries to assist Konquest navigation. For a menu/character-select tool it's out of scope; just detect "in Konquest" and stand down. TCRF shows lots of *cut* Konquest content (training-as-yourself, board-breaking task, Bo' Rai Cho intro cutscene). |
| Online / WLS | none | **PS2 + Xbox only**, GameSpy-backed, incl. online Chess/Puzzle; **GC has none**. Shut down 2014-05-31. DNAS/online-auth bypass raw codes exist for PS2 (`0x002231BC`, `0x003F7638`). | For the GC target, ignore entirely. For PS2, an "MK Online" menu item exists but leads nowhere. |
| Build | PS2/Xbox `0.098` (RenderWare 3.6, built 2004-05-31) | GC `0.142_gc` — a **later, more complete** build; balance tweaks, 20 chars unlocked at start, +Goro +Shao Kahn | The GC build is *not* a straight port of the `0.098` code; addresses and even some logic differ from PS2/Xbox. Treat PS2 RE as a hint, not a map, for GC. |

---

## 5. Roster + menu structure (console version)

### 5a. Main menu (top level) — order per the decomp's `General game notes`
`Kombat` (→ Arcade / Versus / Practice) · `Chess Kombat` · `Puzzle Kombat` · `Konquest` · `MK Online` · `The Krypt` · `Kontent` · `Profiles` · `Game Options` (→ Gameplay [Blood Level OFF/LOW/MEDIUM/MAX, default MAX] / Audio / Video / Controller).
(On GC the `MK Online` entry is absent or inert.)

### 5b. Character-select roster **as displayed** — GameCube
From [StrategyWiki](https://strategywiki.org/wiki/Mortal_Kombat:_Deception) (its grid is the GC layout — it includes Goro and Shao Kahn), read left→right, top→bottom:

Row 1: Jade · Kenshi · Scorpion · Mileena · **Goro** · Baraka · Sub-Zero · Sindel · Havik
Row 2: Raiden · Li Mei · Kabal · Ermac · *(centre gap)* · Nightwolf · Bo' Rai Cho · Noob-Smoke · Tanya
Row 3: Shujinko · Hotaru · Ashrah · Dairou · **Shao Kahn** · Kobra · Darrius · Kira · Liu Kang

= 26 playable (24 base + Goro + Shao Kahn). On GC only **6** are locked at start (Kenshi, Raiden, Sindel, Tanya, Liu Kang, Shujinko); Hotaru, Havik, Jade, Kira, Li Mei, Noob-Smoke are **unlocked by default** unlike PS2/Xbox (where those 6 must be unlocked). Shujinko unlocks by beating Konquest; the rest via Krypt koffins (see [MK Secrets](https://mksecrets.net/index.php?section=mkd&lang=eng&contentID=5515)).

PS2/Xbox display roster is the same grid minus Goro and Shao Kahn (the two centre-column slots), 24 characters, 12 locked at start.

### 5c. Arena select
[MKWarehouse arena list](https://www.mortalkombatwarehouse.com/mkd/arenas/) (23 entries incl. the "Death Traps Theater" viewer):
Sky Temple · Nethership Interior · Dark Prison · Beetle Lair · Hell's Foundry · Slaughterhouse · Lower Mines · Golden Desert · Falling Cliffs · Yin Yang Island · Quan Chi's Fortress · Kuatan Palace · Dragon King's Temple · Chamber of Artifacts · Dragon Mountain · The Pit · Living Forest · Nexus · Liu Kang's Tomb · Shang Tsung's Courtyard · Deadpool · Portal.
Stages with Death Traps: Dark Prison, Deadpool, Dragon King's Temple, Falling Cliffs, Golden Desert, Hell's Foundry, Kuatan Palace, Lower Mines, Nexus, The Pit, Quan Chi's Fortress, Sky Temple, Slaughterhouse, Yin Yang Island. Cut arena: **Katakombs** (restorable), plus `ACIDBATH` reference.
Internal arena names seen: `kollapsing_kliffs` = Falling Cliffs, `netherbelly` = Nethership Interior (see §3c).

### 5d. Chess Kombat (unique to Deception)
Turn-based strategy on an 8×... board; you field MK fighters as chess pieces (King/Queen/etc. roles), and captures are resolved by a real fight. Menu has piece-assignment screens (Ability / Player / Description / Fighter text panels — TCRF prerelease notes these panels changed a lot). Was called "Board Game" in early builds. `chess.msb` sound bank.

### 5e. Puzzle Kombat (unique to Deception)
*Super Puzzle Fighter II Turbo*-style falling-block versus, with chibi versions of the roster; winning triggers a mini-fatality animation. Has its own character-select screen (a frame-rate counter is visible on it in prerelease footage → those builds were debug builds). `puzzle.msb`.

### 5f. Konquest
Free-roam single-player adventure as Shujinko (ages: Kid → Teen → Adult → Old), across Earthrealm / Netherrealm / Outworld / Orderrealm / Chaosrealm / Edenia, with an in-world day/night clock that gates events. Primary source of character/arena Krypt-key unlocks. Ends → unlocks Shujinko. (Fandom [Konquest Script](https://mortalkombat.fandom.com/wiki/Mortal_Kombat:_Deception/Konquest_Script).)

### 5g. The Krypt
400 koffins (down from DA's 676), bought with colour-coded koins (Jade/Onyx/Sapphire/Ruby/Gold) earned in fights, or opened with keys found in Konquest. Grid addressing is letter-letter (e.g. "Koffin ON", "Koffin SJ"). Contents: characters, arenas, alt costumes, concept art, videos, music. GC krypt layout differs slightly from PS2/Xbox.

---

## 6. Existing accessibility work for MK: Deception

**None found for Deception specifically, on any platform.** Searches of AppleVis, audiogames.net, Sightless Kombat, GitHub, and general web turned up nothing.

Context:
- The brief's own premise — that a finished talking-menu tool exists for **Deadly Alliance** (same engine) — is the only known prior art, and is the natural template. DA's GC disc shipping `mk5gc_release.elf` with ~5,864 debug symbols ([RetroReversing](https://www.retroreversing.com/gamecube-debug-symbols)) is almost certainly why DA was tractable; **Deception's GC disc ships the same *plus* a full linker `.MAP`**, so it should be at least as tractable.
- AFB *AccessWorld* ran a history piece, ["Accessibility in Mortal Kombat: The Early Years to Mortal Kombat (2011)"](https://afb.org/aw/fall2025/mortal-kombat-accessibility-1) (Dmitriy Lazarev, Fall 2025). On the 3D-era games it only observes: voiced intros/endings help with story, but *"the 'Krypt' … hid unlockable characters and stages behind visual menus, and the 'Konquest' role-playing modes … created obstacles that blind players could not easily overcome."* Stereo positioning and per-character voice/announcer cues are the only "incidental" accessibility. No tool, no formal options.
- Official screen-reader / TTS menu support in the franchise starts with **MK1 (2023)** / retroactively discussed for MK11 — decades later, unrelated engine.

---

## 7. Emulation notes

### 7a. GameCube `GQNE5D` on Dolphin
[Dolphin Wiki](https://wiki.dolphin-emu.org/index.php?title=Mortal_Kombat:_Deception) — **compatibility rating 5/5 "Perfect."** No listed "Problems."
- Enhancement quirk: at IR > 1×, character shadows get rectangular artifacts / black outlines on the floor — fix by setting **Scaled EFB Copy = Off** or Internal Resolution = Native. Especially visible in Konquest.
- Old testing note (Dolphin 4.0-4803, 2014): a Konquest autosave at the end of the Netherrealm segment could corrupt the profile; not reproduced on 4.0-5078+. Advice on record: **don't rely on savestates** in Konquest.
- 16:9 Gecko code (NA) is published on the wiki (patches projection at `C21DDE54` / `C21DDE6C` and constants around `04256388`/`04256530`) — again a useful seed for the camera/matrix struct if the tool ever needs render state.
- **Debug symbols**: Dolphin's wiki tags this title under ["Ships with Debugging Symbols"](https://wiki.dolphin-emu.org/index.php?title=Ships_with_Debugging_Symbols). Dolphin can load a matching `.map` from `User/Maps/GQNE5D.map` and populate its Symbols view / code/mem breakpoints — i.e. drop the TCRF `mk6gc_release.MAP` (reformatted) there and you get named functions in Dolphin's debugger for free. Dolphin also has scripting (Lua via forks / the newer scripting branch) and a wide memory-watch / AR-code engine for a runtime tool.

### 7b. PS2 `SLUS-20881` on PCSX2
[PCSX2 Wiki](https://wiki.pcsx2.net/Mortal_Kombat:_Deception) — **Playable** (NTSC-U and PAL).
- Known GS quirk: right edge of the screen is distorted with hardware-renderer upscaling/"scaling" — looks perfect in **software** mode or at native.
- "Widescreen supported natively" + a widescreen **pnach** exists in the PCSX2 `cheats_ws` collection (contains commented EE addresses for camera/projection). PS2 game CRC `43341C03` is listed for PAL; NTSC-U CRC differs (used as the pnach filename).
- `.cht`/pnach convention: filename `SLUS_208.81.*`. DNAS bypass `.cht` content: `902231BC 0C04620A` / `203F7638 10000540`.
- MKDHook targets `SLUS20881` under a **PCSX2 "fork with plugins" + extended-RAM** build ([download link in the blog post](https://ermaccer.github.io/posts/mkdhook/)); its in-game menu is keyboard/pad driven and its camera keys are hardcoded keyboard inputs.
- Emulator-side scripting for a runtime tool: PCSX2 has Lua only via old forks; more practical is its pnach engine + `PINE`/IPC (read EE memory from an external process). Or use the [`debugging-games`](https://archive.org/details/debugging-games) torrent's symbol set if a PS2 symbol file is present (none confirmed for Deception PS2 — the symbol'd build is GC).

### 7c. Xbox
Runs on xemu / original-Xbox homebrew; executable is the `0.098` RenderWare build with the repo-log/build-date strings (§3c). No special notes. Least useful of the three (no symbols, oldest build).

### 7d. Redump / disc identity
- GC: [redump disc 9171](http://redump.org/disc/9171/) — serial `DL-DOL-GQNE-USA`, internal name "Mortal Kombat Deception", internal serial `GQNE5D`.
- The [`debugging-games`](https://archive.org/details/debugging-games) Internet Archive item ("Symbols, Symbols Everywhere!") is a torrent bundle of symbol'd builds; the GC MK Deception + MK Deadly Alliance symbol'd executables are the kind of thing it collects.

---

## 8. Bottom line for feasibility

**Strongly favourable for the GameCube target.**

1. The GC retail build (`GQNE5D`, `0.142_gc`) ships **both** a debug-symbol ELF (`mk6gc_release.elf`) **and** a full CodeWarrior linker map (`mk6gc_release.MAP`, downloadable from TCRF, 629 KB). Named functions + named globals + addresses for the exact retail build — the same class of asset that made the Deadly Alliance tool possible, and then some.
2. Dolphin runs it perfectly and natively supports loading that `.map` into its debugger + has a mature memory/AR/watch engine.
3. A concrete, high-value RAM anchor is already published: **`0x803AE747` = P1 character ID** (byte), with a decoded character enum.
4. The menu system is a documented descendant of Deadly Alliance's "shell" (same sound-bank names), and the top-level tree is confirmed.
5. Roster / arena / style data moved into `.MKO` scripts, but strings are still offset-referenced (stable), and ermaccer's `mkoasm` + `SSFExplorer` can dump every script and string table off the disc.
6. The complications are all *avoidable*: Konquest is large and free-roam (detect-and-stand-down), online is dead / GC-absent (ignore), Chess/Puzzle have their own select screens (separate handling), and PS2/Xbox are an *older* codebase so their RE only loosely transfers to GC.

Recommended first steps: (a) pull `MKDeception_LinkerMap.zip` from TCRF and run `dtk map` over it; (b) load it into Dolphin as `GQNE5D.map`; (c) watch `0x803AE747` and the shell-screen/cursor globals the map names; (d) dump the `.ssf`/`.MKO` string tables with SSFExplorer + mkoasm for the display-name lists.

### Key links
- Decomp: <https://github.com/cScarletter/MK-3D-Era-Decompilation>
- mkoasm (+ `data/mkd_def.txt`): <https://github.com/ermaccer/mkoasm>
- SSFExplorer: <https://github.com/ermaccer/SSFExplorer> · PAKTool: <https://github.com/ermaccer/MortalKombat.PAKTool> · Tools: <https://github.com/ermaccer/MortalKombat.Tools>
- MKDHook (PS2): <https://ermaccer.github.io/posts/mkdhook/>
- TCRF: <https://tcrf.net/Mortal_Kombat:_Deception> (linker map download is in the "Development Leftovers" section)
- Dolphin: <https://wiki.dolphin-emu.org/index.php?title=Mortal_Kombat:_Deception> · GC symbol list: <https://www.retroreversing.com/gamecube-debug-symbols>
- PCSX2: <https://wiki.pcsx2.net/Mortal_Kombat:_Deception>
- Cheats: <https://gamehacking.org/game/55021> (GC) · <https://gamehacking.org/game/104314> (PS2) · <https://etherealgames.com/gcn/m/mortal-kombat-deception/action-replay-codes-us/>
- Roster/arenas: <https://strategywiki.org/wiki/Mortal_Kombat:_Deception> · <https://www.mortalkombatwarehouse.com/mkd/arenas/>
- Accessibility history: <https://afb.org/aw/fall2025/mortal-kombat-accessibility-1>
