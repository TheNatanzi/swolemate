#!/usr/bin/env python3
# Round-5: teyaum L8 hammer -> ONE head (top only) + off-hand MOTION; gizem L4 -> ONE spear + off-hand MOTION.
# f1 = establish (allow weapon edit); f2/f3 = lock weapon+main hand, animate the OFF hand + face.
import os, json, base64, time, urllib.request
from PIL import Image
URL="https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC="generated"; GENDER={"gizem":"F"}; RETRIES=6; OUT_W,MS=440,150
TEY_F1=("Fix the warhammer so it has a SINGLE hammer head mounted ONLY at the TOP end of the pole; REMOVE any hammer head from the BOTTOM end, leaving just a plain bare wooden pole tip there (one head total, at the top). "
        "He holds the warhammer upright in his RIGHT hand only; his LEFT (off) hand hangs relaxed at his side. Fierce ready stance.")
TEY_F2=("Keep the warhammer (ONE head at the top only, held in his right hand), his right arm, body, armor and the background EXACTLY as the reference — do NOT change the hammer, add a bottom head, or duplicate it. "
        "Change ONLY his LEFT (off) hand and face: raise the left fist up in a powerful flex, roaring with an open mouth.")
TEY_F3=("Keep the warhammer (ONE head at the top only, in his right hand) and everything else EXACTLY as the reference — no second/bottom head, no duplicate. "
        "Change ONLY his LEFT (off) hand and face: pump the left fist forward with a fierce determined glare.")
GIZ_F1=("Make sure she holds exactly ONE single wooden spear in her RIGHT hand — REMOVE any second, extra, tiny, or duplicate spear so only ONE spear remains in the whole image. "
        "Her LEFT (off) hand hangs at her side. Nervous, scared, unhappy face.")
GIZ_F2=("Keep the ONE single spear in her right hand and everything else EXACTLY as the reference — do NOT add any second/tiny/duplicate spear. "
        "Change ONLY her LEFT (off) hand and face: raise the left hand up in a nervous warding gesture, eyes wide with fear.")
GIZ_F3=("Keep the ONE single spear in her right hand and everything else EXACTLY as the reference — never a second spear. "
        "Change ONLY her LEFT (off) hand and stance: bring the left hand to clutch her chest, sinking into a timid nervous crouch.")
# (name,lvl,frame,source,mode,pose)   mode: 'change' allows weapon edit, 'lock' keeps everything but off-hand/face
FIXES=[
 ("teyaum",8,1,"teyaum-got-L08.png","change",TEY_F1),
 ("teyaum",8,2,"teyaum-got-L08-f1.png","lock",TEY_F2),
 ("teyaum",8,3,"teyaum-got-L08-f1.png","lock",TEY_F3),
 ("gizem",4,1,"gizem-got-L04.png","change",GIZ_F1),
 ("gizem",4,2,"gizem-got-L04-f1.png","lock",GIZ_F2),
 ("gizem",4,3,"gizem-got-L04-f1.png","lock",GIZ_F3),
]
def guard(name,i,mode):
    m=(" Her tunic/armor stays fully INTACT and covers her chest — never rip or show breasts/nipples/cleavage." if GENDER.get(name)=="F" else "")
    base=("This EXACT pixel-art character. Keep the FACE, identity, hair, skin tone, outfit COLORS, body shape/size, HEIGHT, position, camera "
          "distance/scale and the ENTIRE background IDENTICAL to the reference"+m+". This is frame "+str(i)+" of a 3-frame loop of the SAME scene. ")
    return base + ("Make these changes: " if mode=="change" else "Change ONLY this: ")
def call(img,prompt):
    p={"prompt":prompt,"image_base64":base64.b64encode(img).decode(),"mime":"image/png"}
    req=urllib.request.Request(URL,data=json.dumps(p).encode(),headers={"Authorization":"Bearer "+ANON,"apikey":ANON,"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=180); d=json.loads(r.read())
    except Exception as e: return None,repr(e)[:70]
    if not d.get("ok"): return None,"apierr"
    return base64.b64decode(d["image_base64"]),None
for name,lvl,fr,srcname,mode,pose in FIXES:
    sp=os.path.join(SRC,srcname)
    if not os.path.exists(sp): print("NO SRC",srcname,flush=True); continue
    src=open(sp,"rb").read(); op=os.path.join(SRC,f"{name}-got-L{lvl:02d}-f{fr}.png"); ok=False
    for _ in range(RETRIES):
        img,err=call(src,guard(name,fr,mode)+pose+" Keep everything else pixel-identical.")
        if img: open(op,"wb").write(img); print("OK",name,lvl,fr,flush=True); ok=True; break
        time.sleep(3)
    if not ok: print("MISS",name,lvl,fr,err,flush=True)
# rebuild the two gifs (natural aspect) + proof sheets
for name,t in (("teyaum",8),("gizem",4)):
    fp=[os.path.join(SRC,f"{name}-got-L{t:02d}-f{i}.png") for i in (1,2,3)]
    ims=[Image.open(x).convert("RGB") for x in fp]; w=OUT_W; h=int(ims[0].height*w/ims[0].width); h-=h%2
    q=[im.resize((w,h),Image.LANCZOS).convert("P",palette=Image.ADAPTIVE,colors=256) for im in ims]
    q[0].save(os.path.join(SRC,f"{name}-got-L{t:02d}.gif"),save_all=True,append_images=q[1:],duration=MS,loop=0,disposal=2,optimize=True)
    W=230; cs=[im.resize((W,int(im.height*W/im.width))) for im in ims]; hh=max(c.height for c in cs)
    sheet=Image.new("RGB",(3*W,hh),(18,15,26))
    for j,c in enumerate(cs): sheet.paste(c,(j*W,hh-c.height))
    sheet.save(os.path.join(SRC,f"FIX5-{name}-L{t:02d}.png"))
print("DONE",flush=True)
