#!/usr/bin/env python3
# Round-4: (a) prop fixes locked off frame 1 (teyaum L8 hammer, medi L9 scepter-left, gizem L4 one-spear);
# (b) REBUILD every GoT + SS gif at its OWN natural aspect (no shared canvas / no padding bars) -> full-frame, no crop.
import os, json, base64, time, urllib.request
from PIL import Image, ImageDraw
URL="https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC="generated"; GENDER={"medi":"M","teyaum":"M","gizem":"F","rinad":"F"}; PEOPLE=["medi","teyaum","gizem","rinad"]
RETRIES=6; OUT_W,MS=440,150
TH=" The figure has EXACTLY TWO hands total — never a third/duplicate/ghost hand."
MEDI_L9_F1=("hold the royal scepter gripped firmly in his hand on the LEFT side of the image, the scepter shaft vertical along the LEFT, his hand closed around it; "
            "the other (right-side) hand rests on the right throne arm. Regal and still."+TH)
MEDI_L9_F2=("keep the royal scepter gripped in the EXACT same hand and position on the LEFT side of the image — do NOT move it, switch sides or hands, or duplicate it. "
            "Raise the RIGHT-side hand, palm out, in a commanding decree."+TH)
MEDI_L9_F3=("keep the royal scepter gripped in the EXACT same position on the LEFT side of the image — never move or duplicate it. "
            "The right-side hand rests on the throne arm; imperious satisfied nod."+TH)
TEY_L8_F2=("Keep the warhammer EXACTLY as in the reference — ONE single pole with ONE hammer head at its end, in the SAME position and SAME direction "
           "(do NOT rotate, flip, swing, split, separate the head from the pole, or duplicate it). Change ONLY his body: flex the muscles and roar, fierce open-mouth shout.")
TEY_L8_F3=("Keep the warhammer EXACTLY as in the reference — ONE pole plus ONE head at the end, SAME position and direction (never split, rotate, separate, or duplicate). "
           "Change ONLY his face and stance: a fierce determined glare, chest out.")
GIZ_L4_F2=("Keep the ONE single wooden spear EXACTLY as in the reference — the SAME one spear, do NOT add, duplicate, or draw a second/tiny/extra spear anywhere. "
           "Change ONLY her expression and lean: flinch slightly, eyes wide with fear, unhappy.")
GIZ_L4_F3=("Keep the ONE single wooden spear EXACTLY as in the reference — one spear only, never a second/tiny/duplicate spear. "
           "Change ONLY her stance: sink into a timid nervous crouch, trembling.")
# order matters: medi L9 f1 before its f2/f3
FIXES=[
 ("medi",9,1,"medi-got-L09.png",MEDI_L9_F1),
 ("medi",9,2,"medi-got-L09-f1.png",MEDI_L9_F2),
 ("medi",9,3,"medi-got-L09-f1.png",MEDI_L9_F3),
 ("teyaum",8,2,"teyaum-got-L08-f1.png",TEY_L8_F2),
 ("teyaum",8,3,"teyaum-got-L08-f1.png",TEY_L8_F3),
 ("gizem",4,2,"gizem-got-L04-f1.png",GIZ_L4_F2),
 ("gizem",4,3,"gizem-got-L04-f1.png",GIZ_L4_F3),
]
def guard(name,i):
    m=(" Her gown/tunic/armor stays fully INTACT and covers her chest — never rip or show breasts/nipples/cleavage." if GENDER.get(name)=="F" else "")
    return ("This EXACT pixel-art character. Keep the FACE, identity, hair, skin tone, outfit COLORS, body shape/size, HEIGHT, position, camera "
            "distance/scale and the ENTIRE background completely IDENTICAL to the reference — do not redraw, move, or resize them."+m+
            " This is frame "+str(i)+" of a 3-frame loop of the SAME scene. Change ONLY this pose/action: ")
def call(img,prompt):
    p={"prompt":prompt,"image_base64":base64.b64encode(img).decode(),"mime":"image/png"}
    req=urllib.request.Request(URL,data=json.dumps(p).encode(),headers={"Authorization":"Bearer "+ANON,"apikey":ANON,"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=180); d=json.loads(r.read())
    except Exception as e: return None,repr(e)[:70]
    if not d.get("ok"): return None,"apierr"
    return base64.b64decode(d["image_base64"]),None
for name,lvl,fr,srcname,pose in FIXES:
    sp=os.path.join(SRC,srcname)
    if not os.path.exists(sp): print("NO SRC",srcname,flush=True); continue
    src=open(sp,"rb").read(); op=os.path.join(SRC,f"{name}-got-L{lvl:02d}-f{fr}.png"); ok=False
    for _ in range(RETRIES):
        img,err=call(src,guard(name,fr)+pose+" Keep everything else pixel-identical.")
        if img: open(op,"wb").write(img); print("OK",name,lvl,fr,flush=True); ok=True; break
        time.sleep(3)
    if not ok: print("MISS",name,lvl,fr,err,flush=True)

# ---- natural-aspect rebuild of ALL gifs (both sets), each at its own frame size, common width ----
def build_all():
    for tag in ("got","pixel"):
        for name in PEOPLE:
            for t in range(1,11):
                fp=[os.path.join(SRC,f"{name}-{tag}-L{t:02d}-f{i}.png") for i in (1,2,3)]
                if not all(os.path.exists(x) for x in fp): print("skip",tag,name,t,flush=True); continue
                ims=[Image.open(x).convert("RGB") for x in fp]
                w=OUT_W; h=int(ims[0].height*w/ims[0].width); h-=h%2
                q=[im.resize((w,h),Image.LANCZOS).convert("P",palette=Image.ADAPTIVE,colors=256) for im in ims]
                out=os.path.join(SRC,f"{name}-{tag}-L{t:02d}.gif")
                q[0].save(out,save_all=True,append_images=q[1:],duration=MS,loop=0,disposal=2,optimize=True)
        print("rebuilt",tag,flush=True)
build_all()
# proof sheets for the 3 prop fixes
for name,t in (("medi",9),("teyaum",8),("gizem",4)):
    fp=[os.path.join(SRC,f"{name}-got-L{t:02d}-f{i}.png") for i in (1,2,3)]
    W=230; ims=[Image.open(x).convert("RGB") for x in fp]; cs=[im.resize((W,int(im.height*W/im.width))) for im in ims]
    hh=max(c.height for c in cs); sheet=Image.new("RGB",(3*W,hh),(18,15,26))
    for j,c in enumerate(cs): sheet.paste(c,(j*W,hh-c.height))
    sheet.save(os.path.join(SRC,f"FIX4-{name}-L{t:02d}.png"))
print("DONE",flush=True)
