#!/usr/bin/env python3
# Builds: (1) Super Saiyan daily-ladder gallery, (2) updated TEASER pitch deck (L5 peek only),
# (3) DETAILED pitch deck (embeds Medi's two full animated ladders). Keeps old decks untouched.
import os, io, base64, html as H
from PIL import Image, ImageSequence
SRC="Avatars/generated"
PEOPLE=[("medi","Medi","#5b8cff"),("teyaum","Teyaum","#3ec8c0"),("gizem","Gizem","#b07bff"),("rinad","Rinad","#ff7bb0")]
SSNAMES={1:"Jabba the Hutt",2:"Soda Slob",3:"Fry Fiend",4:"Donut Sulker",5:"Fresh Start",
         6:"Warming Up",7:"Pumped",8:"Iron Presser",9:"Deadlift Beast",10:"Super Saiyan"}
def datauri(path,w=190,colors=64):
    im=Image.open(path); frames=[]; durs=[]
    for fr in ImageSequence.Iterator(im):
        f=fr.convert("RGB"); h=int(f.height*w/f.width); frames.append(f.resize((w,h),Image.LANCZOS)); durs.append(fr.info.get("duration",150))
    q=[f.convert("P",palette=Image.ADAPTIVE,colors=colors) for f in frames]; buf=io.BytesIO()
    q[0].save(buf,format="GIF",save_all=True,append_images=q[1:],duration=durs,loop=0,disposal=2,optimize=True)
    return "data:image/gif;base64,"+base64.b64encode(buf.getvalue()).decode()

# ---------- (1) SS daily-ladder gallery ----------
cards=[]
for key,disp,accent in PEOPLE:
    cells=[]
    for lvl in range(1,11):
        uri=datauri(f"{SRC}/{key}-pixel-L{lvl:02d}.gif")
        cells.append(f'<figure class="cell"><span class="lv">{lvl}</span><img loading="lazy" src="{uri}" alt="{disp} {lvl}">'
                     f'<figcaption>{H.escape(SSNAMES[lvl])}</figcaption></figure>')
    cards.append(f'<section class="person"><h2 style="--accent:{accent}">{disp}</h2><div class="grid">{"".join(cells)}</div></section>')
ss=f"""<title>SwoleMate — Daily Ladder</title>
<style>
:root{{--bg:#0f0a08;--panel:#1b1310;--ink:#f7ecdd;--muted:#b6a08c;--gold:#ffb63d;--orange:#ff7a2f;--line:#3a271c;}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(1200px 620px at 50% -10%,#2a1a0f,var(--bg)) fixed;color:var(--ink);font-family:'Iowan Old Style',Georgia,serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:40px 20px 80px}} header{{text-align:center;margin-bottom:30px}}
h1{{font-size:clamp(30px,5vw,52px);margin:0 0 6px;background:linear-gradient(#ffe08a,var(--orange));-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:var(--muted);font-size:15px;max-width:640px;margin:0 auto;line-height:1.5}}
.rule{{margin:20px auto 0;max-width:720px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 18px;font-size:14px;line-height:1.6}}
.rule b{{color:var(--gold)}} .person{{margin-top:40px}} .person h2{{font-size:24px;margin:0 0 14px;padding-left:12px;border-left:4px solid var(--accent);color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}}
.cell{{position:relative;margin:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;text-align:center;transition:transform .15s,border-color .15s}}
.cell:hover{{transform:translateY(-3px);border-color:var(--gold)}} .cell img{{width:100%;display:block;image-rendering:pixelated}}
.lv{{position:absolute;top:8px;left:8px;z-index:2;background:rgba(0,0,0,.66);color:var(--gold);border:1px solid var(--gold);border-radius:50%;width:26px;height:26px;line-height:24px;font-size:13px;font-weight:700;text-align:center}}
figcaption{{padding:8px 6px 10px;font-size:12.5px;color:var(--muted)}} footer{{text-align:center;color:var(--muted);font-size:12.5px;margin-top:50px}}
</style>
<div class="wrap"><header>
<h1>The Daily Ladder</h1>
<p class="sub">SwoleMate's <b style="color:var(--gold)">daily-streak</b> avatar set — Super Saiyan. Jabba the Hutt to blond super-saiyan god. (Weekly streaks use the Game of Thrones set.)</p>
<div class="rule"><b>How you climb:</b> everyone starts at <b>Level 5</b>. Log + hit your day (calories, protein, steps/cardio all within 5%) → <b>+1</b>. Miss it → <b>−1</b>. Floor L1, ceiling L10.</div>
</header>{"".join(cards)}
<footer>40 avatars · 4 warriors · 10 tiers · daily-streak ladder</footer></div>"""
open("Avatars/ss-daily-gallery.html","w",encoding="utf-8").write(ss)
print("SS gallery",round(len(ss)/1024/1024,2),"MB")

