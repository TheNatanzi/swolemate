#!/usr/bin/env python3
# Build a self-contained HTML gallery of all 40 animated GoT avatars (web-sized, base64-embedded).
import os, io, base64, html
from PIL import Image, ImageSequence
SRC="generated"; OUT=os.path.join(os.path.dirname(__file__) or ".","got-gallery.html")
PEOPLE=[("medi","Medi","M","#5b8cff"),("teyaum","Teyaum","M","#3ec8c0"),
        ("gizem","Gizem","F","#b07bff"),("rinad","Rinad","F","#ff7bb0")]
NM={1:("Flea Bottom Peasant","Flea Bottom Peasant"),2:("Gutter Urchin","Gutter Urchin"),
    3:("Tavern Servant","Tavern Servant"),4:("Conscript Spearman","Conscript Spearwoman"),
    5:("Sellsword","Sellsword"),6:("Anointed Knight","Anointed Knight"),
    7:("Landed Lord","Landed Lady"),8:("Warden of the Realm","Warden of the Realm"),
    9:("Crowned King","Crowned Queen"),10:("Targaryen Dragonlord","Targaryen Dragon Queen")}
def datauri(path,w=190):
    im=Image.open(path); frames=[]; durs=[]
    for fr in ImageSequence.Iterator(im):
        f=fr.convert("RGB"); h=int(f.height*w/f.width); frames.append(f.resize((w,h),Image.LANCZOS)); durs.append(fr.info.get("duration",150))
    q=[f.convert("P",palette=Image.ADAPTIVE,colors=64) for f in frames]; buf=io.BytesIO()
    q[0].save(buf,format="GIF",save_all=True,append_images=q[1:],duration=durs,loop=0,disposal=2,optimize=True)
    return "data:image/gif;base64,"+base64.b64encode(buf.getvalue()).decode()
cards=[]
for key,disp,g,accent in PEOPLE:
    cells=[]
    for lvl in range(1,11):
        uri=datauri(os.path.join(SRC,f"{key}-got-L{lvl:02d}.gif"))
        nm=NM[lvl][1] if g=="F" else NM[lvl][0]
        cells.append(f'<figure class="cell"><span class="lv">{lvl}</span>'
                     f'<img loading="lazy" src="{uri}" alt="{html.escape(disp)} level {lvl}">'
                     f'<figcaption>{html.escape(nm)}</figcaption></figure>')
    cards.append(f'<section class="person"><h2 style="--accent:{accent}">{html.escape(disp)}</h2>'
                 f'<div class="grid">{"".join(cells)}</div></section>')
sz=0
page=f"""<title>SwoleMate — Weekly Ladder</title>
<style>
:root{{--bg:#0d0b12;--panel:#16121d;--ink:#efe7d8;--muted:#a99f8e;--gold:#d9b062;--line:#2a2233;}}
*{{box-sizing:border-box}}
body{{margin:0;background:radial-gradient(1200px 600px at 50% -10%,#20182b,var(--bg)) fixed;color:var(--ink);
font-family:'Iowan Old Style',Georgia,'Times New Roman',serif;}}
.wrap{{max-width:1180px;margin:0 auto;padding:40px 20px 80px}}
header{{text-align:center;margin-bottom:34px}}
h1{{font-size:clamp(30px,5vw,52px);margin:0 0 6px;letter-spacing:.5px;
background:linear-gradient(#f4e2b3,var(--gold));-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:var(--muted);font-size:15px;max-width:640px;margin:0 auto;line-height:1.5}}
.rule{{margin:20px auto 0;max-width:720px;background:var(--panel);border:1px solid var(--line);border-radius:14px;
padding:14px 18px;color:var(--ink);font-size:14px;line-height:1.6}}
.rule b{{color:var(--gold)}}
.person{{margin-top:40px}}
.person h2{{font-size:24px;margin:0 0 14px;padding-left:12px;border-left:4px solid var(--accent);color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}}
.cell{{position:relative;margin:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;
overflow:hidden;text-align:center;transition:transform .15s,border-color .15s}}
.cell:hover{{transform:translateY(-3px);border-color:var(--gold)}}
.cell img{{width:100%;display:block}}
.lv{{position:absolute;top:8px;left:8px;z-index:2;background:rgba(0,0,0,.66);color:var(--gold);
border:1px solid var(--gold);border-radius:50%;width:26px;height:26px;line-height:24px;font-size:13px;font-weight:700}}
figcaption{{padding:8px 6px 10px;font-size:12.5px;color:var(--muted);line-height:1.3}}
footer{{text-align:center;color:var(--muted);font-size:12.5px;margin-top:50px}}
</style>
<div class="wrap">
<header>
<h1>The Weekly Ladder</h1>
<p class="sub">SwoleMate's <b style="color:var(--gold)">weekly-streak</b> avatar set — Game of Thrones. Flea Bottom peasant to Targaryen dragon-monarch. (Daily streaks use the Super Saiyan set.)</p>
<div class="rule"><b>How you climb:</b> everyone starts at <b>Level 5</b>. Hit your week → <b>+1 level</b>. Miss it → <b>−1 level</b>. A week counts only if calories, protein, steps/cardio are all within 5% of goal <b>and</b> gym is 100%+.</div>
</header>
{"".join(cards)}
<footer>40 avatars · 4 warriors · 10 tiers each · pixel-art, real-motion loops</footer>
</div>"""
open(OUT,"w",encoding="utf-8").write(page)
print("wrote",OUT,round(len(page)/1024/1024,2),"MB")
