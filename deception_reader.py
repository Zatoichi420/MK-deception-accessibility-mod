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

POLL_HZ = 30
SETTLE_S = 0.05          # floor between spoken lines; cursor moves interrupt anyway
TARGET_RECHECK_S = 5.0
FASTPATH_MAX = 8         # consecutive polls before forcing a full re-classify snapshot

_KEEP_CAPS = {"MK", "CPU", "TV", "AI", "HP"}


def read_cstring(ra: RAClient, addr: int, maxlen: int = 48) -> str:
    if not (0x80003000 <= addr < 0x81800000):
        return ""
    raw = ra.read_memory(addr, maxlen)
    nul = raw.find(b"\0")
    if nul >= 0:
        raw = raw[:nul]
    return raw.decode("latin1", "replace").strip()


def prettify(label: str) -> str:
    """Title-case for TTS without mangling all-caps words we want kept."""
    out = []
    for w in label.split():
        if w.upper() in _KEEP_CAPS:
            out.append(w.upper())
        elif w.isupper() and w.isalpha():
            out.append(w.capitalize())
        else:
            out.append(w)
    return " ".join(out)


class Ctx:
    IDLE = "idle"
    MENU = "menu"
    CHARSELECT = "charselect"


class DeceptionReader:
    def __init__(self, ra: RAClient, speaker: Speaker | None = None):
        self.ra = ra
        self.say = speaker or Speaker()
        self._last_key = None
        self._last_ctx = None
        self._ctx_candidate = None
        self._ctx_streak = 0
        self._last_say_at = -1e9
        self._roster_cache: dict[tuple, str] = {}
        self._region_warned = False
        self._target_ok = False
        self._target_checked_at = -1e9
        self._last_snap: dict | None = None
        self._fast_count = 0

    # -- game detection --------------------------------------------------

    def is_target_game(self) -> bool:
        now = time.monotonic()
        if self._target_ok and now - self._target_checked_at < TARGET_RECHECK_S:
            return True
        self._target_checked_at = now
        self._target_ok = False
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
            self._target_ok = True
            return True
        if disc in (b"GQNP5D", b"GQND5D", b"GQNJ5D", b"GQNF5D", b"GQNI5D"):
            if not self._region_warned:
                print(f"note: non-USA build ({disc.decode('latin1')}); addresses are USA "
                      "(GQNE5D) and may be wrong.", flush=True)
                self._region_warned = True
            self._target_ok = True
            return True
        return False

    # -- roster --------------------------------------------------------

    def _roster_name(self, slot: int, pz: bool = False) -> str:
        key = (slot, pz)
        if key in self._roster_cache:
            return self._roster_cache[key]
        name = ""
        if not pz:
            name = A.PSELECT_SLOT_NAMES.get(slot, "")
        if not name and 0 <= slot < A.SELBOX_MAX:
            try:
                tbl = A.PSELECT_PZ_CHAR_TBL if pz else A.PSELECT_CHAR_TBL
                cid = self.ra.read_u32(tbl + slot * A.PSELECT_CHAR_STRIDE)
                if 0 <= cid < 64:
                    namep = self.ra.read_u32(
                        A.GLOBAL_PLAYER_DATA + cid * A.GLOBAL_PLAYER_STRIDE)
                    name = prettify(read_cstring(self.ra, namep, 24))
            except RetroArchError:
                name = ""
        if not name and not pz and 0 <= slot < len(A.ROSTER):
            name = A.ROSTER[slot]
        if not name:
            name = f"slot {slot}"
        self._roster_cache[key] = name
        return name

    # -- snapshot ----------------------------------------------------

    _CS_PROCS = (A.P_PSELECT, A.P_PZ_PSELECT, A.P_BG_PSELECT)

    def snapshot(self) -> dict:
        """RetroArch handles ~1 command per emulated frame (~16 ms), so read in a
        few blocks, not one call per variable. The screen is identified by the
        active screen-proc pointer (func_addr$283); once known, the fast path
        reads just that pointer + the one block whose values change as you move
        the cursor (2 reads/poll). Every FASTPATH_MAX polls we take the full read
        so nothing is missed."""
        r = self.ra
        prev = self._last_snap
        ctx = self._last_ctx

        proc = r.read_u32(A.SCREEN_PROC_PTR)

        if prev is not None and self._fast_count < FASTPATH_MAX:
            if ctx == Ctx.MENU and proc == A.P_MAIN_MENU:
                b = r.read_memory(A.MENU_MODE_VAR, 8)
                self._fast_count += 1
                s = dict(prev, screen_proc=proc,
                         menu_mode=int.from_bytes(b[0:4], "big"),
                         menu_sub=int.from_bytes(b[4:8], "big"))
                self._last_snap = s
                return s
            if ctx == Ctx.CHARSELECT and proc in self._CS_PROCS:
                a = r.read_memory(0x80510820, 24)
                self._fast_count += 1
                s = dict(prev, screen_proc=proc,
                         p1_selbox=int.from_bytes(a[0x0c:0x10], "big"),
                         p2_selbox=int.from_bytes(a[0x08:0x0c], "big"),
                         pselect_mode=int.from_bytes(a[0x14:0x18], "big"),
                         arena_active=int.from_bytes(a[0x00:0x04], "big"))
                self._last_snap = s
                return s

        self._fast_count = 0
        b = r.read_memory(A.MENU_MODE_VAR, 8)
        a = r.read_memory(0x805107f8, 64)     # f_arena_select_active .. pselect_mode + more

        def ua(addr):
            o = addr - 0x805107f8
            return int.from_bytes(a[o:o + 4], "big")

        s = {
            "screen_proc": proc,
            "menu_mode": int.from_bytes(b[0:4], "big"),
            "menu_sub": int.from_bytes(b[4:8], "big"),
            "pselect_mode": ua(A.PSELECT_MODE),
            "p1_selbox": ua(A.P1_SELBOX_POS),
            "p2_selbox": ua(A.P2_SELBOX_POS),
            "arena_active": ua(A.F_ARENA_SELECT_ACTIVE),
        }
        self._last_snap = s
        return s

    # -- classify + narrate ---------------------------------------

    def _classify(self, s: dict) -> str:
        proc = s.get("screen_proc")
        if proc in self._CS_PROCS:
            return Ctx.CHARSELECT
        if proc == A.P_MAIN_MENU and s["menu_mode"] in A.MAIN_MENU_BY_MODE:
            return Ctx.MENU
        return Ctx.IDLE

    def _menu_utt(self, s: dict):
        mode = s["menu_mode"]
        label = A.MAIN_MENU_BY_MODE.get(mode, f"item {mode}")
        try:
            pos = A.MAIN_MENU_NAV_ORDER.index(mode) + 1
            n = len(A.MAIN_MENU_NAV_ORDER)
            where = f"{label}, {pos} of {n}"
        except ValueError:
            where = label
        return ("menu", mode), where

    def _cs_utt(self, s: dict):
        if s.get("arena_active"):
            # picking a stage, not a fighter — arena-name lookup isn't wired yet
            return ("arena",), "Arena select"
        pz = s.get("screen_proc") == A.P_PZ_PSELECT
        parts, kb = [], ["cs"]
        for pnum, pos in ((1, s["p1_selbox"]), (2, s["p2_selbox"])):
            if 0 <= pos < A.SELBOX_MAX:
                parts.append(f"Player {pnum}: {self._roster_name(pos, pz)}")
                kb.append((pnum, pos))
        if not parts:
            return None
        return tuple(kb), " . ".join(parts)

    def _speak(self, text: str, prefix: str | None):
        now = time.monotonic()
        if prefix:
            text = f"{prefix}. {text}"
        elif now - self._last_say_at < SETTLE_S:
            return
        self.say.say(text)
        self._last_say_at = now

    def narrate(self, s: dict):
        raw_ctx = self._classify(s)

        # a new non-idle context must hold for two polls before we act on it
        if raw_ctx == self._ctx_candidate:
            self._ctx_streak += 1
        else:
            self._ctx_candidate, self._ctx_streak = raw_ctx, 1
        if raw_ctx == Ctx.IDLE or self._ctx_streak >= 2:
            ctx = raw_ctx
        else:
            return

        ctx_changed = ctx != self._last_ctx
        if ctx_changed:
            self._last_ctx = ctx
            self._last_key = None

        if ctx == Ctx.MENU:
            u = self._menu_utt(s)
        elif ctx == Ctx.CHARSELECT:
            u = self._cs_utt(s)
        else:
            return
        if u is None:
            return
        key, text = u
        if key == self._last_key:
            return
        self._last_key = key

        prefix = None
        if ctx_changed:
            prefix = {Ctx.MENU: "Main menu", Ctx.CHARSELECT: "Character select"}[ctx]
        self._speak(text, prefix)

    def run(self):
        period = 1.0 / POLL_HZ
        waited = False
        while True:
            t0 = time.monotonic()
            try:
                if not self.is_target_game():
                    if not waited:
                        print("waiting for MK: Deception to be running...", flush=True)
                        waited = True
                    self._last_snap = None
                    time.sleep(1.5)
                    continue
                waited = False
                self.narrate(self.snapshot())
            except RetroArchError as e:
                print(f"(retro) {e}", flush=True)
                self._target_ok = False
                self._last_snap = None
                time.sleep(0.7)
            except KeyboardInterrupt:
                return
            time.sleep(max(0.0, period - (time.monotonic() - t0)))


