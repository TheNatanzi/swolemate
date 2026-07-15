#!/usr/bin/env python3
# Build message-review.html: every coach roast line (numbered, by category) + live samples of each
# message mode, WhatsApp-styled. Click lines to flag for cleanup -> copy list. 100% static (no connector calls).
import re, io, json, html, os, base64
from PIL import Image, ImageSequence
def datauri(path, w=110, colors=48):
    im = Image.open(path); frames = []; durs = []
    for fr in ImageSequence.Iterator(im):
        f = fr.convert("RGB"); h = int(f.height * w / f.width)
        frames.append(f.resize((w, h), Image.LANCZOS)); durs.append(fr.info.get("duration", 150))
    q = [f.convert("P", palette=Image.ADAPTIVE, colors=colors) for f in frames]
    buf = io.BytesIO()
    q[0].save(buf, format="GIF", save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=2, optimize=True)
    return "data:image/gif;base64," + base64.b64encode(buf.getvalue()).decode()
FA = os.path.dirname(os.path.abspath(__file__))
SCR = r"C:/Users/Mahdi/AppData/Local/Temp/claude/G--Shared-drives-Adibs-Online-Anthropic-Fitness-App/1ee9adac-cee8-474b-88d4-c0197feb8a05/scratchpad"
src = io.open(os.path.join(FA, "supabase/functions/coach/roast-lines.ts"), encoding="utf-8").read()

# --- parse exported arrays of template strings/quotes ---
CATS = {}
for m in re.finditer(r"export const (\w+)\s*(?::[^=]+)?=\s*\[(.*?)\];", src, re.S):
    name, body = m.group(1), m.group(2)
    if name == "GIF_MAP":
        continue
    lines = re.findall(r"`((?:[^`\\]|\\.)*)`|\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)'", body)
    vals = [a or b or c for a, b, c in lines if (a or b or c).strip()]
    if vals:
        CATS[name] = vals

GROUPS = [
 ("Daily openers & sign-offs", ["OPENERS", "SIGNOFFS"]),
 ("Gym", ["GYM_SLAY", "GYM_MID", "GYM_FLOP"]),
 ("Steps", ["STEPS_SLAY", "STEPS_MID", "STEPS_FLOP"]),
 ("Calories", ["CAL_ON", "CAL_OVER", "CAL_UNDER", "CAL_NONE"]),
 ("Protein", ["PROT_SLAY", "PROT_CLOSE", "PROT_LOW"]),
 ("Streaks", ["STREAK_LONG", "STREAK_FRAGILE", "STREAK_BROKEN", "STREAK_MILESTONE"]),
 ("Daily verdicts", ["VERDICT_GREAT", "VERDICT_MID", "VERDICT_TRASH"]),
 ("Weekly league", ["LEAGUE_FIRST", "LEAGUE_LAST", "LEAGUE_MID"]),
 ("Special moments", ["COMEBACK", "GHOSTING", "PERFECT_DAY"]),
 ("Quests", ["QUEST_ANNOUNCE", "QUEST_FIRST", "QUEST_LAST"]),
]
NICE = {"OPENERS":"Openers","SIGNOFFS":"Sign-offs","GYM_SLAY":"Gym · crushed it","GYM_MID":"Gym · meh","GYM_FLOP":"Gym · flop",
 "STEPS_SLAY":"Steps · crushed it","STEPS_MID":"Steps · meh","STEPS_FLOP":"Steps · flop",
 "CAL_ON":"Calories · on target","CAL_OVER":"Calories · over","CAL_UNDER":"Calories · under","CAL_NONE":"Calories · nothing logged",
 "PROT_SLAY":"Protein · hit","PROT_CLOSE":"Protein · close","PROT_LOW":"Protein · low",
 "STREAK_LONG":"Streak · long","STREAK_FRAGILE":"Streak · fragile","STREAK_BROKEN":"Streak · broken","STREAK_MILESTONE":"Streak · milestone",
 "VERDICT_GREAT":"Verdict · great day","VERDICT_MID":"Verdict · mid day","VERDICT_TRASH":"Verdict · trash day",
 "LEAGUE_FIRST":"League · 1st place","LEAGUE_LAST":"League · last place","LEAGUE_MID":"League · middle",
 "COMEBACK":"Comeback","GHOSTING":"Ghosting (no data)","PERFECT_DAY":"Perfect day",
 "QUEST_ANNOUNCE":"Quest · announce","QUEST_FIRST":"Quest · first done","QUEST_LAST":"Quest · last done"}

