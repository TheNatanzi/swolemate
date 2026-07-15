#!/usr/bin/env python3
# uniform_gifs.py — rebuild all 80 ladder GIFs at ONE uniform canvas (440x616, 5:7).
# Each frame: blur-stretched cover of itself as underlay (dimmed) + the full frame fit-centered on top.
# No subject cropping, no hard bars, no AI cost. Frames (-f1..f3 pngs) are untouched source of truth.
import os, glob
from PIL import Image, ImageFilter, ImageEnhance
SRC = "generated"; TW, THh, MS = 440, 616, 150
PEOPLE = ["medi", "teyaum", "gizem", "rinad"]

import statistics
def edge_uniform(im, side, strip=4, thresh=18):
    """Is this border strip near-uniform in color? (so plain extension is seamless)"""
    w, h = im.size
    box = {"L": (0, 0, strip, h), "R": (w - strip, 0, w, h), "T": (0, 0, w, strip), "B": (0, h - strip, w, h)}[side]
    px = list(im.crop(box).getdata())
    return all(statistics.pstdev([p[c] for p in px]) < thresh for c in (0, 1, 2))

def blur_under(im):
    s = max(TW / im.width, THh / im.height)
    big = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (big.width - TW) // 2; y = (big.height - THh) // 2
    under = big.crop((x, y, x + TW, y + THh)).filter(ImageFilter.GaussianBlur(16))
    return ImageEnhance.Brightness(under).enhance(0.62)

def uniform_frame(im, flat_ok=False):
    im = im.convert("RGB")
    f = min(TW / im.width, THh / im.height)
    fg = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
    padx, pady = TW - fg.width, THh - fg.height
    # flat-background sets: EXTEND the border color (seamless) when the touched edges are uniform
    if flat_ok:
        need = (["L", "R"] if padx > 0 else []) + (["T", "B"] if pady > 0 else [])
        if all(edge_uniform(fg, s) for s in need):
            canvas = Image.new("RGB", (TW, THh))
            x0, y0 = padx // 2, pady // 2
            canvas.paste(fg, (x0, y0))
            if padx > 0:  # stretch 1px edge columns outward (handles gradients row-by-row)
                lcol = fg.crop((0, 0, 1, fg.height)).resize((x0, fg.height))
                rcol = fg.crop((fg.width - 1, 0, fg.width, fg.height)).resize((TW - x0 - fg.width, fg.height))
                canvas.paste(lcol, (0, y0)); canvas.paste(rcol, (x0 + fg.width, y0))
            if pady > 0:
                trow = fg.crop((0, 0, fg.width, 1)).resize((fg.width, y0)) if y0 > 0 else None
                brow = fg.crop((0, fg.height - 1, fg.width, fg.height)).resize((fg.width, THh - y0 - fg.height))
                if trow: canvas.paste(trow, (x0, 0))
                canvas.paste(brow, (x0, y0 + fg.height))
            return canvas
    under = blur_under(im)
    under.paste(fg, (padx // 2, pady // 2))
    return under

built = 0; bad = []
for tag in ("got", "pixel"):
    for name in PEOPLE:
        for t in range(1, 11):
            fp = [os.path.join(SRC, f"{name}-{tag}-L{t:02d}-f{i}.png") for i in (1, 2, 3)]
            if not all(os.path.exists(x) for x in fp):
                bad.append(f"{name}-{tag}-L{t:02d}"); continue
            frames = [uniform_frame(Image.open(x), flat_ok=(tag == "pixel")) for x in fp]
            q = [fr.convert("P", palette=Image.ADAPTIVE, colors=256) for fr in frames]
            out = os.path.join(SRC, f"{name}-{tag}-L{t:02d}.gif")
            q[0].save(out, save_all=True, append_images=q[1:], duration=MS, loop=0, disposal=2, optimize=True)
            built += 1
print("built", built, "gifs; missing:", bad or "none")
# verify uniformity
sizes = {Image.open(p).size for p in glob.glob(os.path.join(SRC, "*-got-L[0-9][0-9].gif")) + glob.glob(os.path.join(SRC, "*-pixel-L[0-9][0-9].gif"))}
print("unique sizes:", sizes)
# proof sheet: one frame from each person/aspect extreme, both sets
row = Image.new("RGB", (4 * 230, 340), (10, 8, 14))
for j, (n, tag, lvl) in enumerate([("medi","got",5),("gizem","got",5),("teyaum","pixel",8),("rinad","pixel",3)]):
    im = Image.open(os.path.join(SRC, f"{n}-{tag}-L{lvl:02d}.gif")).convert("RGB").resize((230, 322))
    row.paste(im, (j * 230, 9))
row.save(os.path.join(SRC, "UNIFORM-proof.png"))
print("proof sheet saved")
