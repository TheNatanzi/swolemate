#!/usr/bin/env python3
# bob_gifs.py — one small animated GIF PER LEVEL per person (a gentle 3-frame idle bounce).
# All GIFs share ONE global canvas size so every level of every person is identical dimensions.
# 3 frames: rest -> hop up -> rest, looping fast for a lively pixel-game idle. $0 (local only).
# Usage:
#   python bob_gifs.py all                 -> build all people, tiers 1..10
#   python bob_gifs.py <name> [tiers]      -> e.g. medi "1,5,10"  (still uses global size)
import sys, os, glob
from PIL import Image

STYLE, SRC, MS = "pixel", "generated", 120     # MS per frame (fast)
PEOPLE = ["medi", "teyaum", "gizem", "rinad"]

# --- global canvas from EVERY frame on disk, so all outputs match exactly ---
allf = glob.glob(os.path.join(SRC, f"*-{STYLE}-[0-9][0-9].png"))
sizes = [Image.open(p).size for p in allf]
GW = max(w for w, h in sizes)
GH = max(h for w, h in sizes)
BOB = max(10, GH // 45)                          # hop height in px
CW, CH = GW, GH + BOB                             # extra headroom so the hop never clips

def corner(im): return im.getpixel((2, 2))

def build(name, tier):
    p = os.path.join(SRC, f"{name}-{STYLE}-{tier:02d}.png")
    if not os.path.exists(p): return None
    im = Image.open(p).convert("RGBA")
    bg = corner(im)
    x = (CW - im.width) // 2
    base_y = CH - im.height                       # bottom-aligned (feet on ground)
    offsets = [0, -BOB, 0]                         # rest, hop up, rest
    frames = []
    for dy in offsets:
        c = Image.new("RGBA", (CW, CH), bg)
        c.alpha_composite(im, (x, base_y + dy))
        frames.append(c.convert("P", palette=Image.ADAPTIVE, colors=256))
    out = os.path.join(SRC, f"{name}-{STYLE}-L{tier:02d}.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=MS, loop=0, disposal=2, optimize=True)
    return out, os.path.getsize(out) // 1024

arg = sys.argv[1] if len(sys.argv) > 1 else "all"
if arg == "all":
    names, tiers = PEOPLE, list(range(1, 11))
else:
    names = [arg]
    tiers = [int(t) for t in sys.argv[2].split(",")] if len(sys.argv) > 2 else list(range(1, 11))

print(f"canvas {CW}x{CH}  bob {BOB}px  {MS}ms/frame")
n = 0
for name in names:
    for t in tiers:
        r = build(name, t)
        if r: print(f"OK {os.path.basename(r[0])} {r[1]}KB"); n += 1
print(f"-- {n} gifs")
