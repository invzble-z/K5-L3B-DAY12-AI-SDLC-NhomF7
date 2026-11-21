"""Chụp HUD độ tươi (AC-P3-09) bằng Chrome headless qua DevTools Protocol, bắt lỗi console.

Dùng: python -X utf8 docs/proof/phase-3/hud-fresh/cdp_shots.py <repo> <out_dir> <chrome.exe>   (cần websocket-client)
- Mock v1.2 + mock v1.1 (kiểm HUD cũ không vỡ).
- Live gather với tuning v1.2 trong bộ nhớ (game.contract.json không đổi): giỏ có hàng gần ngưỡng 30,
  sim giỏ cá thể thật (`sim/gather.py`) hao tươi và phát `spoiled`.
"""
import base64, copy, json, os, subprocess, sys, tempfile, time, urllib.request

repo, out_dir, chrome = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, repo)
os.chdir(repo)
import websocket
from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer

t = copy.deepcopy(load_contract()["tuning"])
t["contract_version"] = "1.2"
t["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
hold = [("ca_loc", 100), ("bong_sung", 92), ("ca_linh", 66), ("ca_linh", 45), ("keo_neo", 30.4), ("ca_keo", 30.2), ("bong_sung", 14)]
scenario = {"random_fish": False, "hold": [{"id": f"I{i+1}", "kind": k, "fresh": f} for i, (k, f) in enumerate(hold)]}
srv = LiveServer(LiveGame("gather", t, scenario, 42), port=0)
srv.start()
base = f"http://127.0.0.1:{srv.port}/"

prof = tempfile.mkdtemp()
port = 9334
proc = subprocess.Popen([chrome, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
                         "--window-size=1280,720", "--hide-scrollbars", "--no-first-run", "about:blank"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(50):
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1).read())
        ws_url = next(x["webSocketDebuggerUrl"] for x in tabs if x["type"] == "page")
        break
    except Exception:
        time.sleep(0.2)
ws = websocket.create_connection(ws_url, timeout=10)
mid, errors, log = 0, [], []


def cdp(method, **params):
    global mid
    mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv())
        if m.get("method") == "Runtime.exceptionThrown":
            errors.append(m["params"]["exceptionDetails"].get("exception", {}).get("description", "exception"))
        elif m.get("method") == "Runtime.consoleAPICalled" and m["params"]["type"] == "error":
            errors.append(" ".join(str(a.get("value", a.get("description"))) for a in m["params"]["args"]))
        if m.get("id") == mid:
            return m.get("result", {})


def js(expr):
    return cdp("Runtime.evaluate", expression=expr, returnByValue=True).get("result", {}).get("value")


def shot(name):
    with open(os.path.join(out_dir, name), "wb") as f:
        f.write(base64.b64decode(cdp("Page.captureScreenshot", format="png")["data"]))


def key(k, vk):
    for typ in ("keyDown", "keyUp"):
        cdp("Input.dispatchKeyEvent", type=typ, key=k, code=k, windowsVirtualKeyCode=vk)


try:
    cdp("Runtime.enable"); cdp("Page.enable")
    cdp("Emulation.setDeviceMetricsOverride", width=1280, height=720, deviceScaleFactor=1, mobile=False)
    for mock, name in (("day-gather-v12", "hud-fresh-gather-mock.png"), ("day-quan-v12", "hud-fresh-quan-mock.png"),
                       ("day-gather", "hud-v11-gather-mock.png"), ("day-quan", "hud-v11-quan-mock.png")):
        cdp("Page.navigate", url=base + "?mock=" + mock)
        time.sleep(1.2)
        key("e", 69)          # đóng thẻ intro của mock để thấy HUD
        time.sleep(0.6)
        shot(name)
        log.append(f"mock {mock}: hold={js('JSON.stringify((CN.state.snap||{}).hold||null).slice(0,80)')}")
    cdp("Page.navigate", url=base)
    time.sleep(1.0)
    key("Enter", 13)          # Menu → Chơi (restart lượt, intro hiện + pause)
    time.sleep(0.8)
    key("e", 69)              # đóng intro, chạy tiếp
    time.sleep(4.0)           # 4 s × 0.5/s = 2 điểm: I5 (30.4) và I6 (30.2) qua ngưỡng 30
    snap = js("JSON.stringify({hold: CN.state.snap.hold, ev: CN.state.snap.events.filter(e => e.name === 'spoiled').map(e => e.data)})")
    log.append("live v1.2 sau ~4 s: " + snap)
    shot("hud-fresh-gather-live.png")
finally:
    log.append("CONSOLE ERRORS: " + (json.dumps(errors, ensure_ascii=False) if errors else "none"))
    with open(os.path.join(out_dir, "run.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print("\n".join(log))
    ws.close(); proc.terminate(); srv.stop()
