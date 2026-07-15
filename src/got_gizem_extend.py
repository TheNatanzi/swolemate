#!/usr/bin/env python3
# v2 (PROVEN): outpaint Gizem's GoT frames square->tall via magenta-band padded canvas (JPEG payload).
# Originals live in generated/gizem-got-orig/ (source of truth). Accept only tall (h/w>=1.25) results.
import os, json, base64, io, time, urllib.request
from PIL import Image
URL="https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"
SRC="generated"; BK=os.path.join(SRC,"gizem-got-orig"); RETRIES=4
PROMPT=("The central band of this image is a finished pixel-art scene. The flat MAGENTA bands at the TOP and BOTTOM are "
 "unfinished placeholders. Paint ONLY over the magenta bands: fill the top band with a natural upward continuation of the scene "
 "(more sky / upper background) and the bottom band with a natural downward continuation (more ground / floor), in the exact same "
 "pixel-art style, colors and lighting. Keep every pixel of the existing central scene and the character completely IDENTICAL - "
 "do not redraw, move, zoom or resize anything. No magenta may remain. Output the same tall portrait size.")
def call(jpeg_bytes):
    p={"prompt":PROMPT,"image_base64":base64.b64encode(jpeg_bytes).decode(),"mime":"image/jpeg"}
    req=urllib.request.Request(URL,data=json.dumps(p).encode(),headers={"Authorization":"Bearer "+ANON,"apikey":ANON,"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=180); d=json.loads(r.read())
    except Exception as e: return None,repr(e)[:60]
    if not d.get("ok"): return None,"apierr"
    return base64.b64decode(d["image_base64"]),None
done=0; fails=[]
for t in range(1,11):
    for i in (1,2,3):
        fn=f"gizem-got-L{t:02d}-f{i}.png"; sp=os.path.join(SRC,fn); bp=os.path.join(BK,fn)
        # skip if already tall (e.g. re-runs)
        if Image.open(sp).size[1]/Image.open(sp).size[0]>=1.25:
            print("skip (already tall)",fn,flush=True); done+=1; continue
        im=Image.open(bp).convert("RGB")
        canvas=Image.new("RGB",(1024,1434),(255,0,255)); canvas.paste(im,(0,205))
        buf=io.BytesIO(); canvas.save(buf,format="JPEG",quality=92); payload=buf.getvalue()
        ok=False
        for a in range(RETRIES):
            img,err=call(payload)
            if img:
                out=Image.open(io.BytesIO(img))
                if out.height/out.width>=1.25:
                    open(sp,"wb").write(img); print("OK",fn,out.size,flush=True); ok=True; break
                print("too-square",fn,out.size,flush=True)
            else:
                print("retry",fn,err,flush=True); time.sleep(5)
        if ok: done+=1
        else: fails.append(fn)
print(f"DONE {done}/30 tall; fails: {fails or 'none'}",flush=True)
