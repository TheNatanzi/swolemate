#!/usr/bin/env python3
# avatar_scale.py — CONSISTENT 1..10 avatar scale for one person (pixel-art style).
# Method: generate ONE locked base character (tier 5) from the photo with MAXIMUM face
# likeness, then make every other tier an EDIT of that base image so face/height/style/
# background stay identical and only the body/theme changes.
#   Tiers 1-4 = FOOD themed (fat + sick).  Tiers 6-10 = GYM themed (buff).  10 = super saiyan.
# Per-person look (gender, outfit, skin/eye/height notes) comes from PEOPLE[name].
# Usage: python avatar_scale.py <photo> <out_dir> <name> [tiers e.g. "1,10" | "base"]
import sys, os, json, base64, urllib.request, urllib.error

URL = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"

STYLE_KEY = "pixel"
STYLE = ("clean HIGH-DETAIL 32-bit PIXEL ART — a polished video-game character sprite with crisp pixels, "
         "smooth pixel shading, bold dark outlines and a rich palette, like a modern indie pixel game")

LIKENESS = (
    "TOP PRIORITY — FACIAL LIKENESS. The face must look UNMISTAKABLY like the specific person in this photo. "
    "Anyone who knows them must instantly recognize them. Reproduce their EXACT face precisely: the same face "
    "shape and jawline, the same eye shape, size, spacing AND eye color, the same eyebrows, the same nose, the "
    "same mouth and lips, the same hairstyle, hairline and hair color, the SAME SKIN TONE (do not darken or "
    "lighten it), and the same overall proportions. Spend the pixel detail on the FACE so the features read "
    "clearly. Do NOT generic-ify, beautify, or change their ethnicity, age, or distinctive features — copy the "
    "real face faithfully, only translating it into pixel-art. "
)

# Per-person overrides. build folds in height; outfit is opaque and hides the torso.
M_TEE = ("a fitted OPAQUE gym T-SHIRT in solid BLUE that completely hides his torso and abs (you can NEVER see "
         "skin or muscle through the fabric), plus gym shorts and sneakers")
PEOPLE = {
    "medi":    {"gender": "M", "outfit": M_TEE, "build": "an average normal healthy build", "extra": ""},
    "teyaum":  {"gender": "M", "outfit": M_TEE, "build": "an average normal healthy build",
                "extra": "IMPORTANT SKIN + FACE: his complexion is LIGHTER — olive / light-medium Middle-Eastern "
                         "skin, NOT dark brown and NOT black; match his real complexion exactly and do not darken "
                         "it. His face is noticeably ROUND and full (rounder cheeks, softer jaw). HAIR: match his "
                         "real haircut closely — a clean TIGHT FADE, short and tight on the SIDES fading up to a "
                         "bit more length on top. "},
    "gizem":   {"gender": "F",
                "outfit": "a fitted OPAQUE PURPLE athletic sports top and matching leggings that completely hide "
                          "her torso and midriff (you can NEVER see skin through the fabric), plus sneakers",
                "build": "a PETITE, slightly SHORTER, slender healthy build",
                "extra": "She is petite and a bit shorter than average. "},
    "rinad":   {"gender": "F",
                "outfit": "a fitted OPAQUE TEAL-GREEN athletic sports top and matching leggings that completely "
                          "hide her torso and midriff (you can NEVER see skin through the fabric), plus sneakers",
                "build": "a TALL, slender healthy build with long legs",
                "extra": "She has striking GREEN-HAZEL eyes — make the eye color clearly green/hazel. She is TALL. "},
}
DEFAULT = {"gender": "M", "outfit": M_TEE, "build": "an average normal healthy build", "extra": ""}

def base_prompt(cfg):
    if cfg["gender"] == "F":
        who, pron = "the WOMAN in this photo", "HER"
        hair_face = "her exact hairstyle, hairline and hair, eyebrows, and eyes (NO beard, NO facial hair)"
    else:
        who, pron = "the MAN in this photo", "HIM"
        hair_face = "his exact beard shape and fullness (keep his real facial hair), hairline, hair, eyebrows, and eyes"
    return (LIKENESS + cfg["extra"] +
            "Using " + who + " as the EXACT face reference, create a full-body avatar of " + pron + " in " + STYLE +
            ". Preserve " + hair_face + " and their exact skin tone. They wear " + cfg["outfit"] + ", " +
            cfg["build"] + ", neutral friendly expression. Full body head-to-feet, centered, front-facing, "
            "standing on a ground line, one solid flat lavender background (#b7a4e0). No text or letters.")

