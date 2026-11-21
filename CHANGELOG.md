# Changelog

> Nháp do PO (nganhduong123) viết ở Phase 3, Integrator (invzble-z) duyệt và chốt khi gắn tag. Mỗi mục ghi theo phase và `contract_version`.

## Phase 4 — Contract v1.3 "Phát hành v1.0.0" (tag `phase-4`, `v1.0.0`)

### Thêm
- **Manifest v1.3 (AC-P4-01)**: Nâng `contract_version: "1.3"`, khai báo `bench_cmd: "python3 -m chonoi.bench"` và `soak_cmd: "python3 -m chonoi.soak"`.
- Bổ sung hàm `validate_contract(c)` trong `chonoi/contract.py` kiểm tra bắt buộc phải có `bench_cmd` và `soak_cmd`.
- Bộ test đơn vị `tests/test_p4_contract.py` kiểm tra cấu hình Contract v1.3.
- **Benchmark render (AC-P4-02)**: Cài đặt module `chonoi/bench.py` tự động đo render 30s với Chromium headless (`?bench=1`), thu thập frame_ms và tính toán 5 chỉ số (avg_fps ~46.92, p1_low ~29.79).
- **Soak testing DaySim (AC-P4-03)**: Cài đặt module `chonoi/soak.py` kiểm thử 10 ngày đêm liên tục, đạt 0 crash và tính tất định tuyệt đối.
- **Client Web & Live Server (AC-P4-04)**: Tích hợp 3 cảnh báo trực quan bằng chữ và biểu tượng (Thủy quái gần, Oxy sắp hết, Khách sắp giận) và chế độ Độ tương phản cao (High Contrast, phím H hoặc nút toggle).
- **Phát hành & Đóng gói (AC-P4-05, AC-P4-07)**: Kiểm chứng clone sạch trong ≤ 3 lệnh (`docs/proof/phase-4/clean-clone.txt`), thêm `LICENSE`, Release Notes (`docs/release-notes-v1.0.0.md`), gói ZIP `cho-noi-v1.0.0.zip` và GitHub Release v1.0.0.
- ADR 0003: Bench có render, bot soak và bản đóng gói v1.0.0.

## Phase 3 — Contract v1.2 "Mùa Nước Nổi"

### ⚠️ Breaking change
- **File kho đổi schema.** Kho đếm `{"items":{"ca_linh":3}}` thành kho cá thể `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`, xuất theo id. Khi `contract_version` là `"1.2"`, file kho đếm, id trùng hoặc rỗng, kind lạ, `fresh` ngoài [0,100] đều trả **mã 2**.
- **Đổi sang mảng cá thể:** `gather_end.data.inventory`, snapshot `hold` (gather) và `stock` (quán), `faint.lost`/`monster_hit.lost`, `cook_started.items`.
- **Scenario đổi:** `gather.hold`, `quan.stock` thành mảng cá thể; `customers[].reserved` thành mảng id.

### Thêm
- Khối `freshness {initial, gather_decay_per_s, quan_decay_per_s, spoiled_below}` trong manifest.
- Hao tươi 0.5/s ở giỏ, 0.25/s ở kho quán, kẹp 0. Món chín không hao; pause và Shop không hao.
- Event `spoiled {item_id, kind, location}`, phát đúng một lần khi `fresh` đi từ ≥ 30 xuống < 30.
- Giá món `base_price = floor(giá × trung bình fresh / 100)`, boa tính trên giá đã chốt.
- Client web: HUD độ tươi cho từng cá thể ở giỏ và kho, chữ "ươn" khi < 30. Mock `day-gather-v12`, `day-quan-v12`.
- ADR 0002 (Fraction, `Item` dùng chung, bộ đếm `I<n>`, adapter theo version, thứ tự trong tick).

### Sửa (gộp sau tag `phase-2`, PR #13)
- `chonoi.live --mode day --days 1–5` (mặc định 5).
- Pause khi chạy riêng gather/quan.
- `/state` thêm `shift_earned`, `days_completed`, `max_days` (chỉ để hiển thị).

