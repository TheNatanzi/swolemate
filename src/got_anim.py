#!/usr/bin/env python3
# got_anim.py — REAL 3-frame action GIFs for the Game of Thrones weekly-streak set.
# Each frame is a fresh edit of the level's approved anchor (<name>-got-L##.png) with a guard
# prompt that locks face/body/outfit/background/height/scale/camera so ONLY the pose changes.
# Robust: retry each frame up to RETRIES, up to PASSES passes, skip-existing (retries never re-bill).
# Then assemble 3-frame GIFs (bottom-aligned on one shared canvas, downscaled to WhatsApp size),
# and finally print coverage counts + build a proof contact-sheet per person.
# One-shot:  python got_anim.py         (gen all + build all + verify)
import os, json, base64, glob, time, urllib.request, urllib.error
from PIL import Image

URL  = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC = "generated"
PEOPLE = ["medi", "teyaum", "gizem", "rinad"]
GENDER = {"medi": "M", "teyaum": "M", "gizem": "F", "rinad": "F"}
RETRIES, PASSES = 4, 5
OUT_W, MS = 420, 150   # GIF width, ms per frame

# Per-level 3-beat action loop (pose deltas ONLY — figure stays in the same spot & scale).
MOTION = {
 1:  ["holding the wooden bowl of gruel at the waist, staring into it miserably",
      "lifting a shaky spoonful of grey gruel toward the mouth, grimacing in disgust",
      "swallowing with a sad sigh, lowering the bowl, shoulders slumping"],
 2:  ["standing with arms crossed tight, sulking glum scowl",
      "hugging the arms in and shivering, glancing away miserably",
      "arms crossed again, head dropping down with an unhappy frown"],
 3:  ["holding the wooden tankard down at the side, weary and tired",
      "wiping the brow with the free hand, sighing, exhausted and defeated",
      "holding the tankard out to serve, shoulders drooping unhappily"],
 4:  ["clutching the wooden spear upright with both hands, nervous and unhappy",
      "flinching backward, gripping the spear tighter, eyes wide with fear",
      "sinking into a timid uncertain guard, knees bent, trembling nervously"],
 5:  ["resting the longsword point-down, one hand on the pommel, confident",
      "lifting the longsword up into a ready guard, smirking bravely",
      "giving the blade a small confident sweeping swing"],
 6:  ["standing at attention, longsword lowered, shield held at the side",
      "raising the heraldic shield and pointing the longsword forward boldly",
      "returning to attention with a proud upright nod"],
 7:  ["standing commanding with one hand resting on the hip, chin high",
      "raising a hand in a sweeping commanding gesture, cloak flaring",
      "crossing the arms with an authoritative confident smirk"],
 8:  ["holding the huge warhammer resting head-down on the ground, fierce",
      "HOISTING the warhammer high overhead with both arms, roaring, muscles straining",
      "swinging the warhammer to rest on one shoulder, glaring fiercely"],
 9:  ["seated on the throne, royal scepter held upright, regal and still",
      "raising the scepter and lifting the other hand in a commanding decree",
      "settling back into the throne with an imperious satisfied nod"],
 10: ["seated on the Iron Throne, the dragon looming calmly behind, embers drifting",
      "the DRAGON rearing up BREATHING A BLAST OF FIRE, the monarch raising a hand, aura of embers blazing bright",
      "the dragon settling, the monarch gripping the throne arms with a powerful commanding glare"],
}

def guard(name, i):
    m = (" Her tunic/gown/robes/armor stay fully INTACT and cover her chest — never rip, never show breasts/nipples/cleavage."
         if GENDER.get(name) == "F" else "")
    return ("This EXACT pixel-art character. Keep the FACE, identity, hair, skin tone, the outfit and its COLORS, "
            "body shape/size, HEIGHT, position, camera distance/scale and the ENTIRE background/setting completely "
            "IDENTICAL to the reference — do not redraw, move, or resize them." + m +
            " This is frame " + str(i) + " of a 3-frame loop of the SAME action. Change ONLY this pose: ")