def edit_prefix(cfg):
    p = ("she/her" if cfg["gender"] == "F" else "he/his")
    face_kw = ("her face, identity, hairstyle, hair, eye color" if cfg["gender"] == "F"
               else "his face, identity, beard, hairline, hair, eye color")
    modesty = (" CRITICAL MODESTY RULE: her athletic top ALWAYS stays fully INTACT and fully covers her chest and "
               "breasts — it NEVER rips, tears, explodes, shreds, or comes off, and its SLEEVES/SHOULDERS stay "
               "fully intact too (no torn or shredded sleeves, no fabric bursting on the arms or shoulders), not "
               "even on the strongest/most powered-up tiers; NEVER show breasts, nipples, cleavage, or any chest "
               "skin. Only her LOWER belly "
               "(below the intact top) may be bare, and only when the description says so." if cfg["gender"] == "F" else "")
    return ("This exact pixel-art character. Keep " + face_kw + ", skin tone, HEIGHT, head size, the same "
            "pixel-art style, front-facing standing pose on the same ground line, camera distance/scale and the "
            "solid lavender background 100% IDENTICAL — the FACE must stay an exact match to the reference. The "
            "gym top KEEPS ITS BASE COLOR and is opaque; it hides the torso EXCEPT where the description says the "
            "bare belly hangs out or the top rips/explodes." + modesty + " You MAY dramatically change the body, "
            "the top's fit, the facial expression, and add the described prop. Push it HARD — wildly exaggerated, "
            "cartoonish, comically extreme. Make " + p + " body: ")

# 1-4 FOOD themed w/ bare belly (fat+sick) · 6-9 GYM themed (buff) · 10 super saiyan
BODY = {
    1:  "like JABBA THE HUTT — a colossal immobile blob of fat with NO LEGS AT ALL; instead the entire lower body is a huge fat LIZARD/SLUG TAIL coiled on the ground that they SIT ON TOP OF (exactly like Jabba the Hutt). One gigantic bare belly spilling out under a tiny stretched top, tiny useless arms, greasy sweaty sickly greenish skin, gross, half-buried in fast-food wrappers and burgers. Comically enormous and disgusting.",
    2:  "grotesquely fat and sick — a huge bare round belly hanging out below a too-small top, triple chin, greenish sweaty nauseous face, chugging a giant 2-liter soda with both hands.",
    3:  "clearly fat — a big round bare belly poking out under the top, double chin, lazy slouch, shoving a giant fistful of greasy fries into the mouth.",
    4:  "chubby and a bit unhappy — a soft round pot belly (noticeably bigger now, but still clearly less than #3) poking out under the top, glum grumpy frown, out of shape, holding a donut.",
    6:  "fit with a bit of muscle — trimmed and athletic with visibly toned arms and a firmer build (a touch more buff than just slim), the top covering the torso, casual confident thumbs up.",
    7:  "clearly muscular and RIPPED — noticeably bigger and way more jacked than the lean version, big arms and a broad build filling out the top, sunglasses, confident biceps flex.",
    8:  "a MASSIVE bodybuilder — enormous arms and muscles, the top straining at the seams, veins bulging, hoisting a huge loaded barbell, huge grin.",
    9:  "an ENORMOUS hulking gym beast — colossal veiny boulder muscles (the muscle skin MUST stay their exact natural skin tone — do NOT tint the arms/muscles pink, purple, red or any unnatural color), the top straining hard but INTACT, deadlifting a giant bending barbell, roaring with steam blasting off them.",
    10: "FULL SUPER SAIYAN (in pixel art) — impossibly ripped and huge, a blazing golden energy aura and crackling lightning all around, the top obliterated, screaming mid power-up pose, the ground cracking. IMPORTANT OVERRIDE: change the hair (and beard if present) to be COMPLETELY blond / bright golden-yellow, spiky and standing straight up — absolutely NO brown/dark hair left anywhere. Maximum absurd Dragon Ball Z power. Keep the FACE recognizable as the same person.",
}

def call(img_bytes, prompt):
    payload = {"prompt": prompt, "image_base64": base64.b64encode(img_bytes).decode(), "mime": "image/png"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=180); d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return None, "HTTP %s %s" % (e.code, e.read()[:200].decode(errors="replace"))
    except Exception as e:
        return None, repr(e)
    if not d.get("ok"):
        return None, json.dumps({k: v for k, v in d.items() if k != "raw"})[:300]
    return base64.b64decode(d["image_base64"]), None

photo, out_dir, name = sys.argv[1], sys.argv[2], sys.argv[3]
only = sys.argv[4] if len(sys.argv) > 4 else None
cfg = PEOPLE.get(name, DEFAULT)
os.makedirs(out_dir, exist_ok=True)
base_path = os.path.join(out_dir, f"{name}-{STYLE_KEY}-05.png")

if only and only != "base":
    base = open(base_path, "rb").read()
    tiers = [int(t) for t in only.split(",")]
    print("reusing base, redoing", tiers, flush=True)
else:
    photo_bytes = open(photo, "rb").read()
    print("base(5)...", flush=True)
    base, err = call(photo_bytes, base_prompt(cfg))
    if err: print("BASE FAIL", err); sys.exit(1)
    open(base_path, "wb").write(base)
    print("OK base", flush=True)
    tiers = [] if only == "base" else [4, 6, 3, 7, 2, 8, 1, 9, 10]

for tier in tiers:
    img, err = call(base, edit_prefix(cfg) + BODY[tier] + " Same person, same face, same height, only the body/theme differs.")
    if err: print(f"tier {tier} FAIL", err); continue
    open(os.path.join(out_dir, f"{name}-{STYLE_KEY}-{tier:02d}.png"), "wb").write(img)
    print(f"OK {tier}", flush=True)
