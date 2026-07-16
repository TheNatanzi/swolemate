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
    if not device_ok():
        log(f"ABORT {mode}: no adb device"); return
    wake(); home()
    if mode == "test":
        deliver_text("⚙️ pc-sender self-test ✅"); return
    params = {"daily": "daily=1", "mealam": "meal=am", "mealpm": "meal=pm", "monday": "monday=1"}[mode]
    d = fetch(params)
    if d.get("skipped"): log(f"{mode}: skipped ({d['skipped']})"); return
    msgs = d.get("messages", [])
    log(f"{mode}: {len(msgs)} messages from coach")
    gifs = []
    for msg in msgs:
        deliver_text(msg)
        time.sleep(2)
        if "THE LADDER" in msg:      gifs += movers_from_ladder(msg, "pixel")
        if "THRONE ROOM" in msg:     gifs += movers_from_ladder(msg, "got")
        if "YOUR CHAMPION" in msg:
            c = champion_from(msg)
            if c: gifs.insert(0, f"{c}-podium.gif")
    if mode == "monday" and not any(g.endswith("podium.gif") for g in gifs):
        # no finale this week: podium for the weekly gold medalist from results msg
        for msg in msgs:
            if "LAST WEEK'S RESULTS" in msg:
                c = champion_from(msg)
                if c: gifs.insert(0, f"{c}-podium.gif")
    for g in dict.fromkeys(gifs):  # dedupe, keep order
        deliver_gif(g)
        time.sleep(2)
    log(f"{mode}: done ({len(msgs)} texts, {len(set(gifs))} gifs)")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    try:
        run(mode)
    except Exception as e:
        log(f"ERROR {mode}: {e!r}")
