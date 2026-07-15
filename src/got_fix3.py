#!/usr/bin/env python3
# got_fix3.py — round-3 prop/hand fixes. Edit f2/f3 FROM f1 to lock held props; single-object constraints.
import os, json, base64, glob, time, urllib.request
from PIL import Image, ImageDraw
URL="https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC="generated"; GENDER={"medi":"M","teyaum":"M","gizem":"F","rinad":"F"}; PEOPLE=["medi","teyaum","gizem","rinad"]
RETRIES=5; OUT_W,MS=420,150
TH=" The figure has EXACTLY TWO hands total — never a third/duplicate/ghost hand."
MEDI_L9_F2=("keep the royal scepter planted in the SAME hand and EXACT position as the reference — do NOT move it, raise it, switch hands, or duplicate it. "
            "Raise the OTHER, empty hand palm-out in a commanding decree."+TH)
MEDI_L9_F3=("keep the royal scepter planted in the SAME hand and EXACT position as the reference — do NOT move it, switch hands, or duplicate it. "
            "Rest the other hand on the throne arm with an imperious satisfied nod."+TH)
TEY_L8_F2=("HOISTING the warhammer high overhead with both arms, roaring, muscles straining. The warhammer has EXACTLY ONE head at the TOP of its handle — "
           "do NOT draw a second hammer head at the bottom of the handle or anywhere else. One single hammer only.")
TEY_L8_F3=("swinging the warhammer to rest on one shoulder with a fierce glare. The warhammer has EXACTLY ONE head — never a second or duplicate head. One single hammer only.")
L3_F2=("keep the wooden tankard gripped in the SAME hand and EXACT position as the reference — it must stay HELD in the hand, never floating in the air, never switching hands. "
       "Wipe the brow with the OTHER free hand, a weary unhappy sigh."+TH)
L3_F3=("keep the wooden tankard gripped in the SAME hand and EXACT position as the reference — HELD in the hand, never floating, never switching hands. "
       "The other hand rests, shoulders drooping, glum."+TH)
GIZ_L4_F2=("she holds ONE single wooden spear in her hands — do NOT draw a second, smaller, tiny, or duplicate spear anywhere. "
           "Flinching backward, gripping the one spear tighter, eyes wide with fear.")
GIZ_L4_F3=("she holds ONE single wooden spear — do NOT draw a second, tiny, or duplicate spear anywhere. "
           "Sinking into a timid uncertain guard, knees bent, trembling nervously.")
RIN_L1_F2=("she has EXACTLY TWO hands: one hand holds the wooden bowl, the other lifts a spoon toward her mouth. "
           "Do NOT leave a third or ghost hand resting on the bowl. Grimacing in disgust."+TH)
# (name,lvl,frame,source,pose)
FIXES=[
 ("medi",9,2,"medi-got-L09-f1.png",MEDI_L9_F2),
 ("medi",9,3,"medi-got-L09-f1.png",MEDI_L9_F3),
 ("teyaum",8,2,"teyaum-got-L08.png",TEY_L8_F2),
 ("teyaum",8,3,"teyaum-got-L08.png",TEY_L8_F3),
 ("teyaum",3,2,"teyaum-got-L03-f1.png",L3_F2),
 ("teyaum",3,3,"teyaum-got-L03-f1.png",L3_F3),
 ("gizem",4,2,"gizem-got-L04.png",GIZ_L4_F2),
 ("gizem",4,3,"gizem-got-L04.png",GIZ_L4_F3),
 ("gizem",3,2,"gizem-got-L03-f1.png",L3_F2),
 ("gizem",3,3,"gizem-got-L03-f1.png",L3_F3),
 ("rinad",1,2,"rinad-got-L01.png",RIN_L1_F2),
 ("rinad",3,2,"rinad-got-L03-f1.png",L3_F2),
 ("rinad",3,3,"rinad-got-L03-f1.png",L3_F3),
]
def guard(name,i):
    m=(" Her gown/tunic/rags/armor stay fully INTACT and cover her chest — never rip or show breasts/nipples/cleavage." if GENDER.get(name)=="F" else "")
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
# rebuild touched gifs + proof sheets
pairs=sorted(set((n,l) for n,l,_,_,_ in FIXES))
sz=[Image.open(p).size for p in glob.glob(os.path.join(SRC,"*-got-L[0-9][0-9]-f[0-9].png"))]
gw,gh=max(w for w,h in sz),max(h for w,h in sz)
for name,t in pairs:
    fp=[os.path.join(SRC,f"{name}-got-L{t:02d}-f{i}.png") for i in (1,2,3)]
    frames=[]
    for x in fp:
        im=Image.open(x).convert("RGBA"); bg=im.getpixel((2,2)); c=Image.new("RGBA",(gw,gh),bg)
        c.alpha_composite(im,((gw-im.width)//2,gh-im.height)); ow=OUT_W; oh=int(gh*ow/gw); oh-=oh%2
        frames.append(c.resize((ow,oh),Image.LANCZOS).convert("RGB").convert("P",palette=Image.ADAPTIVE,colors=256))
    out=os.path.join(SRC,f"{name}-got-L{t:02d}.gif")
    frames[0].save(out,save_all=True,append_images=frames[1:],duration=MS,loop=0,disposal=2,optimize=True); print("GIF",os.path.basename(out),flush=True)
    W=230; ims=[Image.open(x).convert("RGB") for x in fp]; cs=[im.resize((W,int(im.height*W/im.width))) for im in ims]
    h=max(c.height for c in cs); sheet=Image.new("RGB",(3*W,h),(18,15,26))
    for j,c in enumerate(cs): sheet.paste(c,(j*W,h-c.height))
    sheet.save(os.path.join(SRC,f"FIX3-{name}-L{t:02d}.png"))
print("DONE",flush=True)
