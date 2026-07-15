#!/usr/bin/env python3
# got_build.py — Game of Thrones weekly-streak avatar set: 10 levels/person (Flea Bottom peasant -> Targaryen dragon-monarch),
# frail -> jacked. Edits each person's pixel base into each GoT level. Robust retries (gen-avatar 502s a lot). Then montages.
import json, base64, urllib.request, os, time
from PIL import Image

URL = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC = "generated"
GENDER = {"medi": "M", "teyaum": "M", "gizem": "F", "rinad": "F"}
PEOPLE = ["medi", "teyaum", "gizem", "rinad"]

def tok(name):
    F = GENDER.get(name) == "F"
    return {"his": "her" if F else "his", "king": "queen" if F else "king", "lord": "lady" if F else "lord"}

LEVELS = {
 1: "a filthy gaunt FLEA BOTTOM PEASANT: ragged dirty patched brown rags and a tattered hood, dirt and soot smudged on {his} sunken gaunt face, a scrawny frail weak body, slumped defeated posture, clutching a chipped wooden bowl of grey-brown gruel, standing in a muddy grimy medieval slum alley. pathetic and dirt-poor.",
 2: "a scrappy starving GUTTER URCHIN: a skinny half-starved frame, a torn grubby tunic, barefoot, matted messy hair, a sneaky hunched pickpocket pose, a dim market-alley background. still small and weak.",
 3: "a soft lowly TAVERN SERVANT: a plain rough-spun commoner tunic and apron, a soft little ale belly, a meek tired slouch, carrying a wooden tankard, a dim candle-lit tavern behind. ordinary and unremarkable.",
 4: "a GOLD CLOAK CITY WATCH guard: a black cloak over simple chainmail, a body just starting to firm up and get fitter, gripping a spear, standing guard at a stone city gate. lowly but rising.",
 5: "a rugged SELLSWORD mercenary: worn leather-and-mail armor, an average toned athletic build, a scarred longsword at the ready, a confident rough stance, a war-camp campfire background. getting capable.",
 6: "a gallant ANOINTED KNIGHT: gleaming polished steel plate armor, a fit muscular build filling out the armor, a longsword and a heraldic shield, a proud upright noble bearing, a castle courtyard. strong and honorable.",
 7: "a mighty LANDED {lord}: rich noble finery with a fur-trimmed cloak and a jeweled brooch, a strong powerful physique, a confident commanding stance inside a grand castle great hall. wealthy and imposing.",
 8: "a fearsome WARDEN of the realm: battle-hardened and heavily MUSCULAR, ornate dark plate armor bearing a house sigil, hoisting a huge warhammer, snowfall and war banners behind, a fierce commanding presence.",
 9: "a CROWNED {king}: regal royal robes and a gleaming gold-and-jewel crown, a buff powerful physique, a royal scepter in hand, standing in a torch-lit throne room. majestic and dominant.",
 10: "the ultimate TARGARYEN DRAGON-{king}: an impossibly RIPPED and jacked physique, long flowing silver-white platinum hair, black armor bearing the red three-headed Targaryen dragon sigil with a royal cloak, a spiky iron crown, seated powerfully upon the IRON THRONE built of a thousand swords, a huge DRAGON looming behind breathing orange fire, glowing embers and epic dramatic lighting. maximum regal power-fantasy.",
}

def call(anchor, prompt):
    img = open(os.path.join(SRC, anchor), "rb").read()
    payload = {"prompt": prompt, "image_base64": base64.b64encode(img).decode(), "mime": "image/png"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=180); d = json.loads(r.read())
    except Exception as e:
        return None, repr(e)[:110]
    if not d.get("ok"):
        return None, "apierr"
    return base64.b64decode(d["image_base64"]), None

def prompt_for(name, lvl):
    t = tok(name); desc = LEVELS[lvl].format(**t)
    mod = (" Her armor/robes/clothing FULLY cover her chest — never show breasts, nipples or cleavage." if GENDER.get(name) == "F" else "")
    seated = " (seated on the throne)" if lvl >= 9 else ""
    return ("This EXACT pixel-art character. Keep " + t["his"] + " FACE, identity, hairline and skin tone clearly recognizable, "
            "the crisp pixel-art style, and a full-body front-facing composition" + seated + ". Change ONLY the outfit, physique, props and "
            "background to make " + t["his"] + " " + desc + mod + " Keep the face an exact match to the reference person.")

def out_path(name, lvl): return os.path.join(SRC, f"{name}-got-L{lvl:02d}.png")

# ---- generate (up to 8 passes, skip existing) ----
for p in range(8):
    missing = 0
    for name in PEOPLE:
        if not os.path.exists(os.path.join(SRC, f"{name}-pixel-05.png")):
            print("NO BASE", name, flush=True); continue
        for lvl in range(1, 11):
            op = out_path(name, lvl)
            if os.path.exists(op) and os.path.getsize(op) > 1000: continue
            img, err = call(f"{name}-pixel-05.png", prompt_for(name, lvl))
            if img:
                open(op, "wb").write(img); print("OK", name, lvl, flush=True)
            else:
                missing += 1; print("fail", name, lvl, err, flush=True); time.sleep(3)
    print(f"=== pass {p+1}: {missing} still missing ===", flush=True)
    if missing == 0: break

# ---- montages (2x5 evolution strip per person) ----
def montage(name):
    fs = []
    for lvl in range(1, 11):
        op = out_path(name, lvl)
        if os.path.exists(op): fs.append(Image.open(op).convert("RGB"))
    if len(fs) < 10:
        print("montage skip", name, len(fs), flush=True); return
    CW = 360; COLS, ROWS = 5, 2
    cells = [f.resize((CW, int(f.height * CW / f.width))) for f in fs]
    CH = max(c.height for c in cells)
    strip = Image.new("RGB", (COLS * CW, ROWS * CH), (18, 15, 26))
    for i, c in enumerate(cells):
        r, cc = divmod(i, COLS); strip.paste(c, (cc * CW, r * CH + CH - c.height))
    strip.save(os.path.join(SRC, f"{name}-got-SCALE.png")); print("montage", name, flush=True)

for name in PEOPLE:
    montage(name)
print("ALL DONE", flush=True)
