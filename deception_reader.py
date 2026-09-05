#!/usr/bin/env python3
"""MK: Deception (GameCube) talking-menu daemon.  Windows / macOS / Linux.

Reads the running game's RAM through RetroArch's UDP command interface and speaks
the highlighted menu item / hovered fighter. Reads only; never writes to the game.

    python deception_reader.py             # run the daemon
    python deception_reader.py --probe     # live raw state, no speech
    python deception_reader.py --once      # one snapshot, exit

Env: MK_RA_HOST (127.0.0.1), MK_RA_PORT (55355), MK_VOICE, MK_RATE_WPM, MK_SPEAK_BACKEND.
Requires in retroarch.cfg:  network_cmd_enable = "true"

Sister project: github.com/Zatoichi420/mortal-kombat-deadly-alliance-accessibility
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from ra_client import RAClient, RetroArchError
import deception_addrs as A
from speak import Speaker

POLL_HZ = 12
SETTLE_S = 0.10

def read_cstring(ra: RAClient, addr: int, maxlen: int = 48) -> str:
    if not (0x80003000 <= addr < 0x81800000):
        return ""
    raw = ra.read_memory(addr, maxlen)
    nul = raw.find(b"\0")
    if nul >= 0:
        raw = raw[:nul]
    return raw.decode("latin1", "replace").strip()

class Ctx:
    IDLE = "idle"
    MENU = "menu"
    CHARSELECT = "charselect"

class DeceptionReader:
    def __init__(self, ra: RAClient, speaker: Speaker | None = None):
        self.ra = ra
        self.say = speaker or Speaker()
        self._last_key = None
        self._pending = None
        self._pending_since = 0.0
        self._last_ctx = None
        self._roster_cache: dict[int, str] = {}
        self._region_warned = False

    # -- game detection --------------------------------------------------

    def is_target_game(self) -> bool:
        try:
            st = self.ra.status()
        except RetroArchError:
            return False
        if st.get("state") != "PLAYING":
            return False
        sysname = (st.get("system") or "").lower()
        if sysname and not any(k in sysname for k in ("gc", "gamecube", "cube")):
            return False
        try:
            disc = self.ra.read_memory(0x80000000, 6)
        except RetroArchError:
            return False
        if disc == b"GQNE5D":
            return True
        if disc in (b"GQNP5D", b"GQND5D", b"GQNJ5D"):
            if not self._region_warned:
                print(f"note: non-USA build ({disc.decode('latin1')}); addresses are USA "
                      "(GQNE5D) and may be wrong.", flush=True)
                self._region_warned = True
            return True
        return False

    # -- roster --------------------------------------------------------

    def _roster_name(self, slot: int, pz: bool = False) -> str:
        key = (slot, pz)
        if key in self._roster_cache:
            return self._roster_cache[key]
        name = ""
        if A.ROSTER_FROM_MEMORY and 0 <= slot < A.SELBOX_MAX:
            try:
                tbl = A.PSELECT_PZ_CHAR_TBL if pz else A.PSELECT_CHAR_TBL
                cid = self.ra.read_u32(tbl + slot * A.PSELECT_CHAR_STRIDE)
                if 0 <= cid < 64:
                    namep = self.ra.read_u32(A.GLOBAL_PLAYER_DATA + cid * A.GLOBAL_PLAYER_STRIDE)
                    name = read_cstring(self.ra, namep, 24).title()
            except RetroArchError:
                name = ""
        if not name and not pz and 0 <= slot < len(A.ROSTER):
            name = A.ROSTER[slot]
        if not name:
            name = f"slot {slot}"
        self._roster_cache[key] = name
        return name

    # -- snapshot ----------------------------------------------------

    def snapshot(self) -> dict:
        r = self.ra
        s = {
            "menu_mode": r.read_u32(A.MENU_MODE_VAR),
            "menu_sub": r.read_u32(A.MENU_MODE_SUB_VAR),
            "arena_sub": r.read_u32(A.ARENA_SUB_MENU_VAR),
            "pselect_mode": r.read_u32(A.PSELECT_MODE),
            "p1_selbox": r.read_u32(A.P1_SELBOX_POS),
            "p2_selbox": r.read_u32(A.P2_SELBOX_POS),
            "arena_active": r.read_u32(A.F_ARENA_SELECT_ACTIVE),
            "mode_of_play": r.read_u32(A.MODE_OF_PLAY),
        }
        return s

    # -- classify + narrate ---------------------------------------

    def _classify(self, s: dict) -> str:
        if s["pselect_mode"] and 0 <= s["p1_selbox"] < A.SELBOX_MAX:
            return Ctx.CHARSELECT
        # main menu: a small stable sub-index and not in a match
        if s["mode_of_play"] in (0, 8) and 0 <= s["menu_sub"] < len(A.MAIN_MENU_LABELS):
            return Ctx.MENU
        return Ctx.IDLE

    def _menu_utt(self, s: dict):
        i = s["menu_sub"]
        n = len(A.MAIN_MENU_LABELS)
        label = A.MAIN_MENU_LABELS[i] if 0 <= i < n else f"item {i + 1}"
        try:
            p = self.ra.read_u32(A.MAIN_MENU_STRINGS + i * 4)
            live = read_cstring(self.ra, p, 24)
            if live:
                label = live
        except RetroArchError:
            pass
        return ("menu", i, label), f"{label}, {i + 1} of {n}", "Main menu"

    def _cs_utt(self, s: dict):
        pz = s["pselect_mode"] == 2
        parts, kb = [], ["cs"]
        for pnum, pos in ((1, s["p1_selbox"]), (2, s["p2_selbox"])):
            if 0 <= pos < A.SELBOX_MAX:
                parts.append(f"Player {pnum}: {self._roster_name(pos, pz)}")
                kb.append((pnum, pos))
        if not parts:
            return None
        return tuple(kb), " . ".join(parts), "Character select"

    def narrate(self, s: dict):
        ctx = self._classify(s)
        now = time.monotonic()
        if ctx != self._last_ctx:
            self._last_ctx = ctx
            if ctx == Ctx.CHARSELECT:
                self.say.say("Character select")
            elif ctx == Ctx.MENU:
                self.say.say("Main menu")
            self._last_key = self._pending = None

        u = self._menu_utt(s) if ctx == Ctx.MENU else self._cs_utt(s) if ctx == Ctx.CHARSELECT else None
        if u is None:
            return
        key, text, _ = u
        if key == self._last_key:
            return
        if key != self._pending:
            self._pending, self._pending_since = key, now
            return
        if now - self._pending_since >= SETTLE_S:
            self.say.say(text)
            self._last_key, self._pending = key, None

    def run(self):
        period = 1.0 / POLL_HZ
        waited = False
        while True:
            try:
                if not self.is_target_game():
                    if not waited:
                        print("waiting for MK: Deception to be running...", flush=True)
                        waited = True
                    time.sleep(1.5)
                    continue
                waited = False
                self.narrate(self.snapshot())
            except RetroArchError as e:
                print(f"(retro) {e}", flush=True)
                time.sleep(0.7)
            except KeyboardInterrupt:
                return
            time.sleep(period)

def _fmt(s: dict) -> str:
    return (f"menu_mode={s['menu_mode']} menu_sub={s['menu_sub']} arena_sub={s['arena_sub']} "
            f"| pselect_mode={s['pselect_mode']} p1_selbox={s['p1_selbox']} p2_selbox={s['p2_selbox']} "
            f"arena_active={s['arena_active']} mode_of_play={s['mode_of_play']}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--host", default=os.environ.get("MK_RA_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MK_RA_PORT", "55355")))
    args = ap.parse_args()

    ra = RAClient(cmd_host=args.host, cmd_port=args.port)
    if args.once or args.probe:
        try:
            print("RetroArch:", ra.version(), ra.status(), flush=True)
        except RetroArchError as e:
            print(f"cannot reach RetroArch on {args.host}:{args.port}: {e}", file=sys.stderr)
            sys.exit(1)
        dr = DeceptionReader(ra)
        while True:
            try:
                print(_fmt(dr.snapshot()), flush=True)
            except RetroArchError as e:
                print(f"(retro) {e}", flush=True)
            if args.once:
                return
            time.sleep(0.25)

    print(f"mk-deception talking-menu daemon: watching RetroArch on {args.host}:{args.port}", flush=True)
    DeceptionReader(ra).run()

if __name__ == "__main__":
    main()
