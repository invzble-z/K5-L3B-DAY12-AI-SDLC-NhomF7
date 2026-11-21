# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Q-P2-01: 2 Bếp nấu độc lập song song | Test 2 bếp B1, B2 nấu đồng thời, bắn `dish_ready` đúng tick | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-02: Ưu tiên nhận đơn theo order_tick cũ nhất | Test bếp trống tự động chọn đơn của khách có `order_tick` nhỏ nhất (nếu bằng thì `table_id` nhỏ hơn) | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-03: Ưu tiên tương tác gần nhất | Test phím E chọn đối tượng gần nhất; cùng khoảng cách ưu tiên Bếp trước Bàn $\rightarrow$ id | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-04: Menu 6 món Phase 2 | Test đọc menu động 6 món (kể cả món phức tạp `lau_mam`), nấu, bưng và phục vụ | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-05: Đóng ca dọn món | Test khi hết giờ ca (`quan_end`), dọn sạch món đang nấu/chín trên bếp và món trên tay | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-EXT: Mở rộng `burn` (Cháy món) | Test khi bật `burn_s: 20`, đĩa chín quá 1200 ticks chuyển sang `burned` (`dish_burned`), dọn bếp bằng phím tương tác | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| QA: Kho nguyên liệu Phase 2 | Chạy `quan --inventory --ticks 0` với từng loại `ca_keo` và `keo_neo` trên `8216a95` | [Log kiểm tra kho](../proof/phase-2/inventory-new-items-8216a95.txt) | chưa đạt. Cả hai trả mã `2` vì bị báo là nguyên liệu lạ. |
| QA: Xác minh trên tag `phase-2` | Chạy regression, kiểm tra kho `ca_keo` và `keo_neo` ở tick 0, chạy smoke D1/D3 trên `ba17f4d` | [Log xác minh Phase 2](../proof/phase-2/qa-phase-2-ba17f4d.txt) | đạt. 128/128 test, kho có mỗi loại 1, D1/D3 hoàn thành đủ số ngày. |
| QA: Khởi tạo `earned` từ day scenario | Khai báo `money=200`, `earned=200`, rồi mua oxy và đóng Shop trên `ba17f4d` | [Log kiểm tra earned](../proof/phase-2/earned-initialization-ba17f4d.txt) | chưa đạt. `earned=0` ngay từ tick 0, trước giao dịch. Mua oxy và hoàn tất D1 vẫn đạt. |

## Đánh giá ngắn
- **Yêu cầu đạt:**
  - Quán hỗ trợ linh hoạt 2 bếp và 4 bàn, điều phối đơn thông minh theo thứ tự thời gian đặt và ưu tiên khoảng cách.
  - Tương thích hoàn toàn menu 6 món và cấu trúc mở rộng của Phase 2.
  - Hoàn thành tính năng mở rộng `burn` (Cháy món) ngay trong module Quán mà không ảnh hưởng tới core engine.
