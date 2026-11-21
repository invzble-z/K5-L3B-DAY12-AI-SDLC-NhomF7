"use strict";
/*
 * Bàn phím. Màn hình (menu, intro, pause) được ưu tiên xử lý phím trước; còn lại là phím chơi.
 * WASD/mũi tên di chuyển · E interact · Space catch · Q attack · F photo (mở rộng) · Esc/P pause · R chơi lại
 * Shop: 1..n mua nâng cấp · Enter đóng Shop · H tương phản cao · ` bật/tắt nhật ký sự kiện.
 */
(function (CN) {
  const down = new Set();
  const MOVE_KEYS = { w: "u", arrowup: "u", s: "d", arrowdown: "d", a: "l", arrowleft: "l", d: "r", arrowright: "r" };
  const HOLD_KEYS = { e: "interact", " ": "catch", q: "attack", f: "photo" };

  function current() {
    const snap = CN.state.snap;
    const phase = snap ? snap.phase || snap.mode : "gather";
    const dx = (down.has("r") ? 1 : 0) - (down.has("l") ? 1 : 0);
    let dy = (down.has("d") ? 1 : 0) - (down.has("u") ? 1 : 0);   // gather: xuống = d dương
    if (phase === "quan") dy = -dy;                               // quan: lên (bắc) = z dương
    const inp = { move: [dx, dy] };
    for (const b of Object.values(HOLD_KEYS)) inp[b] = down.has(b);
    return inp;
  }
  const send = () => CN.net.sendState(current());

  addEventListener("keydown", (e) => {
    const k = e.key.toLowerCase();
    if (k === " " || k.startsWith("arrow")) e.preventDefault();
    if (e.repeat) return;
    if (k === "`") { CN.debug = !CN.debug; return; }
    if (k === "h") { CN.contrast.toggle(); return; }   // tương phản cao, dùng được ở mọi màn hình
    if (CN.screens && CN.screens.onKey(k)) return;
    const snap = CN.state.snap;
    if (MOVE_KEYS[k]) down.add(MOVE_KEYS[k]);
    else if (HOLD_KEYS[k]) down.add(HOLD_KEYS[k]);
    else if (k === "escape" || k === "p") CN.net.tap("pause");
    else if (k === "r") CN.screens.start();
    else if (snap && snap.phase === "shop") {
      if (k === "enter") CN.net.tap("shop_done");
      const ids = CN.shop ? CN.shop.ids(snap) : [];
      const n = parseInt(k, 10);
      if (n >= 1 && n <= ids.length) CN.net.buy(ids[n - 1]);
    }
    send();
  });
  addEventListener("keyup", (e) => {
    const k = e.key.toLowerCase();
    if (MOVE_KEYS[k]) down.delete(MOVE_KEYS[k]);
    else if (HOLD_KEYS[k]) down.delete(HOLD_KEYS[k]);
    send();
  });
  addEventListener("blur", () => { down.clear(); send(); });

  CN.input = { clear() { down.clear(); send(); } };
})(window.CN);
