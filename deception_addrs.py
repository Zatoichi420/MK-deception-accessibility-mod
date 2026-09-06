"""MK: Deception (GameCube, GQNE5D, USA) — addresses & label tables.

All addresses are live GameCube virtual addresses, read straight from the symbol
table of `mk6gc_release.elf` on the disc (unstripped, 25,669 symbols) plus the
`mk6gc_release.MAP` linker map, and confirmed by disassembling the game's own
menu / character-select functions. See docs/research/deception-static-analysis.md.

Re-derive for another region with tools/gc_extract.py + tools/ppcdis.py — the
symbol NAMES are identical across regions, only the numbers move.
"""

GAME_ID = "GQNE5D"

# ---- current-screen procedure ----------------------------------------
# main.o keeps a pointer to the active screen's proc function at
# func_addr$283 (0x80510204). Reading it and matching against these addresses
# (from the .MAP, symbol `p_*`) is the most reliable "what screen am I on"
# signal — far better than mode_of_play, which reuses small ints across screens.
# VERIFIED LIVE 2026-09-05: arcade character select -> 0x80089fdc = p_pselect.
SCREEN_PROC_PTR = 0x80510204
P_MAIN_MENU     = 0x801ad820
P_GAME_OPTIONS  = 0x801ad198
P_PAUSE_MENU    = 0x801ad2d0
P_PSELECT       = 0x80089fdc   # character select — arcade AND versus
P_PZ_PSELECT    = 0x80089d3c   # Puzzle Kombat character select
P_BG_PSELECT    = 0x80089a74   # Konquest / background fight select
P_KONQUEST_PAUSE = 0x801800d0
P_ATTRACT_MODE  = 0x8007f258
SCREEN_PROC_NAMES = {
    P_MAIN_MENU: "Main menu", P_GAME_OPTIONS: "Game Options",
    P_PAUSE_MENU: "Pause menu", P_PSELECT: "Character select",
    P_PZ_PSELECT: "Puzzle Kombat character select",
    P_BG_PSELECT: "Character select", P_ATTRACT_MODE: "Attract mode",
}

# small-data bases (r13 / r2) for this build, from the ELF
SDA_BASE  = 0x80517840
SDA2_BASE = 0x805197a0

# ---- main menu ----------------------------------------------------------
# Deception's front-end is the data-driven "mkScreenEngine". menu_mode_var is a
# screen-engine global (bound in mwScreenEngineGlue.o SetGlobal/GetGlobal, the
# switch at 0x801c1ee8 / 0x801c2404 — the Deception equivalent of MK:DA's
# mkGameVariables). On the TOP-LEVEL menu it holds the highlighted item as an
# enum, NOT a 0-based index. VERIFIED LIVE 2026-09-05 by a hand-driven Down-walk:
# the value stepped 1,2,3,4,6,7,8,9 and wrapped 9->1 (enum 5 = "Online" is hidden
# on the GameCube build, so it is skipped). Screen contents confirmed by OCR:
#   KOMBAT / CHESS KOMBAT / PUZZLE KOMBAT / KONQUEST / THE KRYPT / KONTENT /
#   PROFILES / OPTIONS   (8 rows).
MENU_MODE_VAR      = 0x80510e44   # u32 - highlighted top-menu item (enum, see MAIN_MENU_BY_MODE)
MENU_MODE_SUB_VAR  = 0x80510e48   # u32 - sub-item index (submenus); 0 on the top menu
ARENA_FOCUS_VAR    = 0x80510e4c   # u32 - arena-select focus
ARENA_SUB_MENU_VAR = 0x80510e54   # u32 - arena-select sub-menu cursor
POPUP_TYPE         = 0x80510e60   # u32 - screen-engine popup id (0 = none)
PAUSE_PLAYER       = 0x80510e3c
MAIN_MENU_TIMEOUT  = 0x80510d48   # main_menu_timeout_ticks
DO_MAIN_MENU_TIMEOUT = 0x80510d4c
MENU_PLAYER        = 0x80510d30
TARGET_GAME_MODE   = 0x80510d34

# menu_mode_var value -> label on the top-level menu. Navigation order is the
# sorted key order: Kombat, Chess Kombat, Puzzle Kombat, Konquest, The Krypt,
# Kontent, Profiles, Game Options  (8 items; 5 "Online" never shown on GameCube).
MAIN_MENU_BY_MODE = {
    1: "Kombat",
    2: "Chess Kombat",
    3: "Puzzle Kombat",
    4: "Konquest",
    5: "Online",          # hidden on GameCube
    6: "The Krypt",
    7: "Kontent",
    8: "Profiles",
    9: "Game Options",
}
MAIN_MENU_NAV_ORDER = [1, 2, 3, 4, 6, 7, 8, 9]   # visible items, top -> bottom
MODE_OF_PLAY_MAIN_MENU = 13   # mode_of_play == 13 while the top-level menu is up

