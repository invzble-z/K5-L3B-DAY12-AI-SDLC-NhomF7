# ADR-0001: Client web tách module; máy chủ live phục vụ file tĩnh và nút v1.1

- Trạng thái: đề xuất (chờ cả nhóm đồng ý)
- Ngày, người đề xuất: 2026-11-21, nganhduong123 · cập nhật cho Ticket-02 (Phase 2)

## Bối cảnh
Cần UI demo sớm và Ticket-02 yêu cầu menu, pause, Shop, HUD (chữ ≥ 18 px). Client starter là một file `index.html`; `chonoi/live.py` chỉ trả `index.html` và chỉ nhận `move`/`interact`/`catch`. Người làm UI phải chờ luật xong mới thấy oxy, Cá Sấu, khách, Shop.

## Các lựa chọn đã cân nhắc
1. Viết lại game bằng engine (Phaser/Godot): phải viết luật hai lần, bản chơi và bản chấm (headless) dễ lệch. Loại.
2. Giữ một file `index.html`: nhiều người sửa chung một file, dễ xung đột. Loại.
3. Giữ kiến trúc starter (sim Python duy nhất + máy chủ HTTP local + client Canvas), tách client thành module theo pha, thêm chế độ mock. **Chọn.**

## Quyết định
- `chonoi/web/js/{core,gather,quan,shop,shared}/` + `main.js`; `mock/*.json` theo Test Contract v1.1; `assets/`.
- Sửa **file khung** `chonoi/live.py`:
  - `GET /<file>`: file tĩnh trong `chonoi/web/` theo danh sách đuôi cho phép, chặn thoát khỏi thư mục.
  - `POST /input`: nhận thêm `pause`, `shop_done`, `attack`, `photo` (bool) và `buy` (chuỗi, chỉ có tác dụng ở một tick) qua `_LiveInputsV11`; `InputState` có thêm `.buy`.
  - `GET /state`: `meta` theo `snap.phase` (gather/quan/shop), thêm `menu`.
- Intro/kết quả của vòng ngày là màn hình bản chơi; client gửi `pause` để timer đứng yên (`docs/clarify.md` #3).

### Cập nhật sau khi lát 4a vào `main` (`721088a`)
- **Pause khi chạy riêng `gather`/`quan`:** sim của hai pha này không đọc `pause` (headless v1.0 chỉ có `interact`, `catch`), nên nút Tạm dừng và intro không giữ được đồng hồ. `LiveGame` tự giữ cờ `live_paused`: cạnh `pause` bật/tắt cờ, trong lúc dừng không gọi `step()` (tick, timer đứng yên, cạnh hành động bị bỏ), `state:"paused"` trong `/state`. Mode `day` để `DaySim` tự xử lý như hợp đồng.
- **`--days 1–5`** cho `chonoi.live --mode day`, mặc định **5** ở bản chơi (đi hết D1–D5 rồi Tổng kết). Headless giữ mặc định 1.
- **Trường chỉ để hiển thị trong `/state`** (không vào JSONL): `shift_earned` (tiền ca đang chạy, vì `money` của `DaySim` chỉ cộng khi đóng ca), `days_completed`, `max_days`.
- Kiểm chứng: `tests/test_p2_ui_live.py` và chạy client thật bằng Chrome headless qua vòng 2 Ngày (`docs/proof/phase-2/ui-day/`). Headless `gather`/`quan`/`day` seed 1 giống từng byte trước và sau thay đổi.

## Hệ quả
- Headless, sim, Test Contract: không đổi. Lát 4a đọc `inp.pressed("pause")`, `inp.pressed("shop_done")`, `inp.buy`.
- `tests/test_live.py` (của giảng viên) vẫn chạy; `tests/test_live_static.py` kiểm file tĩnh, mock, chặn thoát thư mục, nút v1.1.
- Đổi tên trường snapshot/sự kiện phải sửa cả mock.
