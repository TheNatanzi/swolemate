#!/usr/bin/env python3
# got_fix_frames.py — surgical re-gen of specific problem frames, then rebuild only the affected GIFs.
# Fixes: L10 f2 ghost/3rd hand (all), L9 f2/f3 scepter-hand consistency (all),
#        L6 f2/f3 static knight -> real motion (all), Rinad L10 all 3 (dragon head fixed, closed/open mouth).
import os, json, base64, glob, time, urllib.request, urllib.error
from PIL import Image, ImageDraw
URL="https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC="generated"; GENDER={"medi":"M","teyaum":"M","gizem":"F","rinad":"F"}
PEOPLE=["medi","teyaum","gizem","rinad"]; RETRIES=5; OUT_W,MS=420,150

TWO_HANDS=" The figure has EXACTLY TWO hands total — never draw a third/duplicate/ghost hand."
L6_F2=("lunging into an aggressive combat stance: THRUSTING the longsword forward at full arm extension toward the viewer, "
       "while raising the heraldic shield up across the chest to guard. A clearly dynamic action pose, obviously different from standing still.")
L6_F3=("raising the longsword HIGH overhead gripped ready for an overhead strike, shield arm dropped to the side, "
       "weight shifted onto the front foot in a fierce battle stance. Clearly mid-action, not standing at attention.")
L9_F2=("lifting the royal scepter HIGHER while keeping it in the SAME hand as the reference (do NOT switch it to the other hand, "
       "do NOT draw a second scepter), and raising the OTHER empty hand palm-out in a commanding decree."+TWO_HANDS)
L9_F3=("bringing the royal scepter back to upright in that SAME single hand, the other hand resting on the throne arm, "
       "an imperious satisfied nod. The scepter stays in one hand only, never duplicated or swapped."+TWO_HANDS)
L10_F2=("the DRAGON behind rears up and BREATHES A BLAST OF FIRE from its open mouth (its head staying in the SAME position, not turning away). "
        "The monarch raises ONE hand UP OFF the armrest in a commanding gesture so that armrest is now EMPTY, while the other hand still rests on the opposite throne arm. "
        "Embers blazing brighter."+TWO_HANDS)
RIN_F1=("the monarch seated calmly with both hands resting on the throne arms; the dragon behind faces FORWARD with its mouth CLOSED, embers gently drifting. "
        "Dragon head in a fixed forward position."+TWO_HANDS)
RIN_F2=("the dragon (head in the SAME fixed forward position, NOT turning its face) opens its mouth and BREATHES A BLAST OF FIRE straight out; "
        "the monarch raises ONE hand up off the armrest in a commanding gesture, the other hand still on the throne arm. Embers blazing bright."+TWO_HANDS)
RIN_F3=("the dragon (same fixed forward head position) closes its mouth again with the fire gone; the monarch grips both throne arms with a powerful commanding glare."+TWO_HANDS)

FIXES=[]
for n in PEOPLE:
    FIXES+=[(n,6,2,L6_F2),(n,6,3,L6_F3),(n,9,2,L9_F2),(n,9,3,L9_F3)]
for n in ["medi","teyaum","gizem"]:
    FIXES.append((n,10,2,L10_F2))
FIXES+=[("rinad",10,1,RIN_F1),("rinad",10,2,RIN_F2),("rinad",10,3,RIN_F3)]

def guard(name,i):
    m=(" Her tunic/gown/robes/armor stay fully INTACT and cover her chest — never rip, never show breasts/nipples/cleavage." if GENDER.get(name)=="F" else "")
    return ("This EXACT pixel-art character. Keep the FACE, identity, hair, skin tone, the outfit and its COLORS, body shape/size, HEIGHT, "
            "position, camera distance/scale and the ENTIRE background/setting completely IDENTICAL to the reference — do not redraw, move, or resize them."+m+
            " This is frame "+str(i)+" of a 3-frame loop of the SAME scene. Change ONLY this pose/action: ")
def call(img,prompt):
    payload={"prompt":prompt,"image_base64":base64.b64encode(img).decode(),"mime":"image/png"}
    req=urllib.request.Request(URL,data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+ANON,"apikey":ANON,"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=180); d=json.loads(r.read())
    except Exception as e:
        return None,repr(e)[:70]
    if not d.get("ok"): return None,"apierr"
    return base64.b64decode(d["image_base64"]),None

# regenerate each fix frame FROM the level anchor (clean 2-hand base)
for name,lvl,fr,pose in FIXES:
    ap=os.path.join(SRC,f"{name}-got-L{lvl:02d}.png"); anchor=open(ap,"rb").read()
    op=os.path.join(SRC,f"{name}-got-L{lvl:02d}-f{fr}.png"); ok=False
    for _ in range(RETRIES):
        img,err=call(anchor,guard(name,fr)+pose+" Keep everything else pixel-identical.")
        if img: open(op,"wb").write(img); print("OK",name,lvl,fr,flush=True); ok=True; break
        time.sleep(3)
    if not ok: print("MISS",name,lvl,fr,err,flush=True)

# rebuild affected GIFs (L6,L9,L10 for all) at the existing global canvas size
def gsize():
    sz=[Image.open(p).size for p in glob.glob(os.path.join(SRC,"*-got-L[0-9][0-9]-f[0-9].png"))]
    return (max(w for w,h in sz),max(h for w,h in sz))
gw,gh=gsize()
for name in PEOPLE:
    for t in (6,9,10):
        fp=[os.path.join(SRC,f"{name}-got-L{t:02d}-f{i}.png") for i in (1,2,3)]
        frames=[]
        for x in fp:
            im=Image.open(x).convert("RGBA"); bg=im.getpixel((2,2))
            c=Image.new("RGBA",(gw,gh),bg); c.alpha_composite(im,((gw-im.width)//2,gh-im.height))
            ow=OUT_W; oh=int(gh*ow/gw); oh-=oh%2; c=c.resize((ow,oh),Image.LANCZOS)
            frames.append(c.convert("RGB").convert("P",palette=Image.ADAPTIVE,colors=256))
        out=os.path.join(SRC,f"{name}-got-L{t:02d}.gif")
        frames[0].save(out,save_all=True,append_images=frames[1:],duration=MS,loop=0,disposal=2,optimize=True)
        print("GIF",os.path.basename(out),flush=True)

# proof sheets: one per fixed level, 4 people (rows) x 3 frames
for t in (6,9,10):
    W=220; rows=[]
    for name in PEOPLE:
        ims=[Image.open(os.path.join(SRC,f"{name}-got-L{t:02d}-f{i}.png")).convert("RGB") for i in (1,2,3)]
        cs=[im.resize((W,int(im.height*W/im.width))) for im in ims]; h=max(c.height for c in cs)
        row=Image.new("RGB",(3*W+70,h),(18,15,26)); d=ImageDraw.Draw(row); d.text((6,h//2-4),name,fill=(255,210,120))
        for j,c in enumerate(cs): row.paste(c,(70+j*W,h-c.height))
        rows.append(row)
    TW=3*W+70; TH=sum(r.height for r in rows); sheet=Image.new("RGB",(TW,TH),(10,8,14)); y=0
    for r in rows: sheet.paste(r,(0,y)); y+=r.height
    sheet.save(os.path.join(SRC,f"FIX-L{t:02d}-sheet.png"))
print("DONE",flush=True)
