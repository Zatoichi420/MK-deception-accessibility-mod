---
name: Region calibration data
about: Addresses for a non-USA disc (PAL / German / Japan)
title: "[region] "
labels: calibration
---

**Region / disc id** (PAL GQNP5D / German GQND5D / Japan GQNJ5D)

**How you got the addresses**
<!-- Recommended: extract mk6gc_release.elf from that disc and read its symbol
     table (docs/CALIBRATION.md). Symbol names are identical across regions. -->

**Addresses** (paste the lines from `deception_addrs.py` that differ)
```python
MENU_MODE_VAR      = 0x...
MENU_MODE_SUB_VAR  = 0x...
MAIN_MENU_STRINGS  = 0x...
P1_SELBOX_POS      = 0x...
P2_SELBOX_POS      = 0x...
PSELECT_CHAR_TBL   = 0x...
GLOBAL_PLAYER_DATA = 0x...
```

**Verified?**
- [ ] Menu narration checked live
- [ ] Character select checked live