# menu_string_matrix @ 0x8034fbc0 — 6 char* : the play-mode names (Arcade / Puzzle
# Kombat / Konquest / MK Chess / Versus / Go Online), used by the Kombat submenu,
# NOT the top-level menu. Kept for the submenu pass.
MAIN_MENU_STRINGS = 0x8034fbc0
PLAY_MODE_LABELS = ["Arcade", "Puzzle Kombat", "Konquest", "MK Chess", "Versus", "Go Online"]

# ---- character select -------------------------------------------------
# pselect_get_player_name(p) reads p1_selbox_pos / p2_selbox_pos, then:
#   entry = pselect_char_tbl[slot]           (stride 0x28)   [pz table if pselect_mode==2]
#   char_id = entry[0]
#   name    = *(global_player_data + char_id*0x10)           (offset 0 = name string ptr)
#
# VERIFIED LIVE 2026-09-05 (hand-driven Right-sweep):
#  * screen is active when  mode_of_play == 9  and  pselect_mode == 1   (normal / Versus)
#                    or     mode_of_play == 6  and  pselect_mode == 2   (Puzzle Kombat)
#  * the cursor is a GRID slot, not a flat index. Rows are 7 wide with a stride
#    of 9: usable slots 1..7, 10..16, 19..25, 28..34; the 8/9/17/18/... gaps are
#    never landed on. Right wraps within the row (7 -> 1, 16 -> 10, 25 -> 19).
#  * pselect_char_tbl[slot] resolves correctly at the raw slot value: e.g.
#    slot 5 -> BARAKA, slot 22 -> SHAO KAHN, slot 15 -> BO' RAI CHO. (verified)
#  * selbox values persist stale after leaving the screen — gate on mode_of_play.
P1_SELBOX_POS = 0x8051082c   # u32 - P1 hovered grid slot
P2_SELBOX_POS = 0x80510828   # u32 - P2 hovered grid slot
PSELECT_MODE  = 0x80510834   # u32 - 1 == normal char select, 2 == Puzzle Kombat select
F_ARENA_SELECT_ACTIVE = 0x805107f8
SCREEN_OBJ_PTR = 0x80510204  # ptr to the active screen object (changes per screen)

MODE_OF_PLAY_PSELECT     = 9   # mode_of_play during normal / Versus character select
MODE_OF_PLAY_PSELECT_PZ  = 6   # mode_of_play during Puzzle Kombat character select

PSELECT_CHAR_TBL     = 0x8033e65c   # normal roster, stride 0x28, [0] = char id
PSELECT_PZ_CHAR_TBL  = 0x8033ea94   # Puzzle Kombat roster, stride 0x28
PSELECT_CHAR_STRIDE  = 0x28
PSELECT_GRID_SLOTS   = [s for row in (1, 10, 19, 28) for s in range(row, row + 7)]
GLOBAL_PLAYER_DATA   = 0x8033c408   # stride 0x10, [0] = name string ptr, indexed by char id
GLOBAL_PLAYER_STRIDE = 0x10
SELBOX_MAX = 0x2c                   # bound checked in pselect_get_player_name

# slot -> name, resolved live 2026-09-05 (normal roster, this save's unlocks):
PSELECT_SLOT_NAMES = {
    0: "Kenshi", 1: "Jade", 2: "Scorpion", 3: "Mileena", 4: "Goro", 5: "Baraka",
    6: "Sub-Zero", 7: "Havik",
    10: "Hotaru", 11: "Kabal", 12: "Ermac", 13: "Random", 14: "Nightwolf",
    15: "Bo' Rai Cho", 16: "Noob-Smoke",
    19: "Li Mei", 20: "Ashrah", 21: "Dairou", 22: "Shao Kahn", 23: "Kobra",
    24: "Darrius", 25: "Kira",
}

# On-screen roster order (verified by resolving pselect_char_tbl -> global_player_data):
ROSTER = [
    "Kenshi", "Jade", "Scorpion", "Mileena", "Goro", "Baraka", "Sub-Zero", "Havik",
    "Sindel", "Raiden", "Hotaru", "Kabal", "Ermac", "Random", "Nightwolf",
    "Bo' Rai Cho", "Noob-Smoke", "Tanya", "Shujinko", "Li Mei", "Ashrah", "Dairou",
    "Shao Kahn", "Kobra", "Darrius", "Kira", "Liu Kang",
]
ROSTER_FROM_MEMORY = True   # prefer dereferencing the tables live (order-proof)

# ---- pause menu ------------------------------------------------------
# get_pause_menu_name() / p_pause_menu — resolve at runtime; not yet wired.

# ---- misc -----------------------------------------------------------
MODE_OF_PLAY = 0x80510224
PLAYER_KODE_DIGIT = 0x80510de4       # kode / name-entry current digit