def call(img, prompt):
    payload = {"prompt": prompt, "image_base64": base64.b64encode(img).decode(), "mime": "image/png"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=180); d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return None, "HTTP %s" % e.code
    except Exception as e:
        return None, repr(e)[:80]
    if not d.get("ok"): return None, "apierr"
    return base64.b64decode(d["image_base64"]), None

def anchor_path(name, t): return os.path.join(SRC, f"{name}-got-L{t:02d}.png")
def frame_path(name, t, i): return os.path.join(SRC, f"{name}-got-L{t:02d}-f{i}.png")

def gen():
    for p in range(PASSES):
        missing = 0
        for name in PEOPLE:
            for t in range(1, 11):
                ap = anchor_path(name, t)
                if not os.path.exists(ap): print("NO ANCHOR", name, t, flush=True); continue
                anchor = open(ap, "rb").read()
                for i, pose in enumerate(MOTION[t], 1):
                    op = frame_path(name, t, i)
                    if os.path.exists(op) and os.path.getsize(op) > 1000: continue
                    ok = False
                    for _ in range(RETRIES):
                        img, err = call(anchor, guard(name, i) + pose + ". Keep everything else pixel-identical.")
                        if img:
                            open(op, "wb").write(img); print("OK", name, t, i, flush=True); ok = True; break
                        time.sleep(3)
                    if not ok: missing += 1; print("miss", name, t, i, err, flush=True)
        print(f"=== pass {p+1}: {missing} missing ===", flush=True)
        if missing == 0: break

def gsize():
    fs = glob.glob(os.path.join(SRC, "*-got-L[0-9][0-9]-f[0-9].png"))
    sz = [Image.open(p).size for p in fs]
    return (max(w for w, h in sz), max(h for w, h in sz)) if sz else (0, 0)

def build():
    gw, gh = gsize()
    if not gw: print("no frames to build"); return
    for name in PEOPLE:
        for t in range(1, 11):
            fp = [frame_path(name, t, i) for i in (1, 2, 3)]
            if not all(os.path.exists(x) for x in fp): print("missing frames", name, t, flush=True); continue
            frames = []
            for x in fp:
                im = Image.open(x).convert("RGBA"); bg = im.getpixel((2, 2))
                c = Image.new("RGBA", (gw, gh), bg)
                c.alpha_composite(im, ((gw - im.width) // 2, gh - im.height))
                ow = OUT_W; oh = int(gh * ow / gw); oh -= oh % 2
                c = c.resize((ow, oh), Image.LANCZOS)
                frames.append(c.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=256))
            out = os.path.join(SRC, f"{name}-got-L{t:02d}.gif")
            frames[0].save(out, save_all=True, append_images=frames[1:], duration=MS, loop=0, disposal=2, optimize=True)
            print("GIF", os.path.basename(out), f"{os.path.getsize(out)//1024}KB", flush=True)

def verify():
    print("---- COVERAGE ----", flush=True)
    total_f = total_g = 0
    for name in PEOPLE:
        nf = sum(os.path.exists(frame_path(name, t, i)) for t in range(1, 11) for i in (1, 2, 3))
        ng = sum(os.path.exists(os.path.join(SRC, f"{name}-got-L{t:02d}.gif")) for t in range(1, 11))
        total_f += nf; total_g += ng
        print(f"{name}: {nf}/30 frames, {ng}/10 gifs", flush=True)
    print(f"TOTAL: {total_f}/120 frames, {total_g}/40 gifs", flush=True)
    # proof contact-sheet: for each person, level 10's 3 frames side by side (prove pose changes)
    for name in PEOPLE:
        fp = [frame_path(name, 10, i) for i in (1, 2, 3)]
        if all(os.path.exists(x) for x in fp):
            ims = [Image.open(x).convert("RGB") for x in fp]
            w = 300; cs = [im.resize((w, int(im.height * w / im.width))) for im in ims]
            h = max(c.height for c in cs); sheet = Image.new("RGB", (3 * w, h), (18, 15, 26))
            for j, c in enumerate(cs): sheet.paste(c, (j * w, h - c.height))
            sheet.save(os.path.join(SRC, f"{name}-got-L10-frames.png"))
    print("DONE", flush=True)

gen(); build(); verify()
