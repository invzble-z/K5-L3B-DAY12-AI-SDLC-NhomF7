# Bằng chứng P3: HUD độ tươi (AC-P3-09)

Người làm: nganhduong123. Nhánh `p3/hud-do-tuoi` cắt từ `main` @ `0586644`.

## Làm gì
- **Giỏ (sáng):** mỗi cá thể một ô theo thứ tự nhặt, gồm icon, số độ tươi (`floor`) và thanh màu (xanh ≥ 60, vàng 30–60, đỏ < 30). Dưới ngưỡng thì ô viền đỏ và chữ **"ươn"** thay cho số; góc trái đếm "N ươn". Có chữ đi kèm nên không chỉ dựa vào màu.
- **Kho (tối):** mỗi loài một nhóm thanh nhỏ, mỗi thanh một cá thể, sắp tươi → ươn, kèm "N ươn" màu đỏ.
- **Đọc được cả hai schema kho** (`docs/contracts/README.md` §2) qua `CN.inv` (`js/core/draw.js`):
  - v1.0/v1.1: mảng tên loài hoặc map đếm, HUD giữ như cũ.
  - v1.2: mảng `{id, kind, fresh}`.

  Trước đây client đếm `hold` như mảng chuỗi, nên khi contract lật sang `"1.2"` giỏ sẽ hiện sai (khóa `[object Object]`). Giờ đã sửa cả ở giỏ, "Cần lấy", thẻ hết buổi, EveningIntro, kho dư ở Shop và giỏ trên lưng Út Sen.
- Ngưỡng "ươn" đọc từ `tuning.freshness.spoiled_below`: `/state` của bản chơi chuyển khối này xuống khi có, mặc định 30.
- Mock mới: `/?mock=day-gather-v12`, `/?mock=day-quan-v12`.

## Ảnh (1280×720, Chrome headless qua [`cdp_shots.py`](cdp_shots.py), log [`run.txt`](run.txt))

| Ảnh | Nguồn | Thấy gì |
|---|---|---|
| [`hud-fresh-gather-live.png`](hud-fresh-gather-live.png) | **Live**, `sim/gather.py` thật (giỏ cá thể của Dũng, `1ae5ba7`), tuning v1.2 trong bộ nhớ | Sau ~4 s, I5 (30.4) và I6 (30.2) hao 0.5/s xuống < 30 thành "ươn", sim phát `spoiled` I6 rồi I5. I7 (14) ươn từ đầu. Góc trái "3 ươn" |
| [`hud-fresh-gather-mock.png`](hud-fresh-gather-mock.png) | `/?mock=day-gather-v12` | 8 cá thể từ 100 tới 12, 2 ươn |
| [`hud-fresh-quan-mock.png`](hud-fresh-quan-mock.png) | `/?mock=day-quan-v12` | Kho 10 cá thể theo loài, thanh từng cá thể, "1 ươn" ở cá lóc và cá linh |
| [`hud-v11-gather-mock.png`](hud-v11-gather-mock.png), [`hud-v11-quan-mock.png`](hud-v11-quan-mock.png) | Mock v1.1 cũ | HUD kho đếm không đổi (không vỡ ngược) |

**Lỗi console:** không có.

**Chưa kiểm được với sim thật:** kho quán dạng cá thể. `QuanSim.snapshot` vẫn trả map đếm, vì phần kho cá thể của Quoosc chưa vào `main`. HUD quán v1.2 mới thử trên mock; khi Quốc xong thì HUD tự hiện, không phải sửa.

## Test
- `python -m unittest tests.test_p3_hud_fresh -v`: 5 test.
  - Mock v1.2 đúng schema: id duy nhất, `fresh` trong [0,100], có cả hàng tươi lẫn hàng ươn.
  - Live v1.2 gửi mảng cá thể + `freshness`, phát `spoiled` đúng id.
  - Live v1.1 không có `freshness`.
  - Các file HUD dùng `CN.inv`.
- Cả bộ: 141/141 (`PYTHONPATH=tests;. python -m unittest discover -s tests`).
