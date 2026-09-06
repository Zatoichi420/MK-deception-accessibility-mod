#!/usr/bin/env python3
"""Continuously log the active screen-proc + menu/select vars to a file.

Start it, then navigate the game freely at your own pace for as long as you
like. Every time the screen-proc or a watched cursor changes it appends a line
(resolved against the .MAP). Ctrl-C or `stop` to finish; then read the file.

    python3 proc_log.py            # -> ~/mkda-work/deception/proc_log.txt
    python3 proc_log.py --secs 600

Reads only; sends nothing to the game.
"""
from __future__ import annotations
import argparse, bisect, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ra_client import RAClient, RetroArchError

MAP = os.path.expanduser("~/mkda-work/deception/mk6gc_release.MAP")
OUT = os.path.expanduser("~/mkda-work/deception/proc_log.txt")


def load_syms():
    syms = []
    if not os.path.exists(MAP):
        return syms
    for ln in open(MAP, errors="replace"):
        p = ln.split()
        if len(p) >= 6 and len(p[2]) == 8:
            try:
                syms.append((int(p[2], 16), p[5]))
            except ValueError:
                pass
    syms.sort()
    return syms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=900.0)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    syms = load_syms()
    addrs = [a for a, _ in syms]

    def name_of(addr):
        i = bisect.bisect_right(addrs, addr) - 1
        if 0 <= i < len(syms):
            a, n = syms[i]
            return n if addr == a else f"{n}+{addr - a:#x}"
        return "?"

    ra = RAClient()
    watch = {
        "proc":      0x80510204,
        "menu_mode": 0x80510e44,
        "menu_sub":  0x80510e48,
        "p1_selbox": 0x8051082c,
        "p2_selbox": 0x80510828,
        "pselect_m": 0x80510834,
        "arena_act": 0x805107f8,
        "arena_foc": 0x80510e4c,
        "arena_sub": 0x80510e54,
        "mode_play": 0x80510224,
    }
    f = open(args.out, "w")
    f.write(f"# proc_log start {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.flush()
    print(f"logging to {args.out} — navigate freely, Ctrl-C when done", flush=True)

    prev = {}
    t0 = time.time()
    try:
        while time.time() - t0 < args.secs:
            try:
                cur = {k: ra.read_u32(a) for k, a in watch.items()}
            except RetroArchError:
                time.sleep(0.3)
                continue
            if cur != prev:
                t = time.time() - t0
                pn = name_of(cur["proc"])
                line = (f"t={t:7.1f}  proc={cur['proc']:#010x} {pn:34} "
                        f"mm={cur['menu_mode']:<4} ms={cur['menu_sub']:<3} "
                        f"p1={cur['p1_selbox']:<3} p2={cur['p2_selbox']:<3} "
                        f"psm={cur['pselect_m']:<2} arena={cur['arena_act']} "
                        f"af={cur['arena_foc']} asub={cur['arena_sub']} mop={cur['mode_play']}")
                print(line, flush=True)
                f.write(line + "\n")
                f.flush()
                prev = cur
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    f.write(f"# end {time.strftime('%H:%M:%S')}\n")
    f.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
