"use strict";
/*
 * Màn hình của bản chơi (Ticket-02 §2 "Menu, pause và HUD"): Menu chính (Chơi/Thoát), DayIntro (Má Tư đọc kế hoạch,
 * tự chuyển sau 4 s hoặc khi nhấn phím), EveningIntro (nhập kho, món nấu được), DayResult, Summary, menu Tạm dừng.
 * Khi hiện intro/kết quả, client gửi `pause` để đồng hồ và timer gameplay đứng yên (xem docs/clarify.md #3).
 * Số liệu hiển thị lấy từ snapshot + sự kiện; không tự tính luật.
 */
(function (CN) {
  const { ctx, text, ui, COLOR, kname, dname } = CN;
  const newStats = () => ({ served: 0, left: 0, money: 0, tips: 0 });

  const S = (CN.screens = {
    mode: CN.state.mock || CN.bench.on ? "play" : "menu",   // menu | play | exit (bench: vào thẳng cảnh)
    menuIdx: 0,
    card: null,                               // {kind: day|evening|result, data, since}
    pausedByCard: false,
    pendingStart: false,
    stats: newStats(),
    dishesSold: {},
    repAtQuan: null,

    start() {
      S.mode = "play"; S.card = null; S.pausedByCard = false; S.pendingStart = true;
      S.stats = newStats(); S.dishesSold = {}; S.repAtQuan = null;
      CN.input.clear(); CN.net.restart();
    },

    onKey(k) {
      if (S.mode === "menu") {
        if (k === "arrowup" || k === "arrowdown" || k === "w" || k === "s") S.menuIdx = 1 - S.menuIdx;
        else if (k === "enter" || k === " " || k === "e") {
          if (S.menuIdx === 0) S.start();
          else { S.mode = "exit"; try { window.close(); } catch (e) { /* trình duyệt có thể chặn */ } }
        }
        return true;
      }
      if (S.mode === "exit") { if (k === "enter") S.mode = "menu"; return true; }
      if (S.card) { closeCard(); return true; }
      const snap = CN.state.snap;
      if (snap && snap.state === "paused") {
        if (k === "escape" || k === "p") CN.net.tap("pause");
        else if (k === "m") S.mode = "menu";
        return true;
      }
      if (snap && snap.finished && k === "m") { S.mode = "menu"; return true; }
      return false;
    },

    update(snap, fresh) {
      if (S.mode !== "play" || CN.bench.on) return;   // bench: không intro/thẻ (thẻ gửi pause, làm mờ cảnh)
      for (const e of fresh) handle(e, snap);
      // P1 chạy riêng từng buổi chưa phát phase_start: hiện intro một lần ngay sau khi bấm Chơi / R.
      if (S.pendingStart && (CN.events.restarted || (snap.tick || 0) < 30)) {
        S.pendingStart = false;
        if (snap.day === undefined && !S.card) {
          if ((snap.phase || snap.mode) === "quan") showCard("evening", { stock: CN.inv.counts(snap.stock), menu: snap.menu });
          else showCard("day", { plan: snap.day_plan });
        }
      }
      if (S.card && S.card.kind === "day" && CN.now() - S.card.since > 4) closeCard();
    },

    drawFull(w, h) { if (S.mode === "menu") drawMenu(w, h); else drawExit(w, h); },

    drawOverlay(w, h, snap) {
      if (S.card) return drawCard(w, h, snap);
      if (snap.state === "paused") return drawPause(w, h);
      if (snap.day !== undefined && snap.finished) drawSummary(w, h, snap);
    },
  });

  function showCard(kind, data) {
    const snap = CN.state.snap;
    S.card = { kind, data, since: CN.now() };
    S.pausedByCard = false;
    if (snap && snap.state !== "paused" && !snap.finished) { CN.net.tap("pause"); S.pausedByCard = true; }
    CN.input.clear();
  }
  function closeCard() {
    S.card = null;
    if (S.pausedByCard) CN.net.tap("pause");
    S.pausedByCard = false;
  }

  function handle(e, snap) {
    const d = e.data || {};
    switch (e.name) {
      case "day_start": S.stats = newStats(); break;
      case "phase_start": {
        const ph = e.phase || snap.phase;
        if (ph === "gather") showCard("day", { day: e.day ?? snap.day, plan: snap.day_plan });
        else if (ph === "quan") {
          S.repAtQuan = snap.reputation;
          showCard("evening", { day: e.day ?? snap.day, stock: CN.inv.counts(snap.stock), plan: snap.day_plan, menu: snap.menu });
        }
        break;
      }
      case "served": { S.stats.served++; const id = d.dish_id || d.dish; if (id) S.dishesSold[id] = (S.dishesSold[id] || 0) + 1; break; }
      case "customer_left": S.stats.left++; break;
      case "paid": S.stats.money += d.price || 0; S.stats.tips += d.tip || 0; break;
      case "quan_end":
        if (snap.day !== undefined || e.day !== undefined) {
          const rep = d.reputation ?? snap.reputation ?? 0;
          showCard("result", { day: e.day ?? snap.day, ...S.stats, rep, repDelta: rep - (S.repAtQuan ?? rep) });
        }
        break;
    }
  }

  // ---------- vẽ ----------
  function dim(w, h, a = 0.62) { ctx.fillStyle = `rgba(8,12,18,${a})`; ctx.fillRect(0, 0, w, h); }
  function card(w, h, cw, ch) { const x = (w - cw) / 2, y = Math.max(20, (h - ch) / 2); ui.panel(x, y, cw, ch, { fill: "rgba(20,28,36,.96)", r: 14 }); return [x, y]; }
  function footer(x, y, cw, label) { text(label, x + cw / 2, y, { size: 18, align: "center", color: COLOR.muted }); }

  function drawMenu(w, h) {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, "#f6d7a7"); g.addColorStop(0.45, "#5aa9b8"); g.addColorStop(1, "#0b2a44");
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    text("Quán Ăn Chợ Nổi", w / 2, h * 0.3, { size: 52, align: "center", weight: "800", color: "#3a2412", noOutline: true });
    text("Một ngày của Út Sen trên sông Rạch Sen", w / 2, h * 0.3 + 44, { size: 22, align: "center", color: "#4a3018", noOutline: true });
    ["Chơi", "Thoát"].forEach((label, i) => {
      const y = h * 0.55 + i * 64, sel = S.menuIdx === i;
      ui.panel(w / 2 - 120, y - 26, 240, 52, { fill: sel ? "rgba(242,194,48,.92)" : "rgba(12,20,28,.7)", r: 12 });
      text(label, w / 2, y + 1, { size: 24, align: "center", base: "middle", weight: "800", color: sel ? "#2a1a0a" : COLOR.text, noOutline: sel });
    });
    text("↑/↓ chọn · Enter xác nhận · H tương phản cao: " + (CN.contrast.on ? "Bật" : "Tắt"), w / 2, h - 40, { size: 18, align: "center", color: CN.contrast.on ? "#fff" : "#dfe9ee" });
  }

  function drawExit(w, h) {
    ctx.fillStyle = COLOR.bg; ctx.fillRect(0, 0, w, h);
    text("Đã thoát. Đóng tab để kết thúc.", w / 2, h / 2, { size: 24, align: "center" });
    text("Enter: về menu", w / 2, h / 2 + 40, { size: 18, align: "center", color: COLOR.muted });
  }

  function iconRow(items, x, y, maxW) {
    let cx = x;
    for (const [k, n] of items) {
      if (cx > x + maxW - 80) break;
      ui.icon(k, cx + 16, y - 6, 30);
      text("×" + n, cx + 36, y, { size: 20, weight: "700" });
      cx += 92;
    }
  }

  function drawCard(w, h, snap) {
    dim(w, h);
    const c = S.card, d = c.data;
    if (c.kind === "day") {
      const dishes = Object.entries((d.plan || {}).dishes || {}), ing = Object.entries((d.plan || {}).ingredients || {});
      const cw = 620, ch = 230 + dishes.length * 40 + (ing.length ? 70 : 0);
      const [x, y] = card(w, h, cw, ch);
      text(d.day !== undefined ? "Ngày " + d.day : "Buổi sáng", x + cw / 2, y + 52, { size: 34, align: "center", weight: "800", color: COLOR.gold });
      if (dishes.length) {
        text("Má Tư dặn: tối nay quán nấu", x + 30, y + 98, { size: 20 });
        dishes.forEach(([id, n], i) => { ui.dish(id, x + 52, y + 132 + i * 40, 34); text(dname(id) + " × " + n, x + 84, y + 140 + i * 40, { size: 20, weight: "600" }); });
        if (ing.length) { const yy = y + 160 + dishes.length * 40; text("Cần lấy:", x + 30, yy, { size: 18, color: COLOR.muted }); iconRow(ing, x + 30, yy + 40, cw - 60); }
      } else text("Lặn hái nguyên liệu cho quán tối nay.", x + cw / 2, y + 110, { size: 20, align: "center" });
      const left = Math.max(0, 4 - (CN.now() - c.since));
      footer(x, y + ch - 24, cw, "Nhấn phím bất kỳ để xuống ghe · tự đi sau " + Math.ceil(left) + " s");
    } else if (c.kind === "evening") {
      const stock = Object.entries(d.stock || {}).filter(([, n]) => n > 0);
      const total = stock.reduce((a, [, n]) => a + n, 0);
      const menu = d.menu || {}, ids = Object.keys((d.plan || {}).dishes || menu);
      const cookable = ids.map((id) => {
        const r = (menu[id] || {}).recipe || {};
        const ks = Object.keys(r);
        return [id, ks.length ? Math.min(...ks.map((k) => Math.floor(((d.stock || {})[k] || 0) / r[k]))) : 0];
      });
      const cw = 640, ch = 250 + cookable.length * 38;
      const [x, y] = card(w, h, cw, ch);
      text("Chiều tối — mở quán", x + cw / 2, y + 50, { size: 32, align: "center", weight: "800", color: COLOR.gold });
      text("Nhập kho: " + total + " nguyên liệu", x + 30, y + 96, { size: 20 });
      if (stock.length) iconRow(stock, x + 30, y + 136, cw - 60); else text("(kho rỗng)", x + 30, y + 136, { size: 18, color: COLOR.muted });
      text("Món nấu được:", x + 30, y + 182, { size: 18, color: COLOR.muted });
      cookable.forEach(([id, n], i) => {
        const yy = y + 214 + i * 38;
        ctx.globalAlpha = n > 0 ? 1 : 0.45;
        ui.dish(id, x + 52, yy - 8, 32);
        text(dname(id), x + 84, yy, { size: 20 });
        text(n + " suất", x + cw - 30, yy, { size: 20, align: "right", weight: "700" });
        ctx.globalAlpha = 1;
      });
      footer(x, y + ch - 20, cw, "Nhấn phím bất kỳ để mở quán");
    } else if (c.kind === "result") {
      const rows = [
        ["Khách đã phục vụ", d.served], ["Khách bỏ đi", d.left], ["Tiền món", d.money + "k"], ["Boa", d.tips + "k"],
        ["Uy tín", d.rep.toFixed(1) + " (" + (d.repDelta >= 0 ? "+" : "") + d.repDelta.toFixed(1) + ")"],
      ];
      const cw = 520, ch = 130 + rows.length * 42;
      const [x, y] = card(w, h, cw, ch);
      text("Kết quả Ngày " + (d.day ?? ""), x + cw / 2, y + 50, { size: 32, align: "center", weight: "800", color: COLOR.gold });
      rows.forEach(([k, v], i) => {
        text(k, x + 40, y + 100 + i * 42, { size: 20 });
        text(String(v), x + cw - 40, y + 100 + i * 42, { size: 20, align: "right", weight: "700", color: k === "Khách bỏ đi" && d.left ? COLOR.danger : COLOR.text });
      });
      footer(x, y + ch - 20, cw, "Nhấn phím bất kỳ để vào Shop");
    }
  }

  function drawPause(w, h) {
    dim(w, h, 0.7);
    const cw = 440, ch = 280;
    const [x, y] = card(w, h, cw, ch);
    text("Tạm dừng", x + cw / 2, y + 54, { size: 32, align: "center", weight: "800" });
    let kw = ui.key(x + 70, y + 112, "Esc/P");
    text("Tiếp tục", x + 82 + kw, y + 113, { size: 20, base: "middle" });
    kw = ui.key(x + 70, y + 162, "M");
    text("Về menu", x + 82 + kw, y + 163, { size: 20, base: "middle" });
    kw = ui.key(x + 70, y + 212, "H");
    text("Tương phản cao: " + (CN.contrast.on ? "Bật" : "Tắt"), x + 82 + kw, y + 213, { size: 20, base: "middle" });
  }

  function drawSummary(w, h, snap) {
    dim(w, h, 0.75);
    const best = Object.entries(S.dishesSold).sort((a, b) => b[1] - a[1])[0];
    const rows = [
      ["Số Ngày", (snap.days_completed ?? snap.day ?? "?") + (snap.max_days ? "/" + snap.max_days : "")], ["Tổng tiền", (snap.earned ?? 0) + "k"], ["Tiền còn", (snap.money ?? 0) + "k"],
      ["Tổng điểm", snap.score ?? 0], ["Uy tín", (snap.reputation ?? 0).toFixed(1)], ["Món bán chạy", best ? dname(best[0]) + " × " + best[1] : "—"],
    ];
    const cw = 560, ch = 140 + rows.length * 42;
    const [x, y] = card(w, h, cw, ch);
    text("Tổng kết", x + cw / 2, y + 52, { size: 34, align: "center", weight: "800", color: COLOR.gold });
    rows.forEach(([k, v], i) => {
      text(k, x + 40, y + 104 + i * 42, { size: 20 });
      text(String(v), x + cw - 40, y + 104 + i * 42, { size: 20, align: "right", weight: "700" });
    });
    footer(x, y + ch - 22, cw, "R chơi lại · M về menu");
  }
})(window.CN);
