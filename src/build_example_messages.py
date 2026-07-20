#!/usr/bin/env python3
# example-messages.html — an ASPIRATIONAL "dream week" mockup of every SwoleMate message with all 4
# participating: realistic fabricated numbers (clearly labeled), avatar GIFs in the ladder messages,
# and group replies for vibe. Static file; no connector calls.
import io, os, base64, html
from PIL import Image, ImageSequence
FA = os.path.dirname(os.path.abspath(__file__))
AV = os.path.join(FA, "Avatars", "generated")
def gif(path, w=96):
    im = Image.open(path); frames = []; durs = []
    for fr in ImageSequence.Iterator(im):
        f = fr.convert("RGB"); h = int(f.height * w / f.width)
        frames.append(f.resize((w, h), Image.LANCZOS)); durs.append(fr.info.get("duration", 150))
    q = [f.convert("P", palette=Image.ADAPTIVE, colors=48) for f in frames]
    buf = io.BytesIO(); q[0].save(buf, format="GIF", save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=2, optimize=True)
    return "data:image/gif;base64," + base64.b64encode(buf.getvalue()).decode()

def B(t): return t  # bubbles written as HTML directly

def av_row(key, set_, lvl, arrow, name, title, note):
    return (f'<div class="avrow"><img src="{gif(os.path.join(AV, f"{key}-{set_}-L{lvl:02d}.gif"))}">'
            f'<div>{arrow} <b>{name}</b> — <b>L{lvl}: {title}</b><br><i class="rz">{note}</i></div></div>')

# ---------- 10:00 AM batch ----------
daily_read = """<span class="hd">☀️ THE DAILY READ · yesterday</span><br><br>
<b>Teyaum</b> ✨385<br>📝✅ 🥩186g✅ 🍽️2,470cal✅ 🏃162min✅ · 🏋️3✅<br><i class="rz">mother served. everyone else take notes. 📝🔥</i><br><br>
<b>Medi</b> ✨362<br>📝✅ 🥩205g✅ 🍽️2,280cal✅ 👟9.1k✅ · 🏋️2❌<br><i class="rz">that's a 10/10 no-flop day. the discipline is DELICIOUS 😋</i><br><br>
<b>Rinad</b> ✨318<br>📝✅ 🥩122g✅ 🍽️1,540cal✅ 👟8.4k✅ · 🏋️1❌<br><i class="rz">green across the board 🟢 said "watch this" and DELIVERED. big slay</i><br><br>
<b>Gizem</b> ✨141<br>📝✅ 🥩74g❌ 🍽️1,210cal❌ 👟4.6k❌ · 🏋️0❌<br><i class="rz">today was a rough draft. tomorrow better be the final. 📝</i>"""
wtd = """<span class="hd">📊 WEEK SO FAR · avg/day</span><br><br>
<b>Teyaum</b>  (5/5)<br>🥩184g✅ 🍽️2,455cal✅ 🏃418min✅ · 🏋️3✅ · 📝3/3✅<br><br>
<b>Medi</b>  (4/5)<br>🥩198g✅ 🍽️2,310cal✅ 👟8.6k✅ · 🏋️2❌ · 📝3/3✅<br><br>
<b>Rinad</b>  (4/5)<br>🥩119g✅ 🍽️1,505cal✅ 👟7.9k❌ · 🏋️1✅ · 📝3/3✅<br><br>
<b>Gizem</b>  (1/5)<br>🥩81g❌ 🍽️1,180cal❌ 👟5.0k❌ · 🏋️0❌ · 📝2/3✅"""
gap = """<span class="hd">🎯 CLOSE THE GAP · lock in for the rest of the week</span><br><br>
<b>Teyaum</b><br>  🎯 on pace — keep it up<br><br>
<b>Medi</b><br>  🏋️ 1 more session to hit your 3 this week<br><br>
<b>Rinad</b><br>  👟 walk 8.2k/day the rest of the week<br>  🏋️ 2 more sessions — get busy 😤<br><br>
<b>Gizem</b><br>  🥩 128g protein/day to catch up<br>  🍽️ don't starve yourself 🍗 you can eat up to 1,680cal/day — muscles need fuel<br>  👟 walk 9.4k/day the rest of the week"""
ladder = ('<span class="hd">⚡ THE LADDER · daily avatar</span><br><br>'
  + av_row("rinad","pixel",9,"🔺","Rinad","Deadlift Beast","ascending!! gagged")
  + av_row("medi","pixel",7,"🔺","Medi","Pumped","up a level. mother is EVOLVING")
  + av_row("teyaum","pixel",6,"🔺","Teyaum","Warming Up","climbed. the glow-up is REAL")
  + av_row("gizem","pixel",4,"🔻","Gizem","Donut Sulker","slipped a level. gravity said hi 💀")
  + '<div class="foot"><i>hit your day (cals · protein · steps, all within 5%) = climb. miss = sink. L1 Jabba the Hutt ⇄ L10 SUPER SAIYAN</i></div>')

