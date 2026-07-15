#!/usr/bin/env python3
# Champion podium GIFs — one per person, reusable every week. 3-frame loop:
# f2 = anchor (trophy thrust overhead, from base avatar), f1/f3 = pose edits OF f2 (scene locked).
# Output: <name>-podium-f{1,2,3}.png + <name>-podium.gif (uniform 440x616, ambient blur fill).
import os, json, base64, io, time, urllib.request
from PIL import Image, ImageFilter, ImageEnhance
URL="https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC="generated"; RETRIES=5; TW,THh,MS=440,616,160
GENDER={"medi":"M","teyaum":"M","gizem":"F","rinad":"F"}
PEOPLE=["medi","teyaum","gizem","rinad"]

def mod(n): return (" Her gold tracksuit stays fully INTACT and covers her chest — never show breasts/nipples/cleavage." if GENDER[n]=="F" else "")
def his(n): return "her" if GENDER[n]=="F" else "his"
def F2(n):
    return ("This EXACT pixel-art character. Keep "+his(n)+" FACE, identity, hair, skin tone, body shape and HEIGHT completely IDENTICAL, "
     "crisp pixel-art style, full-body front-facing. Place "+("her" if GENDER[n]=="F" else "him")+" standing proudly on the TOP step of a GOLD CHAMPION PODIUM marked \"1\", "
     "wearing a gold medal around "+his(n)+" neck and a gold champion tracksuit, THRUSTING a golden trophy high overhead, mouth open in a victorious cheer, "
     "colorful confetti bursting and falling all around, a festive stadium with spotlights behind."+mod(n)+" Keep the face an exact match to the reference person.")
def F1(n):
    return ("This EXACT pixel-art character and scene. Keep the FACE, identity, podium, gold medal, tracksuit, confetti, stadium and scale completely IDENTICAL to the reference. "
     "This is frame 1 of a 3-frame loop. Change ONLY the pose: hold the golden trophy at chest height with both hands, a huge proud grin (mouth closed), chin up."+mod(n)+
     " The figure has exactly two hands. Keep everything else pixel-identical.")
def F3(n):
    return ("This EXACT pixel-art character and scene. Keep the FACE, identity, podium, gold medal, tracksuit, confetti, stadium and scale completely IDENTICAL to the reference. "
     "This is frame 3 of a 3-frame loop. Change ONLY the pose: the golden trophy held high in ONE hand, the OTHER fist pumped up in triumph, laughing joyfully."+mod(n)+
     " The figure has exactly two hands. Keep everything else pixel-identical.")
def call(img,prompt):
    p={"prompt":prompt,"image_base64":base64.b64encode(img).decode(),"mime":"image/png"}
    req=urllib.request.Request(URL,data=json.dumps(p).encode(),headers={"Authorization":"Bearer "+ANON,"apikey":ANON,"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=180); d=json.loads(r.read())
    except Exception as e: return None,repr(e)[:60]
    if not d.get("ok"): return None,"apierr"
    return base64.b64decode(d["image_base64"]),None
def gen(outp, src_bytes, prompt):
    if os.path.exists(outp) and os.path.getsize(outp)>1000: print("skip",os.path.basename(outp),flush=True); return True
    for a in range(RETRIES):
        img,err=call(src_bytes,prompt)
        if img: open(outp,"wb").write(img); print("OK",os.path.basename(outp),flush=True); return True
        print("retry",os.path.basename(outp),err,flush=True); time.sleep(5)
    print("MISS",os.path.basename(outp),flush=True); return False
# seed medi f2 from the approved proof
tp=os.path.join(SRC,"TEST-podium-medi.png"); m2=os.path.join(SRC,"medi-podium-f2.png")
if os.path.exists(tp) and not os.path.exists(m2):
    import shutil; shutil.copy2(tp,m2); print("seeded medi f2 from proof",flush=True)
for n in PEOPLE:
    f2p=os.path.join(SRC,f"{n}-podium-f2.png")
    gen(f2p, open(os.path.join(SRC,f"{n}-pixel-05.png"),"rb").read(), F2(n))
    if not os.path.exists(f2p): continue
    anchor=open(f2p,"rb").read()
    gen(os.path.join(SRC,f"{n}-podium-f1.png"), anchor, F1(n))
    gen(os.path.join(SRC,f"{n}-podium-f3.png"), anchor, F3(n))
# ---- build uniform 440x616 gifs (ambient blur fill; scenic bg) ----
def uniform(im):
    im=im.convert("RGB")
    s=max(TW/im.width,THh/im.height)
    big=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS)
    x=(big.width-TW)//2; y=(big.height-THh)//2
    under=big.crop((x,y,x+TW,y+THh)).filter(ImageFilter.GaussianBlur(16))
    under=ImageEnhance.Brightness(under).enhance(0.62)
    f=min(TW/im.width,THh/im.height)
    fg=im.resize((round(im.width*f),round(im.height*f)),Image.LANCZOS)
    under.paste(fg,((TW-fg.width)//2,(THh-fg.height)//2))
    return under
built=[]
for n in PEOPLE:
    fp=[os.path.join(SRC,f"{n}-podium-f{i}.png") for i in (1,2,3)]
    if not all(os.path.exists(x) for x in fp): print("gif skip",n,flush=True); continue
    frames=[uniform(Image.open(x)) for x in fp]
    q=[fr.convert("P",palette=Image.ADAPTIVE,colors=256) for fr in frames]
    out=os.path.join(SRC,f"{n}-podium.gif")
    q[0].save(out,save_all=True,append_images=q[1:],duration=MS,loop=0,disposal=2,optimize=True)
    built.append(n)
print("PODIUM GIFS:",built,flush=True)
# proof sheet: all 4, f2
row=Image.new("RGB",(4*220,400),(10,8,14))
for j,n in enumerate(PEOPLE):
    p=os.path.join(SRC,f"{n}-podium-f2.png")
    if os.path.exists(p):
        im=Image.open(p).convert("RGB"); im=im.resize((220,int(im.height*220/im.width)))
        row.paste(im.crop((0,0,220,400)) if im.height>=400 else im,(j*220,0))
row.save(os.path.join(SRC,"PODIUM-proof.png")); print("DONE",flush=True)
