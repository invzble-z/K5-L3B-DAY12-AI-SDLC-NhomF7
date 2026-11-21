# Bàn giao Q3 Phase 2 sau merge

Main mới nhất kiểm tra `ba17f4d`; verification trên merge HEAD `5b79199` gồm PR #6, #8, #10, #11, #12 và cập nhật Gather/Phase 3 mới. Test commit mới nhất `053867b`. PR merge không chứng minh QA phê duyệt. GitHub Issues đang tắt; các việc cần người khác quyết định phải được chuyển qua kênh nhóm.

- **Kiên (`ttkien0710`) + Dương (PO): Q4-F1.** Fixture `test_q4_f1_orphan_dish_reproduced`: C1 ở T1, một nguyên liệu cá lóc, patience 2; bắt đầu nấu, khách rời, món ready và nhấc được dù khách đã rời. Actual: món mồ côi. Chính sách hủy/giữ/tái sử dụng cần được chốt trước khi thêm regression sửa lỗi.
- **Bào (`invzble-z`):** xử lý các lỗi đã có test tại `tests/test_p2_q3_day_integration.py`: `_init_quan` biến `dishes={}` thành `menu_filter=None`; truyền `DaySim.reputation` vào `QuanSim` và giữ uy tín qua ngày; sửa hợp đồng `sim_tick` khi pause ở Runner. Sau đó chạy lại test tích hợp/headless và duyệt hợp đồng đề xuất.
- **Dương (`nganhduong123`):** chốt no_dish, bàn đầy/hết món, patience khi nấu, event customer_id/order_id, state, kế hoạch và Q4-F1; xác nhận ticket gốc.
- **Minh (`WorkOfMinh`):** review QA trên commit tích hợp sau khi Bào xử lý ba expected failures; rà Q3 P1/P2, Q4, Day, determinism và AC còn mở. Kết quả hiện tại ở [integration proof](../../docs/proof/phase-2/q3/day-regression-5b79199.txt); chưa có review submission.
- **Quốc (`Quoosc`):** xác nhận phản tư cá nhân T10 sau khi nghiệm thu xong.

Chi tiết và người xử lý: [bảng lệch](contracts/q3-q4-day.md). Quốc xác nhận phản tư cá nhân sau khi hoàn tất nghiệm thu.
