"""Kiểm phía client Phase 4 bằng Chrome headless (DevTools Protocol, cần websocket-client).

Dùng: python -X utf8 docs/proof/phase-4/ui-client/cdp_p4.py <repo> <out_dir> <chrome.exe> [duration_s]
1. Bench: live gather seed 42, mở /?bench=1&warmup=3&duration=30, chờ POST /bench, ghi bench-client.json
   (thời gian khung thô + avg_fps, p1_low_fps tính theo công thức ở docs/plan/phase-4.md §0 để đối chiếu;
   5 trường chính thức do chonoi/bench.py của ttkien0710 tính).
2. Ảnh 3 cảnh báo ở chế độ thường và tương phản cao (mock day-gather: Cá Sấu đuổi + oxy < 25%;
   mock day-quan: khách kiên nhẫn < 25%), menu tạm dừng có dòng tương phản.
3. Phím H bật tương phản, tải lại trang không có ?contrast vẫn giữ (localStorage).
"""
import base64, json, math, os, subprocess, sys, tempfile, time, urllib.request

repo, out_dir, chrome = sys.argv[1], sys.argv[2], sys.argv[3]
duration = float(sys.argv[4]) if len(sys.argv) > 4 else 30
sys.path.insert(0, repo)
os.chdir(repo)
import websocket
from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer

game = LiveGame("gather", load_contract()["tuning"], {}, 42)
srv = LiveServer(game, port=0)
srv.start()
base = f"http://127.0.0.1:{srv.port}/"
prof = tempfile.mkdtemp()
port = 9335
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
ws = websocket.create_connection(ws_url, timeout=60)
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
    time.sleep(0.2)


def go(url, wait=1.2):
    cdp("Page.navigate", url=url)
    time.sleep(wait)


try:
    cdp("Runtime.enable"); cdp("Page.enable")
    cdp("Emulation.setDeviceMetricsOverride", width=1280, height=720, deviceScaleFactor=1, mobile=False)

    # 1. bench
    t_nav = time.time() * 1000
    go(base + f"?bench=1&warmup=3&duration={duration:g}", 0.5)
    time.sleep(1.5)
    log.append("bench screens.mode=" + str(js("CN.screens.mode")) + " card=" + str(js("CN.screens.card")) + " phase=" + str(js("CN.bench.phase")))
    shot("bench-running.png")
    ok = game.bench_event.wait(duration + 30)
    r = game.bench_result if ok else None
    if r:
        fr = r["frame_ms"]
        n = len(fr)
        k = max(1, math.ceil(0.01 * n))
        slow = sorted(fr, reverse=True)[:k]
        summary = {
            "seed": 42, "warmup_s": r["warmup_s"], "measured_s": round(r["measured_s"], 3), "frames": n,
            "avg_fps": round(n / r["measured_s"], 2),
            "p1_low_fps": round(1000 / (sum(slow) / k), 2),
            "first_frame_after_nav_ms": round(r["first_frame_epoch_ms"] - t_nav, 1),
            "width": r["width"], "height": r["height"], "dpr": r["dpr"],
            "note": "đối chiếu công thức; bench.json chính thức do chonoi/bench.py tính",
        }
        with open(os.path.join(out_dir, "bench-client.json"), "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "frame_ms": fr}, f, ensure_ascii=False)
        log.append("bench: " + json.dumps(summary, ensure_ascii=False))
        time.sleep(0.3)
        shot("bench-done.png")
    else:
        log.append("bench: KHÔNG nhận được POST /bench")

    # 2. cảnh báo, thường và tương phản cao
    for c in ("0", "1"):
        tag = "hc" if c == "1" else "thuong"
        go(base + f"?mock=day-gather&contrast={c}")
        key("e", 69)                      # đóng thẻ intro của mock
        time.sleep(0.4)
        shot(f"alerts-gather-{tag}.png")
        go(base + f"?mock=day-quan&contrast={c}")
        key("e", 69)
        time.sleep(0.4)
        shot(f"alerts-quan-{tag}.png")
        log.append(f"contrast={c}: CN.contrast.on={js('CN.contrast.on')}")
    key("p", 80)                          # mock: P bật tạm dừng tại chỗ
    time.sleep(0.4)
    shot("pause-menu-hc.png")

    # 2b. cảnh báo với sim thật (sim/monsters.py): người chơi cạnh M1 ở d=22, oxy 300/1800 (< 25%)
    srv2 = LiveServer(LiveGame("gather", load_contract()["tuning"],
                               {"random_fish": False, "player": {"pos": [56, 22], "oxygen_ticks": 300}}, 42), port=0)
    srv2.start()
    try:
        b2 = f"http://127.0.0.1:{srv2.port}/"
        for c in ("1", "0"):
            go(b2 + f"?contrast={c}")
            key("Enter", 13)              # Menu → Chơi (restart cùng scenario), intro hiện
            time.sleep(0.6)
            key("e", 69)                  # đóng intro, sim chạy tiếp
            time.sleep(0.8)
            st = js("JSON.stringify({m: CN.state.snap.monsters, o2: CN.state.snap.player.oxygen_ticks, d: CN.state.snap.player.pos})")
            log.append(f"live contrast={c}: {st}")
            shot(f"alerts-gather-live-{'hc' if c == '1' else 'thuong'}.png")
    finally:
        srv2.stop()

    # 3. phím H + lưu lựa chọn
    go(base + "?mock=day-quan&contrast=0")
    before = js("CN.contrast.on")
    key("h", 72)
    after = js("CN.contrast.on")
    go(base + "?mock=day-quan")
    reload_ = js("CN.contrast.on")
    log.append(f"phím H: {before} -> {after}; tải lại không có ?contrast: {reload_}")
    key("h", 72)                          # trả về tắt
finally:
    log.append("CONSOLE ERRORS: " + (json.dumps(errors, ensure_ascii=False) if errors else "none"))
    with open(os.path.join(out_dir, "run.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print("\n".join(log))
    ws.close(); proc.terminate(); srv.stop()