# --- live samples ---
MODE_META = [("msg_daily1.json","☀️ Daily read (10:00 AM)"),("msg_wtd1.json","📊 Week-to-date"),("msg_gap1.json","🎯 Close the gap"),
 ("msg_ladder1.json","⚡ Daily avatar ladder (rides the 10 AM drop)"),("msg_mealam.json","🍳 Meal check (4:30 PM)"),("msg_mealpm.json","🍽️ Meal check (9:30 PM)"),
 ("msg_monday1.json","🏁 Monday recap (12 PM)"),("msg_throne1.json","🐉 Weekly avatar ladder (rides Monday recap)")]
samples = []
for fn, label in MODE_META:
    p = os.path.join(SCR, fn)
    if not os.path.exists(p):
        continue
    d = json.load(io.open(p, encoding="utf-8"))
    msgs = d.get("messages") or d.get("msgs") or ([d.get("message")] if d.get("message") else None)
    if msgs is None:
        # fall back: collect all string values / list-of-strings in the dict
        msgs = []
        for v in d.values():
            if isinstance(v, str) and len(v) > 40: msgs.append(v)
            elif isinstance(v, list): msgs += [x for x in v if isinstance(x, str) and len(x) > 20]
    samples.append((label, msgs or ["(no preview returned)"]))

def wa(text):
    t = html.escape(text)
    t = re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", t)  # WhatsApp *bold*
    return t.replace("\n", "<br>")

parts = []
parts.append("""<title>SwoleMate — Message Review</title>
<style>
:root{--bg:#0b0910;--panel:#15111d;--panel2:#1c1628;--line:#2b2340;--ink:#f6f0fc;--muted:#a998c1;--pink:#ff2e88;--green:#00d68f;--gold:#f5b933;
--wa:#0a0f0d;--bub:#1f2c26;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
.wrap{max-width:1060px;margin:0 auto;padding:34px 20px 90px}
h1{font-size:clamp(26px,5vw,42px);font-weight:900;letter-spacing:-.03em}
h1 .p{color:var(--pink)} h1 .g{color:var(--green)}
.sub{color:var(--muted);margin-top:8px;max-width:640px;font-size:15px}
.howto{margin:18px 0 8px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;font-size:13.5px;color:var(--muted)}
.howto b{color:var(--gold)}
h2{font-size:22px;font-weight:800;margin:42px 0 4px;letter-spacing:-.01em}
h3{font-size:13px;font-family:ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--pink);margin:26px 0 10px}
.cat{color:var(--muted);font-size:12px;font-family:ui-monospace,monospace;margin-left:8px}
.line{display:flex;gap:10px;align-items:flex-start;padding:8px 12px;border:1px solid var(--line);border-radius:10px;margin:6px 0;cursor:pointer;background:var(--panel);font-size:14px}
.line:hover{border-color:var(--gold)}
.line.flag{border-color:var(--pink);background:rgba(255,46,136,.10)}
.line.flag .tx{text-decoration:line-through;opacity:.75}
.line .id{font-family:ui-monospace,monospace;font-size:11px;color:var(--gold);flex:0 0 74px;padding-top:2px}
.line .tx{white-space:pre-wrap}
.phones{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;margin-top:16px}
.phone{background:var(--wa);border:8px solid #1b1622;border-radius:26px;padding:10px}
.plabel{font-family:ui-monospace,monospace;font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:4px 6px 10px;border-bottom:1px solid rgba(255,255,255,.07);margin-bottom:8px}
.bub{background:var(--bub);border-radius:12px;border-top-left-radius:4px;padding:10px 12px;margin:8px 2px;font-size:12.8px;line-height:1.5;word-wrap:break-word}
.bar{position:fixed;bottom:0;left:0;right:0;background:var(--panel2);border-top:1px solid var(--line);padding:12px 20px;display:flex;gap:14px;align-items:center;justify-content:center;flex-wrap:wrap}
.bar .n{font-weight:800;color:var(--pink);font-size:15px}
.btn{background:var(--pink);color:#fff;font-weight:800;border:none;border-radius:999px;padding:10px 22px;font-size:14px;cursor:pointer}
.btn.alt{background:transparent;border:1px solid var(--line);color:var(--muted)}
.note{color:var(--muted);font-size:12px}
</style>
<div class="wrap">
<h1><span class="p">Swole</span><span class="g">Mate</span> — every message it can say</h1>
<p class="sub">Top: real previews of the 6 scheduled message types (pulled live from the coach just now). Below: the full roast library, every line numbered.</p>
<div class="howto">🧹 <b>Cleanup mode:</b> tap any line you want changed or killed — it turns pink. When you're done, hit <b>Copy cleanup list</b> at the bottom and paste it back to Claude with your notes (e.g. "GYM_FLOP-3: too mean, soften").</div>
<h2>📱 The 6 scheduled messages — live previews</h2>
<div class="phones">""")
for label, msgs in samples:
    parts.append(f'<div class="phone"><div class="plabel">{html.escape(label)}</div>')
    for msg in msgs[:3]:
        parts.append(f'<div class="bub">{wa(msg)}</div>')
    parts.append("</div>")
