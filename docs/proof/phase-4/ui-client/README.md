# Bằng chứng P4 phía client: bench `?bench=1`, 3 cảnh báo, chế độ tương phản cao

Người làm: nganhduong123. Nhánh `p4/bench-tuong-phan`, nối tiếp `p3/hud-do-tuoi`.
Chạy lại: `python -X utf8 docs/proof/phase-4/ui-client/cdp_p4.py . docs/proof/phase-4/ui-client "<chrome.exe>" 30` (Chrome headless qua DevTools Protocol, cần `websocket-client`). Log: [`run.txt`](run.txt).

## 1. Bench có render, phía client (AC-P4-02, phần của nganhduong123)
**Hành vi của `/?bench=1[&warmup=3&duration=30]`:**
- Bỏ menu/intro, không gửi phím: Út Sen đứng yên ở bến. Cảnh do máy chủ dựng; `bench_cmd` chọn `--mode gather --seed 42`.
- Làm nóng 3 s kể từ khung đầu có snapshot, rồi ghi thời gian từng khung trong 30 s.
- Gửi `POST /bench` với các trường: `frame_ms[]`, `frames`, `measured_s`, `warmup_s`, `first_frame_epoch_ms`, `width`, `height`, `dpr`.

**Máy chủ live:**
- `POST /bench`: kiểm kiểu (sai → 400), giới hạn body 1 MB riêng cho đường này; `/input` vẫn 4 KB.
- `GET /bench` trả `{ready, result}`.
- `LiveGame.bench_event` / `bench_result` để `chonoi/bench.py` (ttkien0710) chờ trong cùng tiến trình.
- Hợp đồng: `docs/contracts/README.md` §5.

**Chạy thật** (Chrome headless 1280×720, seed 42, 3 s + 30 s), [`bench-client.json`](bench-client.json):

| frames | measured_s | avg_fps | p1_low_fps | khung đầu sau khi mở trang |
|---|---|---|---|---|
| 1800 | 30.017 | 59.97 | 51.4 | 91 ms |

- `avg_fps` và `p1_low_fps` ở đây tính theo công thức `docs/plan/phase-4.md` §0 **chỉ để đối chiếu**. `bench.json` chính thức (5 trường, `load_ms` tính từ lúc chạy lệnh) do `chonoi/bench.py` của Kiên tính; file này **chưa có trên `main`**, nên AC-P4-02 chưa đạt đầu-cuối.
- Ảnh: [`bench-running.png`](bench-running.png), [`bench-done.png`](bench-done.png).

## 2. Ba cảnh báo + chế độ tương phản cao (AC-P4-04)
Mỗi cảnh báo có **biểu tượng tam giác "!" + chữ** trong khung viền màu (`ui.alert`), nên không chỉ dựa vào màu:

| Cảnh báo | Điều kiện | Chữ |
|---|---|---|
| Thủy quái gần | quái đang `chase` hoặc trong `detect_radius`, người chơi ở d ≥ 10 | "Thủy quái! Tránh xa" + viền tím màn hình |
| Oxy sắp hết | dưới nước, oxy < 25% (= 0: chữ lớn giữa màn hình) | "Sắp hết hơi! Lên thở" / "Hết hơi! Lên mặt nước!" |
| Khách sắp giận | `waiting`/`ordered`, kiên nhẫn < 25% | banner "Khách sắp giận: T1, …" + nhãn "Sắp giận!" trên bàn |

**Chế độ tương phản cao:**
- Bật/tắt: phím **H** ở mọi màn hình, có dòng trạng thái trong menu chính và menu Tạm dừng; `?contrast=1|0` ghi đè.
- Thay đổi khi bật: khung đen đặc, chữ trắng viền đen, viền dày 2–4 px, màu bão hòa.
- Lưu lựa chọn trong `localStorage`, có try/catch nên trình duyệt chặn lưu thì vẫn chạy, chỉ mặc định tắt.
- Đã kiểm: bấm H rồi tải lại trang không có `?contrast` vẫn giữ trạng thái bật.

| Ảnh | Thấy gì |
|---|---|
| [`alerts-gather-thuong.png`](alerts-gather-thuong.png), [`alerts-gather-hc.png`](alerts-gather-hc.png) | Thủy quái + Sắp hết hơi, chế độ thường / tương phản cao |
| [`alerts-quan-thuong.png`](alerts-quan-thuong.png), [`alerts-quan-hc.png`](alerts-quan-hc.png) | Khách sắp giận T1 (banner + nhãn trên bàn) |
| [`alerts-gather-live-hc.png`](alerts-gather-live-hc.png), [`alerts-gather-live-thuong.png`](alerts-gather-live-thuong.png) | **Sim thật** (`sim/monsters.py` đã vào `main`): người chơi cạnh M1 ở d = 22, oxy 300/1800 → "Thủy quái! Tránh xa" + "Sắp hết hơi! Lên thở", M1 cắn "-1 Máu" |
| [`pause-menu-hc.png`](pause-menu-hc.png) | Menu Tạm dừng có "H Tương phản cao: Bật" |

- Cảnh báo thủy quái và oxy đã chụp với **sim thật**; cảnh báo khách sắp giận chụp trên mock `day-quan`. Snapshot quái thật dùng khóa `species`, mock cũ dùng `kind`; client đọc được cả hai.
- **Lỗi đã sửa khi chụp:** nhãn "Sắp giận!" của T1 bị biển số T3 vẽ đè. Giờ gom nhãn và vẽ sau tất cả bàn. Chữ tối trên nền sáng (nút phím, bong bóng) không viền đen để khỏi nhoè.
- Lỗi console: không có.

## Test
- `python -m unittest tests.test_p4_ui_bench_contrast -v`: 7 test.
  - `/bench`: chưa có kết quả, payload 30 s (> 4 KB) được nhận, 6 payload sai bị 400, giới hạn `/input` không đổi.
  - `index.html` nạp `bench.js` đúng thứ tự; đủ chữ 3 cảnh báo; phím H; `localStorage` có try/catch.
- Cả bộ sau khi gộp `main` @ `48c96b3`: 182 test OK, gồm 5 expected failure của lát khác (`PYTHONPATH=tests;. python -m unittest discover -s tests`).