# ---------- shared: transform v2 -> new deck (swap hook section + roadmap line + title) ----------
v2=open("swolemate-pitch-v2.html","r",encoding="utf-8").read()
def swap_hook(html,new_hook):
    i=html.index("the hook"); s=html.rindex("<section>",0,i); e=html.index("</section>",i)+len("</section>")
    return html[:s]+new_hook+html[e:]
def fix_wording(h):
    # activity pillar = steps OR cardio minutes (per-user choice); show Teyaum as the cardio-min example
    h = h.replace('<div class="e">👟</div><div class="n">Steps</div><div class="d">Move your body</div><div class="tag w">weekly</div>',
                  '<div class="e">👟🏃</div><div class="n">Steps <i>or</i> Cardio</div><div class="d">Your pick: steps/day or cardio min/week</div><div class="tag w">weekly</div>')
    h = h.replace('<div class="t">Apple Health</div><div class="s">steps · no ring needed</div>',
                  '<div class="t">Apple Health</div><div class="s">steps or cardio min · no ring needed</div>')
    h = h.replace('📝✅ 🥩180g✅ 🍽️2,410✅ 👟9.1k✅ · 🏋️2/4', '📝✅ 🥩180g✅ 🍽️2,410✅ 🏃55min✅ · 🏋️2/4')
    h = h.replace('🥩186g✅ 🍽️2,380✅ 👟10.1k✅ · 🏋️4/4✅ · 📝7/7✅', '🥩186g✅ 🍽️2,380✅ 🏃470min✅ · 🏋️4/4✅ · 📝7/7✅')
    h = h.replace('<div class="nm">Teyaum</div><div class="rl">iPhone + Oura</div><div class="src">Cronometer + Oura</div>',
                  '<div class="nm">Teyaum</div><div class="rl">iPhone · tracks cardio minutes</div><div class="src">Cronometer + Apple Health</div>')
    return h

def swap_road(html):
    old=('<b>All 4 pixel avatars</b><span>Every squad member rendered 1→10, face-locked, plus the password-free onboarding page (goals, gender, WhatsApp #, meal times).</span>')
    new=('<b>All 4 avatars — both ladders, animated</b><span>Every squad member rendered across two 10-tier <b>animated</b> ladders (daily Super Saiyan + weekly Game of Thrones), 3-frame motion, face-locked — plus the password-free onboarding page.</span>')
    return html.replace(old,new)

ss_l5=datauri(f"{SRC}/medi-pixel-L05.gif",w=200); got_l5=datauri(f"{SRC}/medi-got-L05.gif",w=200)
TEASER=f"""<section>
  <div class="wrap">
    <div class="eyebrow g rise">the hook</div>
    <h2 class="rise">Your face, as a pixel warrior that levels up — or rots.</h2>
    <p class="lede rise">Everyone sends one selfie. We hand-make a <b>custom animated avatar of you</b> for every tier — <b>two</b> full ladders, 3-frame motion, face-locked. Two streaks, two ways to rise:</p>
    <div class="grid g2 rise" style="margin-top:30px">
      <div class="card" style="text-align:center">
        <div class="num" style="color:var(--gold)">DAILY STREAK</div><h3 style="margin:4px 0 14px">Super Saiyan ladder</h3>
        <img src="{ss_l5}" alt="daily level 5" style="width:150px;border-radius:12px;image-rendering:pixelated">
        <p style="margin-top:12px">Log every day and ascend from Jabba the Hutt to blond super-saiyan. Miss a day, slide back down.</p>
      </div>
      <div class="card" style="text-align:center">
        <div class="num" style="color:var(--blue)">WEEKLY STREAK</div><h3 style="margin:4px 0 14px">Game of Thrones ladder</h3>
        <img src="{got_l5}" alt="weekly level 5" style="width:150px;border-radius:12px;image-rendering:pixelated">
        <p style="margin-top:12px">Win your week and rise from Flea Bottom peasant to a Targaryen dragon-monarch on the Iron Throne.</p>
      </div>
    </div>
    <div class="safe rise" style="margin-top:24px">🐉⚡ <b>40 custom animated avatars per person</b> — 10 tiers × 2 ladders, each a hand-made loop. <b>(Full set shown on request.)</b></div>
  </div>
</section>"""
def strip(name,key):
    cells=""
    for lvl in range(1,11):
        uri=datauri(f"{SRC}/{name}-{key}-L{lvl:02d}.gif",w=140,colors=48)
        cells+=(f'<figure style="margin:0;flex:0 0 82px;position:relative">'
                f'<img src="{uri}" style="width:100%;border-radius:8px;image-rendering:pixelated;display:block">'
                f'<figcaption style="font-family:var(--mono);font-size:10px;color:var(--dim);text-align:center;margin-top:4px">L{lvl}</figcaption></figure>')
    return f'<div style="display:flex;gap:8px;overflow-x:auto;padding:8px 2px 4px">{cells}</div>'
