# Bằng chứng P2 lát 4b: menu, intro, pause, HUD, Shop chạy với `--mode day` thật

Người làm: nganhduong123. Nhánh `p2/po-4b-hoan-thien`, cắt từ `main` @ `721088a` (đã có `sim/day.py` của lát 4a).
Trước đây UI chỉ chạy được trên mock vì chưa có `day.py`. Lần này chạy client thật với sim thật.

## Lỗi tìm thấy khi nối với sim thật và cách sửa

| # | Lỗi | Cách tìm ra | Sửa |
|---|---|---|---|
| 1 | Chạy riêng `gather`/`quan`: Esc không tạm dừng, intro không giữ đồng hồ (`state` vẫn `playing`, `time_left_ticks` 82 → 51 sau khi bấm pause) | Lái `LiveServer` qua HTTP như client | `LiveGame.live_paused` trong `chonoi/live.py` (ADR 0001, mục cập nhật) |
| 2 | `live --mode day` chỉ chơi được 1 Ngày (thiếu `--days`) | Như trên: hết Shop Ngày 1 là `days_complete` | Thêm `--days 1–5`, mặc định 5 ở bản chơi |
| 3 | HUD quán ở chế độ day hiện "Tiền ca" bằng `money` của `DaySim`, mà số này chỉ cộng khi đóng ca | Đọc `DaySim.snapshot` + `QuanSim.snapshot` (không có `shift_earned`) | `/state` thêm `shift_earned`; HUD ở chế độ day đổi "Điểm" thành "Ví" |
| 4 | Tổng kết không biết tổng số Ngày | `DaySim.snapshot` không có `days_completed` | `/state` thêm `days_completed`, `max_days`, nên Tổng kết hiện "2/2" |

Các trường thêm chỉ có trong `GET /state` của bản chơi. Headless `gather`, `quan`, `day` (seed 1, 600 tick) **giống từng byte** trước và sau thay đổi (`cmp`).

## Chạy client thật bằng trình duyệt

[`cdp_play.py`](cdp_play.py) mở Chrome headless (DevTools Protocol, cần `pip install websocket-client`), bấm phím thật qua một vòng `day` 2 Ngày với seed 42. Thời lượng pha được rút ngắn **trong bộ nhớ**, `game.contract.json` không đổi. Log đầy đủ: [`ui-day-run.txt`](ui-day-run.txt).

```
python -X utf8 docs/proof/phase-2/ui-day/cdp_play.py . <thư mục ảnh> "C:/Program Files/Google/Chrome/Application/chrome.exe"
```

| Ảnh | Bước | Kiểm được gì |
|---|---|---|
| [01](ui-day-01-menu.png) | Menu | Chơi / Thoát |
| [02](ui-day-02-dayintro.png) | DayIntro Ngày 1 | Má Tư đọc kế hoạch D1 (món + cần lấy). Sim `paused`, `time_left_ticks` đứng ở 573 trong 1 s. Tự đóng sau 4 s |
| [03](ui-day-03-gather-hud.png) | HUD sáng | Oxy, Máu, giờ (≤ 30 s đổi đỏ), độ sâu, "Cần lấy" đã/cần, giỏ, Ngày |
| [04](ui-day-04-pause.png) | Tạm dừng | Esc → làm mờ nền, menu Tiếp tục / Về menu. Esc lần nữa chạy tiếp |
| [05](ui-day-05-evening.png) | EveningIntro | Nhập kho, món nấu được. Sim `paused` |
| [06](ui-day-06-quan-hud.png) | HUD quán | 2 bếp B1/B2, 4 bàn, tiền ca (`shift_earned`), uy tín, kho, tay, Ngày |
| [07](ui-day-07-result.png) | DayResult | Khách phục vụ/bỏ đi, tiền, boa, uy tín (+/−). Sim `paused` |
| [08](ui-day-08-shop.png) | Shop | Thẻ Bình oxy / Áo phao đọc từ `tuning.shop.upgrades`; bấm 1 khi 0k → `buy_failed` "Không đủ tiền" |
| [09](ui-day-09-summary.png) | Tổng kết | Sau Shop Ngày 2: Số Ngày 2/2, tiền, điểm, uy tín |

- **Lỗi console:** không có (bắt `Runtime.exceptionThrown` và `console.error` suốt vòng chơi).
- **FPS** (đếm `requestAnimationFrame` 3 s, 1280×720): lặn 60.5, quán 60.1. Yêu cầu ≥ 30.

## Ma trận TICKET-02 §2 "Menu, pause và HUD" → bằng chứng

| Yêu cầu | Bằng chứng | Kết quả |
|---|---|---|
| Menu Chơi/Thoát | ảnh 01 | đạt |
| DayIntro 4 s, EveningIntro, DayResult, Summary | ảnh 02, 05, 07, 09; log bước 2–3, 6, 8, 11 | đạt |
| Pause làm mờ nền, đồng hồ đứng yên | ảnh 04; `test_p2_ui_live` (gather, quan, day) | đạt |
| HUD sáng: Máu, oxy < 25% nhấp nháy, giờ ≤ 30 s, cần/đã lấy | ảnh 02–03; oxy thấp ở [`../ui-gather-mock-ca-sau.png`](../ui-gather-mock-ca-sau.png) | đạt |
| "Thủy quái!", "Hết hơi!" | chỉ thấy trên mock ([`../ui-gather-mock-ca-sau.png`](../ui-gather-mock-ca-sau.png)) | **chưa đạt với sim thật**: `sim/monsters.py` (lát 2, comtrang378-ship-it) chưa có, snapshot thật chưa có `monsters[]` |
| HUD quán: kiên nhẫn từng bàn, tiến độ 2 bếp | ảnh 06 (bố cục), [`../ui-quan-mock-v11.png`](../ui-quan-mock-v11.png) (kiên nhẫn < 25%, vòng tiến độ bếp) | đạt |
| Shop UI: mua oxygen/hp, đóng Shop | ảnh 08; log bước 9–10 | đạt |
| Chữ ≥ 18 px | `CN.text` ở HUD/màn hình dùng `size ≥ 18` (chỉ nhật ký debug phím `` ` `` là 14 px) | đạt |
| ≥ 30 FPS | 60.5 / 60.1 | đạt |

## Test

[`tests-live.txt`](tests-live.txt): `tests.test_p2_ui_live` + `test_live` + `test_live_static` 21/21, cả bộ 127/127 (`PYTHONPATH=tests;. python -m unittest discover -s tests`).

Lưu ý cho QA: chạy cả bộ với `python -X utf8` thì 3 test `test_p1_contract` lỗi `NoneType.strip`. Lỗi này có sẵn trên `main` @ `721088a`, không do lát 4b.
