#!/usr/bin/env python3
"""swole_sender.py — PC-driven WhatsApp group delivery for SwoleMate (replaces Tasker/AutoInput).
Fetches composed messages from the coach edge function, then drives the USB-connected Pixel 7a via ADB:
text via SEND text/plain share intent (emoji-safe), avatar GIFs via SEND image/gif with MediaStore URIs.
Modes: daily | mealam | mealpm | monday | test
Scheduled by Windows Task Scheduler (PC is always-on, phone always docked via USB).
"""
import subprocess, sys, json, re, time, urllib.request, datetime, io, os

ADB = r"C:\Users\Mahdi\adb\platform-tools\adb.exe"
COACH = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/coach"
GROUP_RE = r'text="SwoleMate[^"]*"'
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "swole_sender.log")
NAME2KEY = {"medi": "medi", "mahdi": "medi", "teyaum": "teyaum", "gizem": "gizem", "rinad": "rinad"}

def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} | {msg}"
    print(line.encode("ascii", "replace").decode())
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def adb(*args, timeout=30):
    r = subprocess.run([ADB, *args], capture_output=True, timeout=timeout)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")

def shell(cmd, timeout=30):
    return adb("shell", cmd, timeout=timeout)

def device_ok():
    _, out, _ = adb("devices")
    return bool(re.search(r"^\S+\s+device\s*$", out, re.M))

def ui_dump():
    shell("uiautomator dump /sdcard/ui.xml >/dev/null 2>&1")
    _, out, _ = shell("cat /sdcard/ui.xml", timeout=30)
    return out