blocks=""
for key_,disp,accent in PEOPLE:
    blocks+=(f'<div style="margin-top:30px">'
             f'<h3 style="font-size:20px;color:#fff;border-left:4px solid {accent};padding-left:12px;margin:0 0 6px">{disp}</h3>'
             f'<div class="mockcap" style="color:var(--gold);margin-top:8px">⚡ daily · super saiyan</div>{strip(key_,"pixel")}'
             f'<div class="mockcap" style="color:var(--blue);margin-top:8px">🐉 weekly · game of thrones</div>{strip(key_,"got")}'
             f'</div>')
DETAILED=f"""<section>
  <div class="wrap">
    <div class="eyebrow g rise">the hook · live avatars</div>
    <h2 class="rise">Four faces. Two ladders each. Twenty tiers of glory and shame.</h2>
    <p class="lede rise">One selfie per person becomes <b>two full hand-made animated ladders</b> — a daily Super Saiyan climb and a weekly Game of Thrones climb, every tier a 3-frame motion loop, face-locked. Scroll each row →</p>
    {blocks}
    <div class="safe rise" style="margin-top:24px">Start at Level 5 · ✅ climbs a tier · ❌ drops one. Miss enough and you're Jabba the Hutt / Flea Bottom peasant; string wins together and you're a super-saiyan / Targaryen dragon-monarch.</div>
  </div>
</section>"""

teaser=fix_wording(swap_road(swap_hook(v2,TEASER)))
detailed=fix_wording(swap_road(swap_hook(v2,DETAILED))).replace("<title>SwoleMate — the pitch</title>","<title>SwoleMate — the pitch (detailed)</title>",1)

# ---- inject the "day in the dream life" example-message chat section (detailed deck only) ----
# Source of truth: example-messages.html (built by build_example_messages.py — run that first).
exp = io.open("example-messages.html", encoding="utf-8").read()
pb = exp.index('<div class="phones">'); pe = exp.index('<p class="note">')
phones_html = exp[pb:pe].strip()
if phones_html.endswith("</div>"): pass
phones_html = phones_html.replace('class="phones"', 'class="xphones"').replace('class="phone"', 'class="xphone"')
XCSS = """<style>
.xphones{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px;margin-top:34px;align-items:start}
.xphone{background:#0a0f0d;border:8px solid #1b1622;border-radius:26px;padding:10px}
.xphone .plabel{font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:4px 6px 10px;border-bottom:1px solid rgba(255,255,255,.07);margin-bottom:8px}
.xphone .bub{background:#1f2c26;border-radius:12px;border-top-left-radius:4px;padding:10px 12px;margin:8px 2px;font-size:12.8px;line-height:1.55;word-wrap:break-word}
.xphone .bub.me{background:#144d37;border-top-left-radius:12px;border-top-right-radius:4px;margin-left:38px}
.xphone .hd{font-weight:800;color:var(--gold)}
.xphone .rz{color:#8fe9c8;font-style:italic}
.xphone .who{color:#7fc7ff;font-size:11px}
.xphone .avrow{display:flex;gap:10px;align-items:center;margin:10px 0}
.xphone .avrow img{width:58px;border-radius:9px;image-rendering:pixelated;flex:0 0 58px}
.xphone .foot{font-size:11px;color:#5f7a70;margin-top:8px}
</style>"""
DREAM = f"""<section>
  <div class="wrap">
    <div class="eyebrow rise">the group chat</div>
    <h2 class="rise">A day in the dream life.</h2>
    <p class="lede rise">What the thread looks like with all four flowing — the 10 AM drop, the meal checks, Monday's reckoning, streak avatars, and the squad talking back. <b>Example numbers.</b></p>
    {XCSS}
    {phones_html}
  </div>
</section>"""
sq = detailed.index('<div class="eyebrow rise">the squad</div>')
ins = detailed.rindex("<section>", 0, sq)
detailed = detailed[:ins] + DREAM + "\n" + detailed[ins:]
open("SwoleMate-Pitch-Updated.html","w",encoding="utf-8").write(teaser)  # NOTE: not "SwoleMate-Pitch.html" — collides w/ old swolemate-pitch.html on case-insensitive Windows
open("SwoleMate-Pitch-Detailed.html","w",encoding="utf-8").write(detailed)
print("teaser",round(len(teaser)/1024/1024,2),"MB · detailed",round(len(detailed)/1024/1024,2),"MB")
