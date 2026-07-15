#!/usr/bin/env python3
# Regenerate GoT levels 1-4 for all people: all UNHAPPY/miserable, and L4 = unarmored chubby scared spearman.
import json, base64, urllib.request, os, time
from PIL import Image
URL = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC = "generated"; GENDER = {"medi": "M", "teyaum": "M", "gizem": "F", "rinad": "F"}
PEOPLE = ["medi", "teyaum", "gizem", "rinad"]
DESC = {
 1: "a filthy gaunt FLEA BOTTOM PEASANT with a MISERABLE unhappy downcast frowning face: ragged dirty patched brown rags and a tattered hood, dirt and soot smudged on {his} sunken gaunt face, a scrawny frail weak body, a slumped hopeless posture, clutching a chipped wooden bowl of grey-brown gruel, standing in a muddy grimy medieval slum alley. pathetic, dirt-poor and sad.",
 2: "a scrappy starving GUTTER URCHIN with a glum UNHAPPY sulking scowl: a skinny half-starved frame, a torn grubby tunic, barefoot, matted messy hair, a hunched miserable pose, a dim market-alley background. still small, weak and unhappy.",
 3: "a soft lowly TAVERN SERVANT with a tired UNHAPPY defeated expression: a plain rough-spun commoner tunic and apron, a soft little ale belly, a weary miserable slouch, carrying a wooden tankard, a dim candle-lit tavern behind. ordinary, unremarkable and glum.",
 4: "a lowly UNARMORED conscript spear-carrier with a nervous scared UNHAPPY worried face: NO armor at all, just a simple drab peasant tunic and trousers, a soft slightly FAT pudgy belly, timidly clutching a plain wooden spear, cowering slightly, standing in a muddy training yard by a wooden palisade fence. comically soft, out of shape, scared and unhappy.",
}
def call(anchor, prompt):
    img = open(os.path.join(SRC, anchor), "rb").read()
    payload = {"prompt": prompt, "image_base64": base64.b64encode(img).decode(), "mime": "image/png"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=180); d = json.loads(r.read())
    except Exception as e:
        return None, repr(e)[:90]
    if not d.get("ok"): return None, "apierr"
    return base64.b64decode(d["image_base64"]), None
def prompt(name, lvl):
    F = GENDER.get(name) == "F"; his = "her" if F else "his"
    mod = " Her tunic/rags fully cover her chest — never show breasts/nipples/cleavage." if F else ""
    return ("This EXACT pixel-art character. Keep " + his + " FACE, identity, hairline and skin tone clearly recognizable, the crisp pixel-art style, "
            "and a full-body front-facing composition. Change ONLY the outfit, physique, props, EXPRESSION and background to make " + his + " " +
            DESC[lvl].format(his=his) + mod + " Keep the face an exact match to the reference person.")
# regenerate 1-4 (overwrite) with retries
for name in PEOPLE:
    for lvl in [1, 2, 3, 4]:
        op = os.path.join(SRC, f"{name}-got-L{lvl:02d}.png")
        for a in range(6):
            img, err = call(f"{name}-pixel-05.png", prompt(name, lvl))
            if img:
                open(op, "wb").write(img); print("OK", name, lvl, flush=True); break
            print("retry", name, lvl, err, flush=True); time.sleep(4)
        else:
            print("FAIL", name, lvl, flush=True)
# rebuild montages
for name in PEOPLE:
    try:
        fs = [Image.open(f"{SRC}/{name}-got-L{lvl:02d}.png").convert("RGB") for lvl in range(1, 11)]
        CW = 360; cells = [f.resize((CW, int(f.height * CW / f.width))) for f in fs]; CH = max(c.height for c in cells)
        strip = Image.new("RGB", (5 * CW, 2 * CH), (18, 15, 26))
        for i, c in enumerate(cells):
            r, cc = divmod(i, 5); strip.paste(c, (cc * CW, r * CH + CH - c.height))
        strip.save(f"{SRC}/{name}-got-SCALE.png"); print("montage", name, flush=True)
    except Exception as e:
        print("montage fail", name, e, flush=True)
print("DONE", flush=True)
