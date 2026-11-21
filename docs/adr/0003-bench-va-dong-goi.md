# ADR-0003: Bench có render, bot soak và bản đóng gói v1.0.0 (Contract v1.3)

- Trạng thái: **đề xuất**. PO (nganhduong123) ghi theo `docs/plan/phase-4.md` §0, Integrator (invzble-z) chốt. Phần client đã làm và kiểm (mục 1); các phần khác chưa có trên `main` @ `48c96b3`.
- Ngày: 2026-11-21.

## Bối cảnh
TICKET-04 yêu cầu bốn thứ:
- `bench_cmd --seed 42 --duration 30 --out bench.json`, đo **có render**, đủ 5 trường;
- `soak_cmd --seed 7 --days 10` với `crashes = 0`;
- chạy được từ clone sạch trong ≤ 3 lệnh;
- Release v1.0.0 kèm bản đóng gói.

Client của nhóm là web, vẽ bằng `requestAnimationFrame` trên canvas (ADR 0001), nên thời gian khung chỉ đo được trong trình duyệt. Gameplay, tuning, kho và JSONL giữ nguyên v1.2.

## Các lựa chọn đã cân nhắc (đo bench)
1. **Playwright + Chromium** (đề xuất ban đầu trong kế hoạch): điều khiển tốt, nhưng phải `pip install playwright` và `playwright install` (~150 MB). Clone sạch dễ vượt 3 lệnh, và máy lab có thể không có mạng.
2. **`webbrowser.open`**: không thêm thư viện, nhưng cần màn hình, không cố định được 1280×720 và không tự đóng.
3. **Mở Chrome/Edge có sẵn ở chế độ headless trỏ tới `/?bench=1`**, không dùng giao thức điều khiển. Client tự đo và tự `POST /bench`, nên Python chỉ cần bật server, chạy tiến trình trình duyệt, chờ kết quả rồi tắt. Không thêm thư viện. Đã thử trên Windows với Chrome headless qua vòng đo thật 30 s (`docs/proof/phase-4/ui-client/`). **Đề xuất chọn**, với lựa chọn 2 làm dự phòng khi không tìm thấy Chrome/Edge.

## Quyết định
| # | Quyết định | Hiện trạng |
|---|---|---|
| 1 | **Client bench** `/?bench=1[&warmup=3&duration=30]`:<br>• bỏ menu/intro, không gửi phím (Út Sen đứng ở bến);<br>• làm nóng 3 s từ khung đầu có snapshot, rồi ghi `frame_ms` trong 30 s;<br>• `POST /bench {frame_ms[], frames, measured_s, warmup_s, first_frame_epoch_ms, width, height, dpr}`.<br>Server live: body 1 MB riêng cho `/bench`, sai kiểu → 400, `GET /bench`, `LiveGame.bench_event` | ✅ nganhduong123 (`js/core/bench.js`, `chonoi/live.py`, `tests/test_p4_ui_bench_contrast.py`). Chạy thật: 1800 khung, 59.97 FPS |
| 2 | **`chonoi/bench.py`**:<br>• ghi lại thời điểm bắt đầu lệnh;<br>• bật `LiveServer(LiveGame("gather", tuning, {}, seed))` trên cổng ngẫu nhiên;<br>• tìm Chrome/Edge, chạy `--headless=new --window-size=1280,720 --user-data-dir=<tạm> <url>?bench=1&duration=<N>`;<br>• chờ `bench_event` (hết giờ → mã khác 0), tắt trình duyệt, tính 5 trường, ghi `bench.json` | ❌ chưa có (ttkien0710) |
| 3 | **Công thức:**<br>• `avg_fps = frames / measured_s`;<br>• `p1_low_fps = 1000 / trung bình ms của max(1, ceil(0.01 × frames)) khung chậm nhất`;<br>• `load_ms = first_frame_epoch_ms − thời điểm bắt đầu lệnh` (cùng đồng hồ epoch của máy) | 🟡 client gửi đủ dữ liệu; script bằng chứng tính thử `avg_fps`/`p1_low_fps` để đối chiếu |
| 4 | **Bot soak tất định:** mỗi Ngày gather `interact` ở frame 0 (cập bến ngay), quán không điều khiển, Shop `shop_done` ngay. Kế hoạch D1–D5 lặp ở Ngày 6–10. Bắt exception theo Ngày để đếm `crashes`, không dừng tiến trình | ❌ chưa có `chonoi/soak.py` (Quoosc + invzble-z) |
| 5 | **Đóng gói:** `git archive --format=zip --prefix=cho-noi/ <tag>` → `cho-noi-v1.0.0.zip` (Python 3, không build). Clone sạch 3 lệnh: `git clone …`, `cd cho-noi`, `python3 -m chonoi.live --mode day` | 🟡 đã thử trên WSL + giải nén zip (`docs/proof/phase-4/clean-clone.txt`, NguyenQuangDunghe161764). Chưa có `LICENSE` |
| 6 | **Manifest v1.3:** `contract_version:"1.3"`, `bench_cmd`, `soak_cmd` ở gốc `game.contract.json` | ❌ manifest vẫn `"1.1"` (invzble-z) |
| 7 | **Danh tính commit:** 9 commit tác giả "Hai Duong" không khớp ai trong `TEAM.md`. Người đó xác nhận tài khoản và ghi vào phản tư; commit không gán được người thì không tính đóng góp | ❌ chưa ai xác nhận |

## Hệ quả
| Module | File | Ảnh hưởng | Chủ |
|---|---|---|---|
| Client | `chonoi/web/js/core/bench.js`, `main.js`, `shared/screens.js` | Chế độ bench không vào luật, không đổi JSONL (headless giống từng byte) | nganhduong123 |
| Server live | `chonoi/live.py` | Thêm `POST/GET /bench`; giới hạn `/input` giữ 4 KB | nganhduong123 |
| Bench | `chonoi/bench.py`, `tests/test_p4_bench.py` | Phụ thuộc máy có Chrome/Edge; bench là lệnh riêng, không tính vào 3 lệnh chạy game, ghi rõ trong README | ttkien0710 |
| Soak | `chonoi/soak.py`, `tests/test_p4_soak.py` | Dựa trên `DaySim`, tiền/uy tín/nâng cấp/id xuyên Ngày | Quoosc, invzble-z |
| Release | `game.contract.json`, `CHANGELOG.md`, GitHub Release | Tag `phase-4` và Release v1.0.0 cùng một commit | invzble-z |
| Hợp đồng | `docs/contracts/README.md` §5 | Đã ghi `POST/GET /bench` | nganhduong123 |
