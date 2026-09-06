#!/usr/bin/env python3
"""Continuously poll the candidate menu-context words and log every change.

Run it, then drive the game by hand for ~60 s (press Down over and over on the
main menu, let it wrap). Every time a watched word changes value it prints a
line with a timestamp. That shows directly whether `menu_mode` (or any other
word) is the menu cursor.

    python3 live_watch.py            # 60 s, default watch list
    python3 live_watch.py 90         # run for 90 s
    python3 live_watch.py 60 --range 0x80510e00 0x100   # also watch a raw range

Reads only; sends nothing to the game.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ra_client import RAClient, RetroArchError

NAMED = [
    ("mode_of_play",   0x80510224),
    ("menu_mode",      0x80510e44),
    ("menu_sub",       0x80510e48),
    ("arena_focus",    0x80510e4c),
    ("menu_e50",       0x80510e50),
    ("arena_sub",      0x80510e54),
    ("menu_e58",       0x80510e58),
    ("menu_e5c",       0x80510e5c),
    ("menu_e60",       0x80510e60),
    ("menu_e64",       0x80510e64),
    ("p1_selbox",      0x8051082c),
    ("p2_selbox",      0x80510828),
    ("pselect_mode",   0x80510834),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("secs", nargs="?", type=float, default=60.0)
    ap.add_argument("--range", nargs=2, metavar=("BASE", "LEN"), action="append",
                    default=[], help="also watch a raw address range (repeatable), "
                    "e.g. --range 0x80510e00 0x100 --range 0x805107f8 0x80")
    ap.add_argument("--host", default=os.environ.get("MK_RA_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MK_RA_PORT", "55355")))
    args = ap.parse_args()

    ra = RAClient(cmd_host=args.host, cmd_port=args.port)
    try:
        ra.status()
    except RetroArchError as e:
        sys.exit(f"cannot reach RetroArch: {e}")

    watch = list(NAMED)
    rngs = []
    for b, l in args.range:
        base, ln = int(b, 0), int(l, 0)
        rngs.append((base, ln))
        for off in range(0, ln, 4):
            watch.append((f"{base + off:#010x}", base + off))

    def read_all():
        vals = {}
        for base, ln in rngs:
            for chunk in range(0, ln, 0x200):
                n = min(0x200, ln - chunk)
                try:
                    blob = ra.read_memory(base + chunk, n)
                    for off in range(0, n - 3, 4):
                        vals[base + chunk + off] = int.from_bytes(blob[off:off + 4], "big")
                except RetroArchError:
                    pass
        for nm, a in NAMED:
            if a not in vals:
                try:
                    vals[a] = ra.read_u32(a)
                except RetroArchError:
                    vals[a] = None
        return vals

    name_of = {a: nm for nm, a in watch}
    prev = read_all()
    t0 = time.monotonic()
    print(f"watching {len(prev)} words for {args.secs:.0f}s — press Down repeatedly now")
    print("t=0.00  " + "  ".join(f"{name_of.get(a,hex(a))}={v}" for a, v in sorted(prev.items())
                                 if name_of.get(a, "").startswith(("menu_mode", "menu_sub", "mode_of"))))
    changes = {}
    while time.monotonic() - t0 < args.secs:
        cur = read_all()
        t = time.monotonic() - t0
        for a, v in cur.items():
            if a in prev and v != prev[a] and v is not None and prev[a] is not None:
                nm = name_of.get(a, hex(a))
                print(f"t={t:5.2f}  {nm:<16} {prev[a]:>10} -> {v}")
                changes[a] = changes.get(a, 0) + 1
        prev = cur
        time.sleep(0.03)

    print("\n--- summary (change count per word) ---")
    for a, c in sorted(changes.items(), key=lambda kv: -kv[1]):
        print(f"  {name_of.get(a, hex(a)):<16} {c} changes   (final {prev[a]})")


if __name__ == "__main__":
    main()