parts.append("</div><h2>🗯️ The roast library</h2>")
for gname, keys in GROUPS:
    parts.append(f"<h3>{html.escape(gname)}</h3>")
    for k in keys:
        if k not in CATS:
            continue
        parts.append(f'<div style="margin:14px 0 4px;font-weight:700;font-size:14px">{html.escape(NICE.get(k,k))}<span class="cat">{k} · {len(CATS[k])} lines</span></div>')
        for i, line in enumerate(CATS[k], 1):
            lid = f"{k}-{i}"
            parts.append(f'<div class="line" data-id="{lid}" onclick="tog(this)"><span class="id">{lid}</span><span class="tx">{html.escape(line)}</span></div>')
total = sum(len(v) for v in CATS.values())
parts.append(f"""
<p class="note" style="margin-top:30px">{total} library lines · {len(CATS)} categories · previews pulled {json.dumps('2026-07-14')} · placeholders like {{name}}/{{g}}/{{c}} get filled with real numbers at send time.</p>
</div>
<div class="bar"><span class="n" id="cnt">0 flagged</span>
<button class="btn" onclick="copyList()">Copy cleanup list</button>
<button class="btn alt" onclick="clearAll()">Clear</button>
<span class="note" id="copied"></span></div>
<script>
function tog(el){{el.classList.toggle('flag');update();}}
function update(){{document.getElementById('cnt').textContent=document.querySelectorAll('.line.flag').length+' flagged';}}
function copyList(){{const ids=[...document.querySelectorAll('.line.flag')].map(e=>e.dataset.id);
const txt='CLEANUP LIST:\\n'+ids.map(i=>'- '+i).join('\\n');
navigator.clipboard.writeText(txt).then(()=>{{document.getElementById('copied').textContent='✓ copied '+ids.length+' — paste it to Claude';}});}}
function clearAll(){{document.querySelectorAll('.line.flag').forEach(e=>e.classList.remove('flag'));update();document.getElementById('copied').textContent='';}}
</script>""")
out = os.path.join(FA, "message-review.html")
io.open(out, "w", encoding="utf-8").write("".join(parts))
print("wrote", out, round(os.path.getsize(out)/1024), "KB ·", total, "lines ·", len(samples), "mode previews")