### Trạng thái trên `main` (`48c96b3`)
- ✅ Giỏ cá thể, hao tươi, `spoiled` ở gather (`1ae5ba7`).
- ✅ Giá theo độ tươi, `cook_started.items` (AC-P3-05).
- ✅ HUD độ tươi.
- ✅ `Item` + adapter 2 schema + khối `freshness` (`0748ff3`, AC-P3-01). ✅ Bàn giao `day` giữ id xuyên Ngày (`48c96b3`, AC-P3-08).
- ❌ Chưa có: scenario v1.2, kho cá thể + hao tươi ở quán, lật `"1.2"`.

### Cách sửa fixture/test cũ khi lật `"1.2"`
1. File kho: đổi mỗi cặp `kind: n` thành `n` object `{"id":"I<k>","kind":kind,"fresh":100}`, id tăng dần, rồi sắp theo id.
2. `scenario.gather.hold` (mảng tên loài) → mảng object như trên, **giữ thứ tự nhặt** (cuối mảng là mới nhất, LIFO khi mất hàng).
3. `scenario.quan.stock` → mảng cá thể. `customers[].reserved` từ map `kind: n` → mảng id có trong `stock`, chưa ươn, đủ công thức, không dùng chung giữa các đơn.
4. Assert so `fresh` dùng giá trị sau `float(Fraction)` và làm tròn 3 chữ số như JSONL, đừng so float tự tính.
5. Mọi test đổi vì schema mới phải ghi lý do trong commit (`AGENTS.md`).

## phase-2 — Contract v1.1 "Một ngày ở chợ nổi" (tag `phase-2` @ `ba17f4d`)
- Số chuẩn v1.1: 6 nguyên liệu (`ca_keo`, `keo_neo`), 6 món, N1–N6, 2 bếp B1/B2, 4 bàn T1–T4, `day_plan` D1–D5, `shop.upgrades` oxygen/hp, `shop.max_ticks`.
- Gather: cá bơi, đổi hướng, sinh theo lịch (`fish_spawned`); cá kèo yield 2.
- Quán:
  - 2 bếp lấy đơn cũ nhất; tương tác chọn đối tượng gần nhất.
  - Lịch khách 120 + 900·k; `menu_filter` theo kế hoạch Ngày; đóng ca dọn món.
  - Mở rộng `burn` (cháy món).
- `--mode day --days N`: Gather → Quán → Shop. Bàn giao kho trong bộ nhớ, `buy`/`shop_done`/`pause`, `bought`/`buy_failed`/`shop_end`, `days_completed`.
- Client web: Menu, DayIntro, EveningIntro, DayResult, Tổng kết, Tạm dừng, Shop, HUD sáng/quán, vẽ lại cảnh.
- Hợp đồng tích hợp `docs/contracts/README.md`, ADR 0001.
- **Giới hạn đã biết:**
  - Chưa có Cá Sấu (`sim/monsters.py`).
  - Một số tên trường event lệch hợp đồng (`docs/contracts/README.md` §10).
  - Manifest chưa khai khóa sinh cá kèo.

## phase-1 — Contract v1.0 (tag `phase-1` @ `4c83ed8`)
- `gather`:
  - Bơi, oxy, ngạt, Máu, ngất.
  - Hái ở mặt nước, bắt cá, giỏ 12 ô, cập bến.
  - `--inventory-out` ghi nguyên tử.
- `quan`:
  - Khách theo lịch, giữ nguyên liệu, kiên nhẫn, rời bàn trừ uy tín.
  - Bếp, bưng, phục vụ, tiền, boa, uy tín.
  - Đọc `--inventory`.
- Headless tất định theo seed (`Streams`), mã thoát 0/1/2, scenario mâu thuẫn → mã 2.
- TEAM.md 7 người, `docs/clarify.md`, 2 skill trong `.agents/skills/`, `AGENTS.md`, HUD tối thiểu.
