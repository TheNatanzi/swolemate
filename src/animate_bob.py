#!/usr/bin/env python3
# animate_bob.py — turn a static avatar into a looping "idle bob" sticker.
# Free, local (Pillow + imageio/ffmpeg). Outputs a GIF (preview) + MP4 (WhatsApp).
# Usage: python animate_bob.py <input.png> <out.gif> <out.mp4>
import sys, math
from PIL import Image
import imageio.v2 as imageio

inp, out_gif, out_mp4 = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(inp).convert("RGB")

W = 420                                          # even width (libx264 needs even dims)
h = int(im.height * W / im.width)
im = im.resize((W, h), Image.NEAREST)            # keep pixel edges crisp
bg = im.getpixel((2, 2))
A = max(5, h // 36)                              # bob amplitude
CH = h + 2 * A
CH += CH % 2                                     # force even height
N = 14
frames = []
for t in range(N):
    ph = 2 * math.pi * t / N
    dy = round(A * math.sin(ph))                 # vertical bob
    sq = 1 + 0.012 * math.cos(ph)                # subtle breathing squash/stretch
    fh = int(h * sq)
    fim = im.resize((W, fh), Image.NEAREST)
    canvas = Image.new("RGB", (W, CH), bg)
    canvas.paste(fim, (0, (CH - fh) // 2 + dy))
    frames.append(canvas)

frames[0].save(out_gif, save_all=True, append_images=frames[1:], duration=80, loop=0, disposal=2, optimize=True)
imageio.mimsave(out_mp4, frames, fps=12, codec="libx264", macro_block_size=1, quality=8)
print("OK", out_gif, out_mp4, f"{W}x{CH}")
