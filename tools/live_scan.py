#!/usr/bin/env python3
"""Snapshot-and-diff RAM scanner for a pairing calibration session.

You navigate MK: Deception on a real controller. Between steps the operator runs
`snap`; afterwards `find` reports every 32-bit word whose value across the
snapshots looks like a menu cursor (small ints, moving by +/-1, i.e. 0,1,2,3...).

    python3 live_scan.py snap 0            # you are on menu item 0
    python3 live_scan.py snap 1            # ... after pressing Down once
    ...
    python3 live_scan.py find              # analyse all snaps in this set
    python3 live_scan.py find --exact 0,1,2,3,4   # require this exact sequence
    python3 live_scan.py reset             # delete the set and start over

    --wide   also sweep a big .bss chunk + low MEM1 heap (slower snap, ~45 s)
    --set X  name the snapshot set (default "menu"); use a fresh name per screen

Reads only; sends nothing to the game.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ra_client import RAClient, RetroArchError

SCAN_DIR = os.path.expanduser("~/mkda-work/deception/scan")
CHUNK = 0x300

DEFAULT = [
    (0x8050F840, 0x1800),   # .sdata / .sbss  (mode_of_play, menu_mode_*, selbox, ...)
    (0x805117A0, 0x1000),   # .sdata2 tail
    (0x803A9560, 0x6000),   # start of .bss
    (0x8033B000, 0x2000),   # menu_slots / *_smm / pselect tables (.data)
    (0x8050A000, 0x5000),   # .bss tail near the menu vars
]
WIDE_EXTRA = [
    (0x803B0000, 0x60000),
    (0x80600000, 0xA0000),
]


def regions(wide):
    return list(DEFAULT) + (WIDE_EXTRA if wide else [])


def grab(ra, regs):
    out = {}
    for base, length in regs:
        blob = bytearray()
        for off in range(0, length, CHUNK):
            n = min(CHUNK, length - off)
            try:
                blob += ra.read_memory(base + off, n)
            except RetroArchError:
                blob += b"\0" * n
        for i in range(0, len(blob) - 3, 4):
            out[base + i] = int.from_bytes(blob[i:i + 4], "big")
    return out


def save(path, words):
    with open(path, "wb") as f:
        for a in sorted(words):
            f.write(struct.pack(">II", a, words[a] & 0xFFFFFFFF))


def load(path):
    d = {}
    raw = open(path, "rb").read()
    for i in range(0, len(raw), 8):
        a, v = struct.unpack(">II", raw[i:i + 8])
        d[a] = v
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snap", "find", "reset", "list"])
    ap.add_argument("n", nargs="?", help="snapshot number (for snap)")
    ap.add_argument("--set", default="menu")
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--exact", help="comma list, e.g. 0,1,2,3")
    ap.add_argument("--host", default=os.environ.get("MK_RA_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MK_RA_PORT", "55355")))
    args = ap.parse_args()

    d = os.path.join(SCAN_DIR, args.set)
    os.makedirs(d, exist_ok=True)

    if args.cmd == "reset":
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        print(f"cleared set {args.set!r}")
        return

    if args.cmd == "list":
        print(sorted(os.listdir(d)))
        return

    if args.cmd == "snap":
        ra = RAClient(cmd_host=args.host, cmd_port=args.port)
        try:
            st = ra.status()
        except RetroArchError as e:
            sys.exit(f"cannot reach RetroArch: {e}")
        regs = regions(args.wide)
        t0 = time.time()
        w = grab(ra, regs)
        p = os.path.join(d, f"{int(args.n):03d}.bin")
        save(p, w)
        # also capture a few named vars for context
        ctx = {}
        for nm, a in (("mode_of_play", 0x80510224), ("menu_mode", 0x80510e44),
                      ("menu_sub", 0x80510e48), ("p1_selbox", 0x8051082c),
                      ("p2_selbox", 0x80510828), ("pselect_mode", 0x80510834),
                      ("arena_focus", 0x80510e4c), ("arena_sub", 0x80510e54)):
            try:
                ctx[nm] = ra.read_u32(a)
            except RetroArchError:
                ctx[nm] = "?"
        print(f"snap {args.n} -> {p}  ({len(w)} words, {time.time()-t0:.1f}s)  "
              f"{st.get('game','?')}  ctx={ctx}")
        return

    # find
    snaps = sorted(f for f in os.listdir(d) if f.endswith(".bin"))
    if len(snaps) < 2:
        sys.exit("need at least 2 snaps")
    seqs = [load(os.path.join(d, s)) for s in snaps]
    common = set(seqs[0])
    for s in seqs[1:]:
        common &= set(s)
    exact = [int(x) for x in args.exact.split(",")] if args.exact else None
    hits = []
    for a in common:
        vals = [s[a] for s in seqs]
        if exact is not None:
            if vals == exact:
                hits.append((99, a, vals))
            continue
        if len(set(vals)) < 2 or not all(0 <= v < 64 for v in vals):
            continue
        deltas = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
        score = sum(1 for x in deltas if x in (0, 1, -1))
        if score >= max(2, len(deltas) - 1):
            hits.append((score, a, vals))
    hits.sort(reverse=True)
    print(f"{len(snaps)} snaps, {len(common)} common words")
    for score, a, vals in hits[:25]:
        print(f"  {a:#010x}  score {score}/{len(seqs)-1}  {vals}")
    if not hits:
        print("  nothing matched — try --wide, or a different navigation")


if __name__ == "__main__":
    main()
