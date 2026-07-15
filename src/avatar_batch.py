#!/usr/bin/env python3
# avatar_batch.py — generate avatar tiers in a chosen art style via the gen-avatar edge fn.
# Usage: python avatar_batch.py <input_image> <out_dir> <name> <combos>
#   combos = comma list of "style:tier" e.g. "pixel:1,pixel:10,anime:1,anime:10"
# Scale: 1 = sickly ... 5 = baseline ... 10 = buff beyond all control (super extra).
# Prints ONLY status per image; writes files to <out_dir>/<name>-<style>-<tier2>.png
import sys, os, json, base64, urllib.request, urllib.error

URL = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"

FACE = ("Using the man with the dark beard and cream knit polo shirt in this photo as the EXACT face reference, "
        "create a cartoon avatar of HIM. Match his real face as closely as possible so it is instantly "
        "recognizable as this same specific person — keep the exact beard shape and fullness, the hairline and "
        "hair, eye shape and color, eyebrows, nose, face shape and skin tone. Prioritize a faithful facial "
        "likeness above everything else; only the body changes between versions, the face stays the same person.")
WARDROBE = "He is dressed in gym / athletic clothes: a fitted workout tank top, gym shorts, and training sneakers."
FRAMING = ("Full body, centered, front-facing, standing, clean solid flat pastel background, consistent framing, "
           "glossy mobile game sticker look. Absolutely no text, words, letters or numbers anywhere in the image.")

STYLES = {
    "pixel": ("Rendered as detailed retro PIXEL ART — a 32-bit video-game character sprite, crisp chunky pixels, "
              "bold limited color palette, like a classic SNES / arcade fighter character-select screen."),
    "anime": ("Rendered in an OVER-THE-TOP shonen anime style like Dragon Ball Z and One Punch Man — bold cel "
              "shading, thick clean outlines, dramatic dynamic energy, glowing power aura and speed lines, "
              "hyper-exaggerated intensity."),
}

TIERS = {
    1:  "Physique: deathly SICKLY and GROSS — skeletal and frail, sickly greenish-pale clammy skin, sunken bloodshot eyes with heavy dark circles, dripping sweat, hunched and trembling, looks nauseous and about to throw up, ribs showing. Comically disgusting and near-death. Mood: miserable, ill, defeated.",
    2:  "Physique: sickly, weak and GROSS — very skinny with a pale greenish sweaty tinge, sunken tired bloodshot eyes, bad hunched posture, looks queasy and unwell, clammy and gross. Mood: exhausted and sick.",
    3:  "Physique: skinny-soft, unfit, a little pudgy, no muscle tone. Mood: sluggish, meh.",
    4:  "Physique: slightly soft and below average, faint dad-bod. Mood: neutral, low energy.",
    5:  "Physique: totally average BASELINE build — ordinary regular guy, neither fit nor unfit. Mood: calm, content.",
    6:  "Physique: fit and toned, in decent shape, hint of abs. Mood: upbeat, confident.",
    7:  "Physique: athletic and clearly muscular, defined abs and arms. Mood: proud, flexing lightly.",
    8:  "Physique: very muscular bodybuilder, big arms and chest, six-pack. Mood: strong and cocky.",
    9:  "Physique: massive hulking bodybuilder, huge veiny muscles bursting from clothes. Mood: fierce, powerful.",
    10: ("Physique: ABSURDLY, IMPOSSIBLY, COMICALLY muscular — buff beyond all control, gigantic bulging veiny "
         "muscles stacked on muscles, shoulders wider than the frame, tiny head on a mountain of muscle, shirt "
         "exploding off, radiating golden power. WAY past any realistic bodybuilder, maximum over-the-top. "
         "Mood: euphoric, roaring in triumph, flexing with unstoppable god energy."),
}

def gen(inp, prompt, outp):
    raw = open(inp, "rb").read()
    ext = os.path.splitext(inp)[1].lower()
    mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
    payload = {"prompt": prompt, "image_base64": base64.b64encode(raw).decode(), "mime": mime}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=180)
        d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return "HTTP_ERROR %s %s" % (e.code, e.read()[:300].decode(errors="replace"))
    except Exception as e:
        return "ERROR " + repr(e)
    if not d.get("ok"):
        return "GEN_FAIL " + json.dumps({k: v for k, v in d.items() if k != "raw"})[:400]
    out = base64.b64decode(d["image_base64"])
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    open(outp, "wb").write(out)
    return "OK %s (%d bytes)" % (os.path.basename(outp), len(out))

inp, out_dir, name, combos = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
for combo in combos.split(","):
    style, tier = combo.split(":")
    tier = int(tier)
    prompt = " ".join([FACE, STYLES[style], TIERS[tier], WARDROBE, FRAMING])
    outp = os.path.join(out_dir, "%s-%s-%02d.png" % (name, style, tier))
    print(combo, "->", gen(inp, prompt, outp), flush=True)
