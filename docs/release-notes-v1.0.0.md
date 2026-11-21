# Quán Ăn Chợ Nổi — Bản Phát Hành v1.0.0

Phiên bản phát hành chính thức đánh dấu việc hoàn thành toàn diện 4 giai đoạn phát triển theo quy trình AI-SDLC của nhóm **NhomF7**.

---

## 1. Giới thiệu tổng quan
**Quán Ăn Chợ Nổi** là tựa game mô phỏng 2D lấy bối cảnh sông nước miền Tây Nam Bộ:
- **Buổi sáng (Lặn & Thu hoạch):** Điều khiển nhân vật Út Sen bơi lặn bắt cá và thu hoạch rau muống, bông súng, né tránh thủy quái và quản lý lượng dưỡng khí (oxy).
- **Buổi tối (Quán ăn nổi):** Chế biến các món ăn đặc sản miền Tây (Cá tai tượng chiên xù, Cá lóc nướng trui, Canh chua bông súng...) để phục vụ thực khách cập thuyền đến quán, quản lý độ kiên nhẫn và tích lũy doanh thu / độ uy tín.
- **Vòng lặp Ngày liên tục (DaySim):** Kết nối liên tục qua nhiều ngày, bảo toàn kho nguyên liệu và mở rộng quy mô quán.

---

## 2. Các tính năng nổi bật qua 4 Phase

### Phase 1: Nền tảng cốt lõi
- Hệ thống vật lý bơi lặn mượt mà với gia tốc ramp mượt.
- Cơ chế thu hoạch mặt nước và lặn bắt cá theo độ sâu.
- Logic quán ăn cơ bản: nhận món, nấu nướng, phục vụ và thanh toán.
- Hệ thống kho nguyên liệu hợp đồng `game.contract.json` (v1.0).

### Phase 2: Mở rộng cơ chế & Giao diện Trực tiếp
- Cơ chế bơi đàn của cá, kích thước và giá trị khác nhau.
- Menu đa dạng với các công thức nấu ăn nhiều nguyên liệu.
- Cơ chế khách đến ngẫu nhiên nhưng tất định theo luồng `Streams`.
- Giao diện trực tiếp trên nền web qua thư viện chuẩn Python (HTTP Server & HTML5 Canvas), không phụ thuộc thư viện đồ họa ngoài.

### Phase 3: Độ tươi & Quản lý Kho cá thể
- Cơ chế độ tươi (Freshness): nguyên liệu trong giỏ giảm dần phẩm chất theo thời gian.
- Hệ thống kho cá thể (item-based inventory) lưu trữ từng cá thể với timestamp và độ tươi riêng biệt.
- Quán Q3 nâng cao: giữ chỗ bàn theo ID khách hàng, ưu tiên phục vụ nguyên liệu tươi nhất.

### Phase 4: Ổn định hóa, Đo kiểm & Trợ năng
- **Contract v1.3:** Tích hợp `bench_cmd` và `soak_cmd`.
- **Soak Testing (`chonoi.soak`):** Mô phỏng xuyên suốt 10 ngày đêm liên tục (`--days 10 --seed 7`), đạt 0 crash và tính tất định tuyệt đối qua 2 lần chạy.
- **Benchmark Hiệu năng Render (`chonoi.bench`):** Tự động đo 30 giây với headless Chromium, đạt xấp xỉ ~47 FPS trung bình và ~30 FPS ở 1% low.
- **Trợ năng & Trải nghiệm (Accessibility):**
  - Chế độ **Độ tương phản cao** (High Contrast Mode) thân thiện với người khiếm thị màu.
  - Bộ 3 cảnh báo trực quan bằng biểu tượng và chữ rõ ràng: *Thủy quái đến gần*, *Dưỡng khí sắp cạn*, *Khách sắp mất kiên nhẫn*.

---

## 3. Khởi động nhanh (Quick Start trong 3 lệnh)

Chỉ yêu cầu Python 3.10 trở lên và Git:

```bash
# 1. Clone mã nguồn
git clone https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7.git cho-noi

# 2. Di chuyển vào thư mục dự án
cd cho-noi

# 3. Khởi chạy chế độ chơi cả Ngày trên trình duyệt
python3 -m chonoi.live --mode day
```
*(Trên Windows PowerShell, sử dụng lệnh `python -m chonoi.live --mode day`)*

### Các phím điều khiển
- **WASD / Phím mũi tên:** Di chuyển nhân vật.
- **Space:** Lặn / Bắt cá / Nhặt nguyên liệu.
- **E:** Tương tác tại bếp / Phục vụ khách / Cập bến.
- **Esc / P:** Tạm dừng game.
- **R:** Chơi lại từ đầu.

---

## 4. Kết quả kiểm thử & Bằng chứng nghiệm thu
- **Bộ Unit Tests:** 207/207 tests đạt (100% passed, 5 expected failures theo spec ban đầu).
- **DaySim 10-Day Soak:** Hoàn thành 10/10 ngày, 0 crash (`docs/proof/phase-4/soak.json`).
- **Render Benchmark:** 1408 frames / 30s (~46.92 FPS), không giật lag (`docs/proof/phase-4/bench.json`).
- **Truy vết chất lượng:** Chi tiết tại `docs/verification/phase-4.md`.

---

## 5. Nhóm phát triển (NhomF7)
- Nguyễn Khắc Bào (`invzble-z`) — Integrator / Release Lead
- Trịnh Tiến Kiên (`ttkien0710`) — Benchmark / Dev Lead
- Dương Thái Ngân (`nganhduong123`) — UI Client / Accessibility Lead
- Nguyễn Quốc (`Quoosc`) — DaySim / Soak Lead
- Nguyễn Văn Tú (`comtrang378-ship-it`) — Logic / Sim Lead
- Nguyễn Quang Dũng (`NguyenQuangDunghe161764`) — Test & Contract Review
- Nguyễn Đức Minh (`WorkOfMinh`) — Quality Assurance / Verification Lead
