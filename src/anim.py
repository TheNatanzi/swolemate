#!/usr/bin/env python3
# anim.py — REAL 3-frame action GIFs per level. Each frame is a fresh edit of the level's
# approved anchor art, so face/body/outfit/background stay locked and ONLY the action pose
# changes. Then 3 frames are padded to a shared canvas (bottom-aligned) and saved as a GIF.
#   gen   <name> <tiers>   -> generate the 3 action frames per tier  (COSTS $ — Gemini)
#   build <name> <tiers>   -> assemble GIFs from frames on disk       (free, local)
# Global canvas = max across ALL *-fN.png present, so every GIF is identical size.
import sys, os, json, base64, glob, urllib.request, urllib.error
from PIL import Image

URL  = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
STYLE, SRC, MS = "pixel", "generated", 150

GENDER = {"medi": "M", "teyaum": "M", "gizem": "F", "rinad": "F"}

# Per-tier 3-beat action loop (pose deltas only — position/scale/framing stay identical).
MOTION = {
 1:  ["holding a greasy burger up near the mouth, cheeks resting",
      "taking a HUGE bite of the burger, mouth stretched wide open, cheeks bulging",
      "chewing with puffed-out cheeks, eyes half-closed in gross bliss"],
 2:  ["lifting the giant soda bottle toward the lips",
      "head tilted way back CHUGGING the soda, throat gulping, eyes bulging",
      "lowering the bottle, cheeks puffed in a big satisfied burp"],
 3:  ["grabbing a big fistful of fries from the carton",
      "cramming the whole fistful of fries INTO the wide-open mouth",
      "chewing the mouthful of fries, cheeks stuffed full"],
 4:  ["holding the donut up, glum grumpy frown",
      "taking a reluctant sighing bite of the donut, eyes drooping",
      "chewing the donut slowly with a sad sulking face"],
 5:  ["standing relaxed, arm down at the side",
      "raising a hand in a big friendly WAVE, bright smile",
      "hand halfway down mid-wave, still smiling"],
 6:  ["giving a confident single thumbs-up",
      "giving an energetic DOUBLE thumbs-up with a wink and grin",
      "back to a single thumbs-up, smiling"],
 7:  ["both arms up in a biceps flex pose",
      "PUMPING the flex harder — biceps bulging bigger, teeth gritted, veins popping",
      "easing the flex slightly, cocky smirk behind the sunglasses"],
 8:  ["holding the loaded barbell racked at the shoulders",
      "PRESSING the barbell straight up overhead, arms fully extended, straining",
      "lowering the barbell back down toward the shoulders"],
 9:  ["gripping the giant barbell low near the knees, back set",
      "HEAVING the deadlift up toward lockout, whole body straining, veins bursting, steam blasting",
      "controlling the barbell back down a bit, still roaring"],
 10: ["fists clenched at the sides, charging up, small golden aura, hair beginning to rise",
      "EXPLOSIVE full power-up — massive blazing golden aura and crackling lightning, spiky hair flared straight up, screaming, ground cracking",
      "aura pulsing at medium size, still powered up and roaring"],
}

def guard(name, i):
    m = (" Her athletic top stays fully INTACT and covers her chest — never rips, never shows breasts/nipples/cleavage."
         if GENDER.get(name) == "F" else "")
    return ("This EXACT pixel-art character. Keep the FACE, identity, hair, skin tone, the outfit's BASE COLOR, "
            "body shape/size, HEIGHT, standing position, camera distance/scale and the flat lavender background "
            "completely IDENTICAL to the reference — do not redraw or shift them." + m +
            " This is frame " + str(i) + " of a 3-frame loop of the SAME action. Change ONLY this pose: ")

def call(img, prompt):
    payload = {"prompt": prompt, "image_base64": base64.b64encode(img).decode(), "mime": "image/png"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=180); d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return None, "HTTP %s %s" % (e.code, e.read()[:160].decode(errors="replace"))
    except Exception as e:
        return None, repr(e)
    if not d.get("ok"): return None, json.dumps({k: v for k, v in d.items() if k != "raw"})[:200]
    return base64.b64decode(d["image_base64"]), None

def gen(name, tiers):
    for t in tiers:
        anchor_p = os.path.join(SRC, f"{name}-{STYLE}-{t:02d}.png")
        if not os.path.exists(anchor_p): print(f"{name} L{t}: no anchor"); continue
        anchor = open(anchor_p, "rb").read()
        for i, pose in enumerate(MOTION[t], 1):
            out = os.path.join(SRC, f"{name}-{STYLE}-L{t:02d}-f{i}.png")
            if os.path.exists(out) and os.path.getsize(out) > 1000:
                print(f"skip {name} L{t} f{i} (exists)", flush=True); continue
            img, err = call(anchor, guard(name, i) + pose + ". Keep everything else pixel-identical.")
            if err: print(f"{name} L{t} f{i} FAIL {err}"); continue
            open(out, "wb").write(img); print(f"OK {name} L{t} f{i}", flush=True)

def gsize():
    fs = glob.glob(os.path.join(SRC, f"*-{STYLE}-L[0-9][0-9]-f[0-9].png"))
    sz = [Image.open(p).size for p in fs]
    return (max(w for w, h in sz), max(h for w, h in sz)) if sz else (0, 0)

def build(name, tiers, gw=0, gh=0):
    if not gw: gw, gh = gsize()
    for t in tiers:
        fp = [os.path.join(SRC, f"{name}-{STYLE}-L{t:02d}-f{i}.png") for i in (1, 2, 3)]
        if not all(os.path.exists(p) for p in fp): print(f"{name} L{t}: missing frames"); continue
        frames = []
        for p in fp:
            im = Image.open(p).convert("RGBA"); bg = im.getpixel((2, 2))
            c = Image.new("RGBA", (gw, gh), bg)
            c.alpha_composite(im, ((gw - im.width) // 2, gh - im.height))
            frames.append(c.convert("P", palette=Image.ADAPTIVE, colors=256))
        out = os.path.join(SRC, f"{name}-{STYLE}-L{t:02d}.gif")
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=MS, loop=0, disposal=2, optimize=True)
        print(f"OK {os.path.basename(out)} {gw}x{gh} {os.path.getsize(out)//1024}KB")

cmd, name = sys.argv[1], sys.argv[2]
tiers = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else list(range(1, 11))
if cmd == "gen":   gen(name, tiers)
elif cmd == "build": build(name, tiers)
