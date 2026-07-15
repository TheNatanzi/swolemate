#!/usr/bin/env python3
# montage.py — stitch a person's 1..10 tiers into one evolution strip (2 rows x 5),
# FORCING every character to the same height: detect the character vs the flat
# background, scale so its height is uniform, and align all feet to a common line.
# Usage: python montage.py <name> <style> <generated_dir>
import sys, os
import numpy as np
from PIL import Image

name, style, gen = sys.argv[1], sys.argv[2], sys.argv[3]
files = [os.path.join(gen, f"{name}-{style}-{i:02d}.png") for i in range(1, 11)]

TARGET_H = 300     # uniform character height (px)
PAD = 14

def norm_char(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    bg = a[3, 3]                                  # sample the flat corner background
    dist = np.abs(a - bg).sum(axis=2)
    ys, xs = np.where(dist > 45)                  # non-background = the character
    if len(ys) == 0:
        w = int(im.width * TARGET_H / im.height)
        return im.resize((w, TARGET_H), Image.NEAREST), tuple(int(v) for v in bg)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    char = im.crop((x0, y0, x1 + 1, y1 + 1))
    w = max(1, int(char.width * TARGET_H / char.height))
    return char.resize((w, TARGET_H), Image.NEAREST), tuple(int(v) for v in bg)

chars = [norm_char(f) for f in files]
bg = chars[0][1]
cw = max(c.width for c, _ in chars) + PAD * 2
cols, rows, CH = 5, 2, TARGET_H + PAD * 2
W, H = cols * cw, rows * CH
sheet = Image.new("RGB", (W, H), bg)
for idx, (char, _) in enumerate(chars):
    r, c = divmod(idx, cols)
    x = c * cw + (cw - char.width) // 2
    y = r * CH + PAD                              # all TARGET_H tall -> feet align per row
    sheet.paste(char, (x, y))
out = os.path.join(gen, f"{name}-{style}-SCALE.png")
sheet.save(out)
print("OK", out, f"{W}x{H}")