def _fmt(s: dict) -> str:
    proc = s.get("screen_proc", 0)
    name = A.SCREEN_PROC_NAMES.get(proc, "?")
    return (f"proc={proc:#010x}({name}) menu_mode={s['menu_mode']} menu_sub={s['menu_sub']} "
            f"| pselect_mode={s['pselect_mode']} p1_selbox={s['p1_selbox']} "
            f"p2_selbox={s['p2_selbox']} arena_active={s['arena_active']}")


def _autostart(action: str) -> int:
    """--install / --uninstall / --status: register this daemon (the downloaded
    binary or this script) with the OS's per-user service manager. Kept in its
    own module so the hot path never imports it."""
    import autostart
    try:
        fn = {"install": autostart.install,
              "uninstall": autostart.uninstall,
              "status": autostart.status}[action]
        print(fn(), flush=True)
        return 0
    except autostart.AutostartError as e:
        print(f"autostart {action} failed: {e}", file=sys.stderr)
        return 1


def main():
    ap = argparse.ArgumentParser(
        description="MK: Deception talking-menu daemon (reads only; never writes).")
    ap.add_argument("--probe", action="store_true", help="print live state, no speech")
    ap.add_argument("--once", action="store_true", help="one snapshot, then exit")
    ap.add_argument("--install", dest="autostart_action", action="store_const",
                    const="install", help="run automatically in the background at login")
    ap.add_argument("--uninstall", dest="autostart_action", action="store_const",
                    const="uninstall", help="undo --install")
    ap.add_argument("--status", dest="autostart_action", action="store_const",
                    const="status", help="is the background service installed?")
    ap.add_argument("--host", default=os.environ.get("MK_RA_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MK_RA_PORT", "55355")))
    args = ap.parse_args()

    if args.autostart_action:
        sys.exit(_autostart(args.autostart_action))

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

    print(f"mk-deception talking-menu daemon: watching RetroArch on {args.host}:{args.port}",
          flush=True)
    DeceptionReader(ra).run()


if __name__ == "__main__":
    main()
