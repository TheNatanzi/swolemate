#!/usr/bin/env python3
# animate_ai.py — AI-keyframe animation: generate ONE alternate frame of an avatar
# and ping-pong loop it with the original. Outputs GIF (preview) + MP4 (WhatsApp).
# Usage: python animate_ai.py <base.png> <out.gif> <out.mp4> <variant_prompt>
import sys, io, json, base64, urllib.request, urllib.error
from PIL import Image
import imageio.v2 as imageio

URL = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"

base_path, out_gif, out_mp4, prompt = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
base_bytes = open(base_path, "rb").read()

payload = {"prompt": prompt, "image_base64": base64.b64encode(base_bytes).decode(), "mime": "image/png"}
req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
    headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
r = urllib.request.urlopen(req, timeout=180)
d = json.loads(r.read())
if not d.get("ok"):
    print("VARIANT FAIL", json.dumps({k: v for k, v in d.items() if k != "raw"})[:300]); sys.exit(1)
var_bytes = base64.b64decode(d["image_base64"])

base_im = Image.open(base_path).convert("RGB")
var_im = Image.open(io.BytesIO(var_bytes)).convert("RGB").resize(base_im.size, Image.NEAREST)

W = 420
h = int(base_im.height * W / base_im.width); h -= h % 2
base_im = base_im.resize((W, h), Image.NEAREST)
var_im = var_im.resize((W, h), Image.NEAREST)

frames = [base_im] * 4 + [var_im] * 4          # 2-frame ping-pong loop, held
frames[0].save(out_gif, save_all=True, append_images=frames[1:], duration=110, loop=0, disposal=2, optimize=True)
imageio.mimsave(out_mp4, frames, fps=9, codec="libx264", macro_block_size=1, quality=8)
print("OK", out_mp4, f"{W}x{h}")
