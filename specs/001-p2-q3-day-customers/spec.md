> Trạng thái kiểm chứng trên main `ba17f4d` (verification branch HEAD `5b79199`): Q3/Q4 và DaySim đã có; integration test mới phát hiện ba lỗi DaySim/Runner cần Bào xử lý. Contract và QA vẫn mở. Xem [research](research.md), [handoff](handoff.md). Nội dung dưới mô tả yêu cầu Q3.

# Phase 2 Q3 — khách và kế hoạch ngày

Nguồn: `docs/plan/phase-2.md`, `docs/plan/phan-chia-cong-viec.md` và yêu cầu người dùng. Ticket-02 gốc/Test Contract v1.1 không có trong checkout và GitHub issue search không tìm thấy; kế hoạch nhóm là nguồn thứ cấp.

DaySim hiện được kiểm thử bằng [integration suite](../../tests/test_p2_q3_day_integration.py); kết quả và giới hạn tại [proof](../../docs/proof/phase-2/q3/day-findings.md). Test mô tả lỗi qua expected failure, không coi là AC đạt.

- US1: khách đến theo first tick và interval từ tuning, bàn trống có ID nhỏ nhất; không có bàn hoặc món nấu được thì bỏ cơ hội, không xếp hàng (chính sách tạm thời).
- US2: Quán độc lập xét toàn menu; Day truyền `menu_filter`; xét filter trước nguyên liệu, sort ổn định và chọn bằng Streams, giữ cả recipe nguyên khối.
- US3: giữ và tiêu thụ đúng một lần, nhả khi khách rời; bàn giải phóng khi rời hoặc thanh toán. Khách mới có `order_tick` là tick đến, fixture mặc định 0.
- US4: cung cấp snapshot khách và interface Q4/Day. PO #11 chốt: lượt đến hạn có bàn trống nhưng không có món hợp lệ phát `no_dish {}` một lần, không tạo khách, không kết thúc ca và không dồn lượt; bàn đầy thì bỏ lượt im lặng. Chính sách món mồ côi Q4-F1 vẫn cần review module.

AC nội bộ: bốn bàn không trùng; lịch 120/1020/1920 với tuning thử; sáu món thử được chọn khi đủ nguyên liệu; filter rỗng không sinh; cùng seed tái lập; reservation không vượt kho. Chưa ánh xạ AC chính thức.
