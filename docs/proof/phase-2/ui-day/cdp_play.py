"""Lái client web thật (Chrome headless qua CDP) qua một vòng `--mode day` 2 Ngày, chụp ảnh và kiểm lỗi.

Thời lượng pha rút ngắn TRONG BỘ NHỚ (không sửa game.contract.json) để đi hết vòng nhanh.
Dùng: python cdp_play.py <repo> <out_dir> <chrome.exe>
"""
import base64, copy, json, os, subprocess, sys, tempfile, time, urllib.request

repo, out_dir, chrome = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, repo)
os.chdir(repo)
import websocket  # websocket-client
from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer

t = copy.deepcopy(load_contract()["tuning"])
t["gather"]["duration_s"] = 10
t["quan"]["duration_s"] = 10
srv = LiveServer(LiveGame("day", t, {}, 42, {}, days=2), port=0)
srv.start()
url = f"http://127.0.0.1:{srv.port}/"

prof = tempfile.mkdtemp()
port = 9333
proc = subprocess.Popen([chrome, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
                         "--window-size=1280,720", "--hide-scrollbars", "--no-first-run", "about:blank"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ws_url = None
for _ in range(50):
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1).read())
        ws_url = next(x["webSocketDebuggerUrl"] for x in tabs if x["type"] == "page")
        break
    except Exception:
        time.sleep(0.2)
ws = websocket.create_connection(ws_url, timeout=10)
mid = 0
errors = []


def cdp(method, **params):
    global mid
    mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv())
        if m.get("method") == "Runtime.exceptionThrown":
            errors.append(m["params"]["exceptionDetails"].get("exception", {}).get("description", str(m["params"])))
        elif m.get("method") == "Runtime.consoleAPICalled" and m["params"]["type"] == "error":
            errors.append(" ".join(str(a.get("value", a.get("description"))) for a in m["params"]["args"]))
        if m.get("id") == mid:
            return m.get("result", {})


def js(expr):
    r = cdp("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
    return r.get("result", {}).get("value")


VK = {"Enter": 13, "Escape": 27, "1": 49, "2": 50, "e": 69}


def key(k):
    for typ in ("keyDown", "keyUp"):
        cdp("Input.dispatchKeyEvent", type=typ, key=k, code=("Digit" + k) if k.isdigit() else ("Key" + k.upper() if len(k) == 1 else k),
            windowsVirtualKeyCode=VK.get(k, 0))
    time.sleep(0.15)


def shot(name):
    data = cdp("Page.captureScreenshot", format="png")["data"]
    with open(os.path.join(out_dir, name), "wb") as f:
        f.write(base64.b64decode(data))


def state():
    return js("(() => { const s = CN.state.snap || {}; return {mode: CN.screens.mode, card: CN.screens.card && CN.screens.card.kind,"
              " phase: s.phase, state: s.state, day: s.day, tick: s.tick, finished: s.finished, money: s.money,"
              " shift: s.shift_earned, dc: s.days_completed, md: s.max_days, tl: s.time_left_ticks}; })()")


def wait(pred, timeout=40, label=""):
    end = time.time() + timeout
    while time.time() < end:
        s = state()
        if s and pred(s):
            return s
        time.sleep(0.1)
    raise SystemExit(f"TIMEOUT {label}: {state()}")


log = []
def step(msg, s):
    line = f"{msg}: {json.dumps(s, ensure_ascii=False)}"
    log.append(line); print(line, flush=True)


try:
    cdp("Runtime.enable"); cdp("Page.enable")
    cdp("Emulation.setDeviceMetricsOverride", width=1280, height=720, deviceScaleFactor=1, mobile=False)
    cdp("Page.navigate", url=url)
    s = wait(lambda s: s["mode"] == "menu" and s["tick"], label="menu"); time.sleep(0.5)
    step("1 menu", s); shot("ui-day-01-menu.png")

    key("Enter")
    s = wait(lambda s: s["card"] == "day" and s["state"] == "paused", label="dayintro"); time.sleep(0.3)
    step("2 DayIntro (sim paused)", s); shot("ui-day-02-dayintro.png")
    tl0 = s["tl"]; time.sleep(1.0); s = state()
    step("2b timer frozen during intro", s); assert s["tl"] == tl0, "timer chạy trong intro"

    s = wait(lambda s: s["card"] is None and s["state"] == "running", timeout=6, label="intro auto-close 4s")
    step("3 intro auto-closed after 4s", s)
    time.sleep(1.0); shot("ui-day-03-gather-hud.png")

    key("Escape")
    s = wait(lambda s: s["state"] == "paused", label="pause"); time.sleep(0.3)
    step("4 pause menu", s); shot("ui-day-04-pause.png")
    key("Escape")
    s = wait(lambda s: s["state"] == "running", label="resume"); step("4b resumed", s)

    fps = js("new Promise(r => { let n = 0; const t0 = performance.now(); (function f() { n++; if (performance.now() - t0 < 3000) requestAnimationFrame(f); else r(n * 1000 / (performance.now() - t0)); })(); })")
    step("5 FPS gather (3 s, 1280x720)", round(fps, 1))

    s = wait(lambda s: s["card"] == "evening" and s["state"] == "paused", label="evening paused"); time.sleep(0.3)
    step("6 EveningIntro", s); shot("ui-day-05-evening.png")
    key("e")
    s = wait(lambda s: s["card"] is None and s["phase"] == "quan" and s["state"] == "running", label="quan")
    time.sleep(3.0); s = state(); step("7 quan HUD", s); shot("ui-day-06-quan-hud.png")
    fps_q = js("new Promise(r => { let n = 0; const t0 = performance.now(); (function f() { n++; if (performance.now() - t0 < 3000) requestAnimationFrame(f); else r(n * 1000 / (performance.now() - t0)); })(); })")
    step("7b FPS quan", round(fps_q, 1))

    s = wait(lambda s: s["card"] == "result" and s["state"] == "paused", label="result paused"); time.sleep(0.3)
    step("8 DayResult", s); shot("ui-day-07-result.png")
    key("e")
    s = wait(lambda s: s["card"] is None and s["phase"] == "shop", label="shop")
    key("1"); time.sleep(0.4)
    step("9 Shop (bấm 1)", state()); shot("ui-day-08-shop.png")
    key("Enter")
    s = wait(lambda s: s["day"] == 2 and s["card"] == "day", label="day2 intro"); step("10 Ngày 2 intro", s)
    key("e")
    s = wait(lambda s: s["card"] == "evening", label="evening2"); key("e")
    s = wait(lambda s: s["card"] == "result", label="result2"); key("e")
    s = wait(lambda s: s["phase"] == "shop" and s["card"] is None, label="shop2"); key("Enter")
    s = wait(lambda s: s["finished"], label="summary"); time.sleep(0.5)
    step("11 Summary", s); shot("ui-day-09-summary.png")
finally:
    print("CONSOLE ERRORS:", errors if errors else "none")
    with open(os.path.join(out_dir, "ui-day-run.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\nCONSOLE ERRORS: " + (json.dumps(errors, ensure_ascii=False) if errors else "none") + "\n")
    try: ws.close()
    except Exception: pass
    proc.terminate(); srv.stop()
