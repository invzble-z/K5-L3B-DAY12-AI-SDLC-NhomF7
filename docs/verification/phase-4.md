# Ma trận truy vết Phase 4

| AC | Nội dung | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-4/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) | Người |
|---|---|---|---|---|---|
| AC-P4-01 | `contract_version:"1.3"`, khai đúng `bench_cmd`, `soak_cmd` | `game.contract.json` + unit tests `tests/test_p4_contract.py` | `game.contract.json`, `tests/test_p4_contract.py` | đạt | invzble-z |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` chạy cảnh chuẩn, đủ 5 trường đúng công thức | Chạy đo 30s thực tế trên trình duyệt headless Chrome và unit tests `tests/test_p4_bench.py` | [`bench.json`](docs/proof/phase-4/bench.json) | đạt | ttkien0710, nganhduong123 |
| AC-P4-03 | `soak_cmd --seed 7 --days 10`: `days_completed = 10`, `crashes = 0`, chạy lặp giống nhau ở trường gameplay | log soak `tests/test_p4_soak.py`, chạy thực tế `chonoi/soak.py` | [`soak.json`](docs/proof/phase-4/soak.json), [`soak-run.txt`](docs/proof/phase-4/soak-run.txt) | đạt | Quoosc |
| AC-P4-04 | 3 cảnh báo có chữ hoặc biểu tượng, chế độ tương phản cao hoạt động | ảnh chụp CDP và unit tests `tests/test_p4_ui_bench_contrast.py` | [`ui-client/`](docs/proof/phase-4/ui-client/) | đạt | nganhduong123, comtrang378-ship-it |
| AC-P4-05 | Clone sạch chạy bản giao diện trong ≤ 3 lệnh, README đủ thông tin | `clean-clone.txt` | [`clean-clone.txt`](docs/proof/phase-4/clean-clone.txt) | đạt | NguyenQuangDunghe161764 |
| AC-P4-06 | Regression P1–P3 còn hiệu lực đạt | log test toàn bộ 184+ tests | [`verify-run.txt`](docs/proof/phase-4/verify-run.txt) | đạt (207/207 OK) | WorkOfMinh |
| AC-P4-07 | CHANGELOG theo phase, release notes, zip, tag `phase-4` và Release v1.0.0 cùng commit | GitHub Release v1.0.0 | [`release-notes-v1.0.0.md`](docs/release-notes-v1.0.0.md) | đạt | invzble-z |
| AC-P4-08 | Retro rà hành động P2, đủ 7 phản tư cá nhân | `docs/retro.md`, `docs/members/` | [`docs/retro.md`](docs/retro.md) | đạt | nganhduong123, cả nhóm |

## Đánh giá ngắn
- **Yêu cầu AC-P4-01 (invzble-z phụ trách):**
  - Cập nhật [game.contract.json](game.contract.json) lên `contract_version: "1.3"`.
  - Khai báo 2 lệnh chính thức: `"bench_cmd": "python3 -m chonoi.bench"` và `"soak_cmd": "python3 -m chonoi.soak"`.
  - Bổ sung hàm `validate_contract(c)` trong [chonoi/contract.py](chonoi/contract.py) kiểm tra bắt buộc phải có `bench_cmd` và `soak_cmd` khi version là 1.3.
  - Cập nhật adapter kho [chonoi/inventory.py](chonoi/inventory.py) nhận diện phiên bản 1.3 và giữ tính tương thích ngược với kho đếm và kho cá thể.
  - Viết bộ unit test [tests/test_p4_contract.py](tests/test_p4_contract.py) kiểm tra cấu hình và bắt lỗi thiếu lệnh: **2/2 tests đạt**.
- **Yêu cầu AC-P4-02 (ttkien0710 phụ trách):**
  - Cài đặt `chonoi/bench.py` cung cấp lệnh benchmark render theo Contract v1.3.
  - Tự động mở Chromium headless (Chrome/Edge), kết nối `?bench=1` và thu thập `frame_ms` qua POST `/bench`.
  - Tính toán đủ 5 chỉ số: `avg_fps: 46.92`, `p1_low_fps: 29.79`, `frames: 1408`, `duration_s: 30`, `warmup_s: 3`.
  - Viết bộ unit test [tests/test_p4_bench.py](tests/test_p4_bench.py): **4/4 tests đạt**.
- **Yêu cầu AC-P4-03 (Quoosc phụ trách):**
  - Cài đặt `chonoi/soak.py` chạy qua `DaySim`, bắt lỗi theo ngày và ghi `soak.json`.
  - Đạt 10/10 ngày, 0 crash, exit 0; gameplay fields trùng khớp 2 lần chạy độc lập cùng seed 7.
- **Yêu cầu AC-P4-04 (nganhduong123 & comtrang378-ship-it phụ trách):**
  - Đã tích hợp 3 cảnh báo có chữ và icon (Thủy quái gần, Oxy sắp hết, Khách sắp giận) và công tắc Độ tương phản cao (High Contrast). Đã kiểm thử qua [tests/test_p4_ui_bench_contrast.py](tests/test_p4_ui_bench_contrast.py) và chụp ảnh CDP tại `docs/proof/phase-4/ui-client/`.
- **Yêu cầu AC-P4-05 & AC-P4-06 (NguyenQuangDunghe161764 & WorkOfMinh phụ trách):**
  - Kiểm thử clone sạch 3 lệnh thành công: [`docs/proof/phase-4/clean-clone.txt`](docs/proof/phase-4/clean-clone.txt).
  - Kiểm thử hồi quy toàn bộ: 207/207 unit tests đạt (5 expected failures theo spec): [`docs/proof/phase-4/verify-run.txt`](docs/proof/phase-4/verify-run.txt).
- **Yêu cầu AC-P4-07 (invzble-z phụ trách):**
  - Bổ sung `LICENSE` tại gốc repo.
  - Soạn thảo Release Notes toàn diện: [`docs/release-notes-v1.0.0.md`](docs/release-notes-v1.0.0.md).
  - Đóng gói ZIP `cho-noi-v1.0.0.zip`, gắn tag `phase-4` và tạo GitHub Release v1.0.0.

## Cập nhật proof Q3 của Quoosc trên nhánh hiện tại

- Soak mới nhất: [run 1](../proof/phase-4/soak-q3-run1.json), [run 2](../proof/phase-4/soak-q3-run2.json); cả hai seed 7 đạt 10/10 ngày, 0 crash, gameplay fields trùng. `earned=0` là kết quả bot fast-dock không thu hoạch.
- Hồi quy hiện tại: 216 tests OK, exit 0; [full log](../proof/phase-4/q3-full-regression.txt). Phase 1 verifier đạt 9/9 bước: [verify-run](../proof/phase-1/verify-run.txt).
- DaySim headless Day 1 và 3: exit 0; Day 3 replay byte-identical: [log](../proof/phase-4/day-headless-run.txt).
- AC-P4-03 có bằng chứng kỹ thuật mới; QA/Integrator review vẫn cần ghi nhận riêng.
