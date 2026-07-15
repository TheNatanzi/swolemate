#!/usr/bin/env python3
# got_fix2.py — round-2 fixes:
#  - ALL L10 f3: dragon keeps breathing fire (edit from f2, only lower the monarch's hand to grip) -> f2 & f3 both flames
#  - Rinad L10 f1/f2/f3: dragon locked to ONE fixed spot (f2 from f1, f3 from f2), f2 & f3 flames
#  - Teyaum L9 f2: kill ghost hand (exactly two hands)
# Each fix names its OWN source image so we can chain edits. Then rebuild L09/L10 gifs + proof sheets.
import os, json, base64, glob, time, urllib.request
from PIL import Image, ImageDraw
URL="https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC="generated"; GENDER={"medi":"M","teyaum":"M","gizem":"F","rinad":"F"}; PEOPLE=["medi","teyaum","gizem","rinad"]
RETRIES=5; OUT_W,MS=420,150
TH=" The figure has EXACTLY TWO hands total — never a third/duplicate/ghost hand."
GUY_F3=("Keep the DRAGON and its blazing FIRE-BREATH, the throne, crown, armor, face and background EXACTLY as the reference. "
        "Change ONLY the monarch's raised hand: lower it to grip the throne armrest so BOTH hands grip the throne arms with a powerful commanding glare."+TH)
RIN_F1=("the dragon behind sits at a FIXED forward-facing position (this exact spot & size for the whole loop), mouth CLOSED, NO fire; "
        "the monarch seated calmly with both hands resting on the throne arms, embers gently drifting."+TH)
RIN_F2=("Keep the DRAGON in the EXACT same position and size as the reference — do NOT move, turn or resize it. Now the dragon opens its mouth and "
        "BREATHES A BLAST OF FIRE straight forward; the monarch raises ONE hand up off the armrest in a commanding gesture, the other hand still resting on the throne arm."+TH)
RIN_F3=("Keep the DRAGON and its FIRE-BREATH in the EXACT same position and size as the reference — do NOT move or resize it. "
        "Change ONLY the monarch's raised hand: lower it to grip the throne armrest so both hands grip the throne arms with a commanding glare."+TH)
TEY_L9_F2=("lifting the royal scepter HIGHER in the SAME single hand as the reference (do NOT switch hands, do NOT draw a second scepter), and raising the OTHER, "
           "EMPTY hand palm-out in a decree. Exactly TWO hands — one holding the scepter, one empty — never a third or ghost hand on the armrest or lap.")
# (name, lvl, frame, source_filename, pose)  — ORDER MATTERS (rinad chain)
FIXES=[
 ("medi",10,3,"medi-got-L10-f2.png",GUY_F3),
 ("teyaum",10,3,"teyaum-got-L10-f2.png",GUY_F3),
 ("gizem",10,3,"gizem-got-L10-f2.png",GUY_F3),
 ("rinad",10,1,"rinad-got-L10.png",RIN_F1),
 ("rinad",10,2,"rinad-got-L10-f1.png",RIN_F2),
 ("rinad",10,3,"rinad-got-L10-f2.png",RIN_F3),
 ("teyaum",9,2,"teyaum-got-L09.png",TEY_L9_F2),
]
def guard(name,i):
    m=(" Her gown/robes/armor stay fully INTACT and cover her chest — never rip or show breasts/nipples/cleavage." if GENDER.get(name)=="F" else "")
    return ("This EXACT pixel-art character. Keep the FACE, identity, hair, skin tone, outfit COLORS, body shape/size, HEIGHT, position, camera "
            "distance/scale and the ENTIRE background completely IDENTICAL to the reference — do not redraw, move, or resize them."+m+
            " This is frame "+str(i)+" of a 3-frame loop of the SAME scene. Change ONLY this pose/action: ")
def call(img,prompt):
    p={"prompt":prompt,"image_base64":base64.b64encode(img).decode(),"mime":"image/png"}
    req=urllib.request.Request(URL,data=json.dumps(p).encode(),headers={"Authorization":"Bearer "+ANON,"apikey":ANON,"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=180); d=json.loads(r.read())
    except Exception as e:
        return None,repr(e)[:70]
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
# rebuild L09 + L10 gifs (all people) at existing global canvas
sz=[Image.open(p).size for p in glob.glob(os.path.join(SRC,"*-got-L[0-9][0-9]-f[0-9].png"))]
gw,gh=max(w for w,h in sz),max(h for w,h in sz)
for name in PEOPLE:
    for t in (9,10):
        fp=[os.path.join(SRC,f"{name}-got-L{t:02d}-f{i}.png") for i in (1,2,3)]
        frames=[]
        for x in fp:
            im=Image.open(x).convert("RGBA"); bg=im.getpixel((2,2)); c=Image.new("RGBA",(gw,gh),bg)
            c.alpha_composite(im,((gw-im.width)//2,gh-im.height)); ow=OUT_W; oh=int(gh*ow/gw); oh-=oh%2
            frames.append(c.resize((ow,oh),Image.LANCZOS).convert("RGB").convert("P",palette=Image.ADAPTIVE,colors=256))
        out=os.path.join(SRC,f"{name}-got-L{t:02d}.gif")
        frames[0].save(out,save_all=True,append_images=frames[1:],duration=MS,loop=0,disposal=2,optimize=True); print("GIF",os.path.basename(out),flush=True)
# proof sheets
for t in (9,10):
    W=220; rows=[]
    for name in PEOPLE:
        ims=[Image.open(os.path.join(SRC,f"{name}-got-L{t:02d}-f{i}.png")).convert("RGB") for i in (1,2,3)]
        cs=[im.resize((W,int(im.height*W/im.width))) for im in ims]; h=max(c.height for c in cs)
        row=Image.new("RGB",(3*W+70,h),(18,15,26)); d=ImageDraw.Draw(row); d.text((6,h//2-4),name,fill=(255,210,120))
        for j,c in enumerate(cs): row.paste(c,(70+j*W,h-c.height))
        rows.append(row)
    TT=sum(r.height for r in rows); sheet=Image.new("RGB",(3*W+70,TT),(10,8,14)); y=0
    for r in rows: sheet.paste(r,(0,y)); y+=r.height
    sheet.save(os.path.join(SRC,f"FIX2-L{t:02d}-sheet.png"))
print("DONE",flush=True)
