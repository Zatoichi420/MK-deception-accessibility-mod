"""MK: Deception (GameCube, GQNE5D, USA) — addresses & label tables.

All addresses are live GameCube virtual addresses, read straight from the symbol
table of `mk6gc_release.elf` on the disc (unstripped, 25,669 symbols) plus the
`mk6gc_release.MAP` linker map, and confirmed by disassembling the game's own
menu / character-select functions. See docs/research/deception-static-analysis.md.

Re-derive for another region with tools/gc_extract.py + tools/ppcdis.py — the
symbol NAMES are identical across regions, only the numbers move.
"""

GAME_ID = "GQNE5D"

# small-data bases (r13 / r2) for this build, from the ELF
SDA_BASE  = 0x80517840
SDA2_BASE = 0x805197a0

# ---- main menu ----------------------------------------------------------
# Deception's front-end is the data-driven "mkScreenEngine". The choice list and
# which item is highlighted are held as mkGameVariables ints:
#   menu_mode_var       — which menu screen is active
#   menu_mode_sub_var   — highlighted item index within it   (CONFIRM live: see CALIBRATION)
MENU_MODE_VAR      = 0x80510e44   # u32 - active menu screen
MENU_MODE_SUB_VAR  = 0x80510e48   # u32 - highlighted item index
ARENA_SUB_MENU_VAR = 0x80510e54   # u32 - arena-select sub-menu cursor
MAIN_MENU_TIMEOUT  = 0x80510d48   # main_menu_timeout_ticks
DO_MAIN_MENU_TIMEOUT = 0x80510d4c
MENU_PLAYER        = 0x80510d30
TARGET_GAME_MODE   = 0x80510d34

# menu_string_matrix @ 0x8034fbc0 — 6 char* : the top-level menu choices, in order
MAIN_MENU_STRINGS = 0x8034fbc0
MAIN_MENU_LABELS = ["Arcade", "Puzzle Kombat", "Konquest", "MK Chess", "Versus", "Go Online"]

# ---- character select -------------------------------------------------
# pselect_get_player_name(p) reads p1_selbox_pos / p2_selbox_pos (0..0x2b), then:
#   entry = pselect_char_tbl[slot]           (stride 0x28)   [pz table if pselect_mode==2]
#   char_id = entry[0]
#   name    = *(global_player_data + char_id*0x10)           (offset 0 = name string ptr)
P1_SELBOX_POS = 0x8051082c   # u32 - P1 hovered roster slot
P2_SELBOX_POS = 0x80510828
PSELECT_MODE  = 0x80510834   # u32 - 2 == Puzzle Kombat select (uses the pz roster table)
F_ARENA_SELECT_ACTIVE = 0x805107f8

PSELECT_CHAR_TBL     = 0x8033e65c   # normal roster, stride 0x28, [0] = char id
PSELECT_PZ_CHAR_TBL  = 0x8033ea94   # Puzzle Kombat roster, stride 0x28
PSELECT_CHAR_STRIDE  = 0x28
GLOBAL_PLAYER_DATA   = 0x8033c408   # stride 0x10, [0] = name string ptr, indexed by char id
GLOBAL_PLAYER_STRIDE = 0x10
SELBOX_MAX = 0x2c                   # bound checked in pselect_get_player_name

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
