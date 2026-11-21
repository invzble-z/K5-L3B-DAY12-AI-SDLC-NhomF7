# Client web (bản chơi trên trình duyệt)

Client **chỉ vẽ**: đọc snapshot từ `GET /state`, gửi phím qua `POST /input`. Mọi luật nằm trong `chonoi/sim/` (cùng lớp với headless), nên hiệu ứng, âm thanh, đồ họa thêm ở đây **tự tắt ở headless**. Giao diện theo Ticket-02 §2 "Menu, pause và HUD"; phong cách mượn quy ước chung của thể loại lặn/mở quán (camera bám, bình oxy, bong bóng order, tổng kết cuối buổi), hình và nhân vật là của lab.

## Chạy

```powershell
python -X utf8 -m chonoi.live --mode day         # vòng D1–D5 (mặc định 5 Ngày; --days 1..5 để chơi ngắn hơn)
python -X utf8 -m chonoi.live --mode gather      # hoặc --mode quan: chơi riêng một buổi
```

Mở http://127.0.0.1:8000/ → Menu → **Chơi**. (`-X utf8` tránh lỗi in tiếng Việt trên Windows.)

Luồng `day`: Menu → DayIntro (4 s) → Lặn → EveningIntro → Quán → DayResult → Shop → Ngày kế … → Tổng kết. Intro/kết quả gửi `pause` nên đồng hồ đứng yên. Chạy riêng `gather`/`quan`, máy chủ live tự giữ trạng thái tạm dừng (sim hai pha này không có `pause`), xem ADR 0001.

**Mock** (vẽ khi sim chưa xong; phím không gửi lên máy chủ, `P` bật/tắt tạm dừng tại chỗ, `R` đọc lại file):

| URL | Thử gì |
|---|---|
| `/?mock=gather` | Lặn: oxy thấp, giỏ, sự kiện |
| `/?mock=day-gather` | DayIntro (Má Tư đọc kế hoạch D1), Cá Sấu đuổi, "Thủy quái!", danh sách cần lấy |
| `/?mock=quan` | Quán chạy riêng: 2 bếp, 4 bàn, món trên tay |
| `/?mock=day-quan` | EveningIntro (nhập kho, món nấu được), kiên nhẫn < 25% |
| `/?mock=day-shop` | Shop nâng cấp oxygen/hp |
| `/?mock=day-summary` | Tổng kết sau Ngày 5 |
| `/?mock=day-gather-v12` | v1.2: giỏ cá thể, số + thanh độ tươi từng ô, "ươn" khi < 30 |
| `/?mock=day-quan-v12` | v1.2: kho cá thể, thanh độ tươi theo loài, số hàng ươn |

Sửa file JSON trong `mock/` để thử trạng thái khác (vd. `"state": "paused"`, `"finished": true`).

## Phím

WASD/mũi tên di chuyển · E tương tác · Space bắt cá · Esc/P tạm dừng (M về menu) · **H tương phản cao** (lưu lại; `?contrast=1|0` ghi đè) · R chơi lại · Shop: 1..n mua, Enter đóng · Q/F cho mở rộng Lao/Sổ tay · `` ` `` nhật ký sự kiện (debug).

## Cấu trúc (mỗi thư mục một chủ)

| File | Việc |
|---|---|
| `js/core/draw.js` | Canvas, bảng màu, tên loài/món, chữ, thanh, khung bo góc |
| `js/core/art.js` | Nét vẽ tự làm: cá theo loài, bông/rau, khăn rằn, quầng sáng; hàm băm cố định thay cho số ngẫu nhiên |
| `js/core/widgets.js` | Khung, vòng tiến độ, icon nguyên liệu/món, bong bóng, gợi ý phím |
| `js/core/bench.js` | `/?bench=1[&warmup=3&duration=30]`: bỏ menu/intro, đứng yên, đo thời gian khung, `POST /bench` (TICKET-04) |
| `js/core/net.js` | `/state`, `/input` (trạng thái phím, `tap` pause/shop_done, `buy`), mock |
| `js/core/events.js` | Lọc sự kiện mới từ `snap.events` |
| `js/core/input.js` | Bàn phím → màn hình hoặc phím chơi |
| `js/core/camera.js`, `js/core/fx.js` | Camera bám người lặn; chữ nổi + rung theo sự kiện |
| `js/gather/scene.js`, `hud.js` | Cảnh lặn: trời hồng, nhà sàn, dừa nước, nước phù sa theo độ sâu, bến, Út Sen, cá, bông, Cá Sấu + HUD sáng |
| `js/quan/scene.js`, `hud.js` | Cảnh quán: nhà bè, đèn dây, bếp cà ràng có khói, bàn ghế nhựa, khách + kiên nhẫn + HUD tối |
| `js/shop/scene.js` | Shop nâng cấp (đọc `meta.upgrades`) |
| `js/shared/screens.js` | Menu, DayIntro, EveningIntro, DayResult, Tổng kết, Tạm dừng |
| `js/shared/overlay.js` | MOCK, mất kết nối, lỗi luật, nhật ký, thẻ hết buổi (chạy riêng) |
| `js/main.js` | Vòng vẽ: sự kiện → màn hình → cảnh theo `snap.phase` → HUD → fx → lớp phủ |
| `mock/*.json`, `assets/` | Snapshot giả theo Test Contract v1.1; sprite/âm thanh (ghi nguồn `CREDITS.md`) |

Thêm pha mới: tạo `js/<pha>/scene.js` đăng ký `CN.scenes[pha]` (+ `CN.hud[pha]`), thêm `<script>` vào `index.html`.

## Quy tắc
- Không đặt luật trong client. Gợi ý phím, "món nấu được", "chưa đủ tiền" chỉ là hiển thị; sim quyết định.
- Intro/kết quả gửi `pause` để đồng hồ đứng yên (`docs/clarify.md` #3).
- Đổi tên trường snapshot/sự kiện: sửa `docs/contracts/` trước, rồi mock và renderer.
- Chữ người chơi đọc ≥ 18 px ở 1280×720 (yêu cầu Ticket-02).
