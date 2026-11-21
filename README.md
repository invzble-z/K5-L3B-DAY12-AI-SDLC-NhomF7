# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

Trên macOS, Linux hoặc Ubuntu WSL, cần Git, Python 3.10 trở lên và trình duyệt. Bản chơi dùng thư viện chuẩn Python.

```bash
git clone https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7.git cho-noi
cd cho-noi
python3 -m chonoi.live --mode day
```

Mở địa chỉ in trên terminal. Dùng WASD hoặc phím mũi tên để di chuyển, E để tương tác, Space để bắt cá, Esc/P để tạm dừng và R để chơi lại.

Nếu dùng ZIP, giải nén rồi chạy lệnh cuối từ thư mục `cho-noi`. Trên Windows PowerShell, dùng `python` nếu `python3` là lối tắt Microsoft Store.

### Kiểm thử

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 23000 --out day.jsonl
```

Lệnh benchmark có render và soak 10 ngày sẽ được cập nhật khi các module Phase 4 được tích hợp vào bản phát hành.

Buổi tối có thể tự tìm `inventory.json` trong thư mục chạy lệnh; không bắt buộc truyền `--inventory`:

```powershell
python -m chonoi.live --mode quan --seed 1
```

Với `--mode day`, kho mặc định cũng được nạp tự động từ `inventory.json`, sau đó buổi sáng có thể cộng nguyên liệu mới vào kho.

### Chơi nối buổi sáng sang quán

```powershell
python -m chonoi.live --mode day --seed 1 --inventory-out inventory.json
```

Mode `day` tự thu thập cá/rau ở buổi sáng, chuyển kho sang buổi tối và cho Út Sen nấu/bán món trong cùng cửa sổ trình duyệt. Sau buổi tối, kho dùng cho quán là kho khả dụng sau phần nguyên liệu khách đang giữ chỗ.

Chạy headless một Ngày:

```powershell
python -m chonoi.headless --mode day --seed 1 --ticks 21600 --inventory-out inventory.json --out day.jsonl
```

### Lưu kho khi hái/bắt cá

Chạy giao diện Gather và ghi kho tức thì vào `inventory.json`:

```powershell
python3 -m chonoi.live --mode gather --inventory-out inventory.json
```

File được tạo sau lần hái/bắt cá đầu tiên, sau đó cập nhật ngay mỗi lần thu hoạch hoặc bắt cá, khi ngất và khi kết thúc buổi. Nếu file đã có kho từ lần chạy trước, số lượng được cộng dồn thay vì xóa. Dùng cùng file cho Quán:

```powershell
python3 -m chonoi.live --mode quan --inventory inventory.json
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.


## Sáng tạo của nhóm

**Đồ họa client web (P2, lát `p2/ui-visual`)** — chỉ ở `chonoi/web/`, tự vẽ bằng canvas, không dùng ảnh ngoài; luật, `game.contract.json`, schema kho và JSONL không đổi (headless giống từng byte, xem [`docs/proof/phase-2/ui-visual.md`](docs/proof/phase-2/ui-visual.md)).

- **Cảnh lặn buổi sáng** (mặt cắt ngang): trời hồng lúc mặt trời mọc, mây trôi, rặng cây xa, nhà sàn có đèn cửa sổ, ghe, dừa nước đung đưa; nước phù sa đậm dần theo độ sâu (nông / giữa / sâu), tia nắng xiên, hạt phù sa lơ lửng, đáy bùn có sỏi và rong.
- **Út Sen**: áo bà ba, khăn rằn bay theo nước, kính lặn, búi tóc, giỏ lưới đầy dần theo số món trong giỏ; đạp chân/sải tay khi bơi, nổi đứng khi ở mặt nước.
- **Loài**: cá linh bạc đi đàn (hai con nhỏ bơi kèm chỉ để trang trí), cá lóc thân dài có đốm, cá kèo mắt lồi; bông súng có lá và cuống dưới nước, cây điên điển ra chùm bông vàng, bó kèo nèo; nút chưa hồi chỉ còn lá/nụ kèm đồng hồ.
- **Bến**: cầu tàu, biển "Bến", ghe có mui, sọc sơn, mắt ghe và đèn treo. **Cá Sấu**: vảy gai lưng, chân chèo, há mõm khi đuổi; khi đến gần thì có viền tím, quầng tím và chữ "Thủy quái!" ngay trên con quái (HUD vẫn giữ viền màn hình tím).
- **Quán buổi tối** (nhìn từ trên): nhà bè có phao gỗ, sàn ván, góc bếp lát gạch tàu với quầy hũ mắm, thớt, rổ rau; đèn dây vàng nhấp nháy, đèn lồng đỏ bốn góc, biển "QUÁN ĂN CHỢ NỔI"; sông đêm có ánh trăng và hoa đăng trôi.
- **Bếp cà ràng** B1/B2: than hồng chập chờn, nồi đất có nước dùng sôi, khói bếp; **bàn** T1–T4: bàn gỗ, ghế nhựa đỏ, ống đũa, chén nước mắm, đèn dầu; **khách** áo nhiều màu, có người đội nón lá, bong bóng order có món và thanh kiên nhẫn (< 25% đỏ nhấp nháy); Út Sen quấn khăn rằn, quay theo hướng đi, bưng món còn bốc hơi.
- Mọi chi tiết "ngẫu nhiên" lấy từ hàm băm cố định `CN.art.hash` (`chonoi/web/js/core/art.js`), không dùng `Math.random` hay `Streams`; hiệu ứng chỉ chạy trên trình duyệt nên tự tắt ở headless.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