def find_bounds(xml, pattern):
    m = re.search(pattern + r'[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml)
    if not m:
        m2 = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*' + pattern, xml)
        if not m2: return None
        m = m2
    return ((int(m.group(1)) + int(m.group(3))) // 2, (int(m.group(2)) + int(m.group(4))) // 2)

def tap(xy): shell(f"input tap {xy[0]} {xy[1]}")
def home():
    shell("input keyevent KEYCODE_BACK"); time.sleep(0.6)
    shell("input keyevent KEYCODE_HOME"); time.sleep(0.8)
def wake():
    shell("input keyevent KEYCODE_WAKEUP"); time.sleep(0.8)
    shell("svc power stayon usb")  # keep screen on while on USB

def wait_find(pattern, tries=6, delay=1.2):
    for _ in range(tries):
        xy = find_bounds(ui_dump(), pattern)
        if xy: return xy
        time.sleep(delay)
    return None

def deliver_text(text):
    # write UTF-8 message to phone, share it (emoji-safe), pick group, send
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_msg.txt")
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(text)
    adb("push", tmp, "/sdcard/swole_msg.txt")
    shell('am start -a android.intent.action.SEND -t text/plain --es android.intent.extra.TEXT "$(cat /sdcard/swole_msg.txt)" -p com.whatsapp')
    time.sleep(2.5)
    g = wait_find(GROUP_RE)
    if not g: log("FAIL text: group row not found"); home(); return False
    tap(g); time.sleep(2)
    s = wait_find(r'(?:content-desc="Send"|resource-id="com.whatsapp:id/send")')
    if not s: log("FAIL text: send button not found"); home(); return False
    tap(s); time.sleep(2.5)
    home()
    log(f"sent text ({len(text)} chars): {text.splitlines()[0][:60]}")
    return True

GIF_DIR = r"G:\Shared drives\Adibs Online\Anthropic\Fitness App\Avatars\generated"

def build_composite(people, gifset, outname):
    """people = [(display, key, lvl)]; hstack their 3-frame gifs + name/level label bar -> one gif."""
    from PIL import Image, ImageDraw, ImageFont, ImageSequence
    cols = []
    for disp, key, lvl in people:
        im = Image.open(os.path.join(GIF_DIR, f"{key}-{gifset}-L{lvl:02d}.gif"))
        frames = [f.convert("RGB").copy() for f in ImageSequence.Iterator(im)][:3]
        while len(frames) < 3: frames.append(frames[-1])
        cols.append((disp, lvl, frames))
    W, H, LBL = 440, 616, 74
    try: font = ImageFont.truetype("arialbd.ttf", 40)
    except Exception: font = ImageFont.load_default()
    out_frames = []
    for i in range(3):
        canvas = Image.new("RGB", (W * len(cols), H + LBL), (13, 11, 18))
        for j, (disp, lvl, frames) in enumerate(cols):
            canvas.paste(frames[i].resize((W, H)), (j * W, 0))
            d = ImageDraw.Draw(canvas)
            label = f"{disp} · L{lvl}"
            tw = d.textlength(label, font=font)
            d.text((j * W + (W - tw) // 2, H + 14), label, fill=(245, 185, 51), font=font)
        out_frames.append(canvas.convert("P", palette=Image.ADAPTIVE, colors=256))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), outname)
    out_frames[0].save(out, save_all=True, append_images=out_frames[1:], duration=160, loop=0, disposal=2, optimize=True)
    return out

def parse_ladder_people(text):
    out = []
    for m in re.finditer(r"[\U0001F53A\U0001F53B▪] ?️? ?\*(\w+)\* — \*L(\d+)", text):
        key = NAME2KEY.get(m.group(1).lower())
        if key: out.append((m.group(1), key, int(m.group(2))))
    return out

def deliver_gif_file(local_path, caption=None):
    """Push a fresh gif to the phone, register it, share w/ optional caption via EXTRA_TEXT (emoji-safe)."""
    name = os.path.basename(local_path)
    adb("push", local_path, f"/sdcard/Download/SwoleMate/{name}")
    shell(f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Download/SwoleMate/{name}")
    time.sleep(1.5)
    mid = media_id(name)
    if not mid: log(f"FAIL composite: {name} not scanned"); return False
    extra = ""
    if caption is not None:
        tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_msg.txt")
        io.open(tmp, "w", encoding="utf-8", newline="\n").write(caption)
        adb("push", tmp, "/sdcard/swole_msg.txt")
        extra = ' --es android.intent.extra.TEXT "$(cat /sdcard/swole_msg.txt)"'
    shell(f"am start -a android.intent.action.SEND -t image/gif --eu android.intent.extra.STREAM content://media/external/images/media/{mid} --grant-read-uri-permission{extra} -p com.whatsapp")
    time.sleep(3)
    g = wait_find(GROUP_RE)
    if not g: log(f"FAIL composite {name}: group not found"); home(); return False
    tap(g); time.sleep(2)
    s = wait_find(r'content-desc="Send"')
    if not s: log(f"FAIL composite {name}: send not found"); home(); return False
    tap(s); time.sleep(3.5)
    home()
    log(f"sent composite gif: {name} (caption: {bool(caption)})")
    return True

def media_id(display_name):
    _, out, _ = shell(f"content query --uri content://media/external/images/media --projection _id:_display_name --where \"_display_name='{display_name}'\"")
    m = re.search(r"_id=(\d+)", out)
    return m.group(1) if m else None

def deliver_gif(filename):
    mid = media_id(filename)
    if not mid: log(f"FAIL gif: {filename} not in MediaStore"); return False
    shell(f"am start -a android.intent.action.SEND -t image/gif --eu android.intent.extra.STREAM content://media/external/images/media/{mid} --grant-read-uri-permission -p com.whatsapp")
    time.sleep(3)
    g = wait_find(GROUP_RE)
    if not g: log(f"FAIL gif {filename}: group row not found"); home(); return False
    tap(g); time.sleep(2)
    s = wait_find(r'content-desc="Send"')
    if not s: log(f"FAIL gif {filename}: send not found"); home(); return False
    tap(s); time.sleep(3.5)
    home()
    log(f"sent gif: {filename}")
    return True

AUTOREMOTE_KEY = "fhRa6IJhcsA:APA91bGsi45wFYoTfVs4jkoD8_hv0KPGNywWR6z_i33AgqPdw3R23UHTJuTvkXX8GTgbOjdYUqyDsszuvA8rgit_N1xc5p2ynaTYjDaJz4VArsveyodTQgM"

def fallback_text(text):
    """Backup route: AutoRemote -> Tasker on the phone posts the text (works even if ADB/USB is down)."""
    import urllib.parse
    try:
        url = "https://autoremotejoaomgcd.appspot.com/sendmessage?key=" + AUTOREMOTE_KEY + "&message=" + urllib.parse.quote("swole=:=" + text)
        with urllib.request.urlopen(url, timeout=30) as r:
            ok = r.status == 200
        log(f"BACKUP route (Tasker) {'ok' if ok else 'FAILED'}: {text.splitlines()[0][:50]}")
        time.sleep(18)  # Tasker needs time to type+send before the next message
        return ok
    except Exception as e:
        log(f"BACKUP route error: {e!r}")
        return False

def send_text_resilient(text):
    if device_ok() and deliver_text(text):
        return True
    return fallback_text(text)

def fetch(params):
    with urllib.request.urlopen(f"{COACH}?{params}", timeout=120) as r:
        return json.loads(r.read())

def movers_from_ladder(text, gifset):
    out = []
    for m in re.finditer(r"[\U0001F53A\U0001F53B] \*(\w+)\* — \*L(\d+)", text):
        key = NAME2KEY.get(m.group(1).lower())
        if key: out.append(f"{key}-{gifset}-L{int(m.group(2)):02d}.gif")
    return out

def champion_from(text):
    m = re.search(r"YOUR CHAMPION: (\w+)", text) or re.search(r"\U0001F451 Bragging Rights.*", text)
    if m and m.re.pattern.startswith("YOUR"):
        return NAME2KEY.get(m.group(1).lower())
    m2 = re.search(r"\U0001F947 \*(\w+)\*", text)
    return NAME2KEY.get(m2.group(1).lower()) if m2 else None

def run(mode):
    usb = device_ok()
    if usb:
        wake(); home()
    else:
        log(f"{mode}: no adb device — using BACKUP route (Tasker) for texts, images skipped")
    if mode == "test":
        send_text_resilient("⚙️ pc-sender self-test ✅"); return
    params = {"daily": "daily=1", "mealam": "meal=am", "mealpm": "meal=pm", "monday": "monday=1"}[mode]
    d = fetch(params)
    if d.get("skipped"): log(f"{mode}: skipped ({d['skipped']})"); return
    msgs = d.get("messages", [])
    log(f"{mode}: {len(msgs)} messages from coach")
    stamp = datetime.date.today().strftime("%Y%m%d")
    texts = 0; images = 0
    for msg in msgs:
        # LADDER / THRONE become ONE image message: composite gif of everyone + the text as caption
        gifset = "pixel" if "THE LADDER" in msg else ("got" if "THRONE ROOM" in msg else None)
        if usb and gifset:
            people = parse_ladder_people(msg)
            if people:
                comp = build_composite(people, gifset, f"_ladder_{gifset}_{stamp}.gif")
                if deliver_gif_file(comp, caption=msg): images += 1
                else: send_text_resilient(msg); texts += 1
                time.sleep(2); continue
        if usb and "YOUR CHAMPION" in msg:
            c = champion_from(msg)
            if c and deliver_gif_file(os.path.join(GIF_DIR, f"{c}-podium.gif"), caption=msg):
                images += 1; time.sleep(2); continue
        if usb and mode == "monday" and "LAST WEEK'S RESULTS" in msg:
            c = champion_from(msg)
            if c and deliver_gif_file(os.path.join(GIF_DIR, f"{c}-podium.gif"), caption=msg):
                images += 1; time.sleep(2); continue
        send_text_resilient(msg); texts += 1
        time.sleep(2)
    log(f"{mode}: done ({texts} texts, {images} image-messages)")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    try:
        run(mode)
    except Exception as e:
        log(f"ERROR {mode}: {e!r}")