# ---------- meal checks ----------
meal_am = """<span class="hd">🍳 DID YOU EAT? · breakfast + lunch check</span><br><br><b>Gizem</b> — breakfast? lunch? hello?? your food log is a ghost town 👻"""
meal_pm = """<span class="hd">🍽️ DINNER CHECK</span><br><br><b>Gizem</b> — calories suspiciously low for this hour. log that dinner 👀<br><br><b>Rinad</b> — day's looking light — did dinner get logged, or ghosted? 🍽️"""

# ---------- Monday 12 PM batch ----------
lastweek = """<span class="hd">🏁 LAST WEEK'S RESULTS · avg/day</span><br><br>
🥇 <b>Teyaum</b> 5/5 — 👑 Bragging Rights of the Week<br>🥩182g✅ 🍽️2,490cal✅ 🏃465min✅ · 🏋️4✅ · 📝7/7✅<br><br>
🥈 <b>Medi</b> 4/5<br>🥩201g✅ 🍽️2,260cal✅ 👟8.3k✅ · 🏋️2❌ · 📝7/7✅<br><br>
🥉 <b>Rinad</b> 3/5<br>🥩116g❌ 🍽️1,520cal✅ 👟8.1k✅ · 🏋️3✅ · 📝5/7❌<br><br>
💩 <b>Gizem</b> 2/5 — crickets 🦗<br>🥩88g❌ 🍽️1,340cal❌ 👟5.8k❌ · 🏋️1✅ · 📝6/7✅"""
season = """<span class="hd">🏆 THE CHALLENGE · Week 3 of 8</span><br><br>
1. <b>Teyaum</b> — 8 pts 🥇🥇🥈<br>2. <b>Medi</b> — 6 pts 🥈🥉🥇<br>3. <b>Rinad</b> — 4 pts 🥉🥉🥈<br>4. <b>Gizem</b> — 0 pts 💩💩💩"""
throne = ('<span class="hd">🐉 THE THRONE ROOM · weekly avatar</span><br><br>'
  + av_row("rinad","got",8,"🔺","Rinad","Warden of the Realm","leveled UP. the ladder trembles")
  + av_row("medi","got",6,"🔺","Medi","Anointed Knight","climbed. the glow-up is REAL")
  + av_row("teyaum","got",5,"🔻","Teyaum","Sellsword","dropped. your avatar felt that")
  + av_row("gizem","got",3,"🔻","Gizem","Tavern Servant","sank a rung. embarrassing for you")
  + '<div class="foot"><i>win the week (cals · protein · steps within 5% + gym 100%) to rise from Flea Bottom to the Iron Throne</i></div>')

def phone(label, items):
    b = ""
    for kind, content in items:
        if kind == "coach": b += f'<div class="bub">{content}</div>'
        else:
            who, txt = content
            b += f'<div class="bub me"><b class="who">{who}</b><br>{txt}</div>'
    return f'<div class="phone"><div class="plabel">{label}</div>{b}</div>'

