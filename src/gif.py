#!/usr/bin/env python3
# gif.py — build an animated evolution GIF for one person from their 10 pixel frames.
# Cycles tier 1..10 (fat -> buff -> super saiyan) then loops. Frames padded to a common
# canvas, bottom-aligned so the character stands on the same ground line.
# Usage: python gif.py <name> [style=pixel] [src_dir=generated] [ms_per_frame=500]
import sys, os
from PIL import Image

name  = sys.argv[1]
style = sys.argv[2] if len(sys.argv) > 2 else "pixel"
src   = sys.argv[3] if len(sys.argv) > 3 else "generated"
ms    = int(sys.argv[4]) if len(sys.argv) > 4 else 500

tiers = list(range(1, 11))
paths = [os.path.join(src, f"{name}-{style}-{t:02d}.png") for t in tiers]
imgs  = [Image.open(p).convert("RGBA") for p in paths if os.path.exists(p)]
if len(imgs) < 2:
    print("need at least 2 frames, found", len(imgs)); sys.exit(1)

W = max(i.width for i in imgs)
H = max(i.height for i in imgs)

def bg_color(im):                      # sample top-left corner as the flat background
    return im.getpixel((2, 2))

frames = []
for im in imgs:
    canvas = Image.new("RGBA", (W, H), bg_color(im))
    x = (W - im.width) // 2            # center horizontally
    y = H - im.height                  # bottom-align (feet on ground line)
    canvas.alpha_composite(im, (x, y))
    frames.append(canvas.convert("P", palette=Image.ADAPTIVE, colors=256))

out = os.path.join(src, f"{name}-{style}-EVOLVE.gif")
frames[0].save(out, save_all=True, append_images=frames[1:],
               duration=ms, loop=0, disposal=2, optimize=True)
kb = os.path.getsize(out) // 1024
print(f"OK {out} {W}x{H} {len(frames)}f {kb}KB")
