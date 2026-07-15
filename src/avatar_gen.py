#!/usr/bin/env python3
# avatar_gen.py — turn a source photo into a cartoon avatar via the gen-avatar edge fn.
# Usage: python avatar_gen.py <input_image> <output_image> <prompt_file> [--modalities]
# Prints ONLY status (never the base64), writes the generated image to <output_image>.
import sys, os, json, base64, urllib.request, urllib.error

URL = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/gen-avatar"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXZhZ2d6bnl2Z3F4a25sbnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NDk5NTcsImV4cCI6MjA5OTAyNTk1N30.qP7MWhAc-zV2W8-_1ZGkBmLj8E6Wc1K2QlYGad2-g1s"

inp, outp, prompt_file = sys.argv[1], sys.argv[2], sys.argv[3]
modalities = "--modalities" in sys.argv[4:]
prompt = open(prompt_file, encoding="utf-8").read().strip()
raw = open(inp, "rb").read()
ext = os.path.splitext(inp)[1].lower()
mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
payload = {"prompt": prompt, "image_base64": base64.b64encode(raw).decode(), "mime": mime}
if modalities:
    payload["modalities"] = True

req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
    headers={"Authorization": "Bearer " + ANON, "apikey": ANON, "Content-Type": "application/json"})
try:
    r = urllib.request.urlopen(req, timeout=180)
    d = json.loads(r.read())
except urllib.error.HTTPError as e:
    print("HTTP_ERROR", e.code, e.read()[:600].decode(errors="replace")); sys.exit(1)
except Exception as e:
    print("ERROR", repr(e)); sys.exit(1)

if not d.get("ok"):
    trimmed = {k: v for k, v in d.items() if k != "raw"}
    print("GEN_FAIL", json.dumps(trimmed)[:800]); sys.exit(2)

out = base64.b64decode(d["image_base64"])
os.makedirs(os.path.dirname(outp), exist_ok=True)
open(outp, "wb").write(out)
print("OK", outp, len(out), "bytes", d.get("mime"))