phones = [
 phone("☀️ 10:00 AM · the morning drop (4 messages)", [
   ("coach", daily_read),
   ("reply", ("Teyaum","not me being the group's mother AND its cardio queen 💅")),
   ("coach", wtd), ("coach", gap), ("coach", ladder),
   ("reply", ("Rinad","DEADLIFT BEAST?? framing this")),
   ("reply", ("Gizem","the donut sulker slander is real 😭 ok ok I'm logging")),
 ]),
 phone("🍳 4:30 PM · lunch check", [
   ("coach", meal_am),
   ("reply", ("Gizem","IT WAS ONE BUSY MORNING. logged now 🙄")),
 ]),
 phone("🍽️ 9:30 PM · dinner check", [
   ("coach", meal_pm),
   ("reply", ("Rinad","chicken + rice just went in. check again coward 🐔")),
 ]),
 phone("🏁 MONDAY 12:00 PM · the reckoning (3 messages)", [
   ("coach", lastweek),
   ("coach", f'<img src="{gif(os.path.join(AV,"teyaum-podium.gif"), w=220)}" style="width:75%;border-radius:10px;display:block"><div style="font-size:11px;color:#5f7a70;margin-top:5px"><i>👑 the champion\'s podium drops with the crowning</i></div>'),
   ("reply", ("Teyaum","👑 bow.")),
   ("coach", season), ("coach", throne),
   ("reply", ("Medi","rinad really speedran the whole feudal hierarchy")),
   ("reply", ("Gizem","tavern servant era. pouring ales, plotting revenge 🍺")),
 ]),
]

page = f"""<title>SwoleMate — Example Messages</title>
<style>
:root{{--bg:#0b0910;--panel:#15111d;--line:#2b2340;--ink:#f6f0fc;--muted:#a998c1;--pink:#ff2e88;--green:#00d68f;--gold:#f5b933;--wa:#0a0f0d;--bub:#1f2c26;--mine:#144d37;}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}}
.wrap{{max-width:1120px;margin:0 auto;padding:34px 20px 80px}}
h1{{font-size:clamp(26px,5vw,42px);font-weight:900;letter-spacing:-.03em}}
h1 .p{{color:var(--pink)}} h1 .g{{color:var(--green)}}
.sub{{color:var(--muted);margin-top:8px;max-width:700px;font-size:15px}}
.badge{{display:inline-block;margin-top:14px;background:rgba(245,185,51,.12);border:1px solid rgba(245,185,51,.4);color:var(--gold);border-radius:999px;padding:6px 14px;font-size:12.5px;font-weight:700}}
.phones{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:20px;margin-top:28px;align-items:start}}
.phone{{background:var(--wa);border:8px solid #1b1622;border-radius:26px;padding:10px}}
.plabel{{font-family:ui-monospace,monospace;font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:4px 6px 10px;border-bottom:1px solid rgba(255,255,255,.07);margin-bottom:8px}}
.bub{{background:var(--bub);border-radius:12px;border-top-left-radius:4px;padding:10px 12px;margin:8px 2px;font-size:12.8px;line-height:1.55;word-wrap:break-word}}
.bub.me{{background:var(--mine);border-top-left-radius:12px;border-top-right-radius:4px;margin-left:38px}}
.hd{{font-weight:800;color:var(--gold)}}
.rz{{color:#8fe9c8}}
.who{{color:#7fc7ff;font-size:11px}}
.avrow{{display:flex;gap:10px;align-items:center;margin:10px 0}}
.avrow img{{width:58px;border-radius:9px;image-rendering:pixelated;flex:0 0 58px}}
.foot{{font-size:11px;color:#5f7a70;margin-top:8px}}
.note{{text-align:center;color:var(--muted);font-size:12.5px;margin-top:40px}}
</style>
<div class="wrap">
<h1><span class="p">Swole</span><span class="g">Mate</span> — a day in the dream life 💬</h1>
<p class="sub">Every scheduled message, mocked the way we hope it looks once all 4 are flowing: full participation, medals, streak avatars, and the group talking back.</p>
<div class="badge">⚠️ EXAMPLE — all numbers fabricated for illustration (real messages live on the Message Review page)</div>
<div class="phones">{"".join(phones)}</div>
<p class="note">Avatar GIFs shown are each person's real generated ladder art at that level · avatars ride as text today, image-attach is the planned upgrade</p>
</div>"""
out = os.path.join(FA, "example-messages.html")
io.open(out, "w", encoding="utf-8").write(page)
print("wrote", out, round(os.path.getsize(out)/1024), "KB")
