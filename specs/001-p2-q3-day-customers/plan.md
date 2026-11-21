# Kế hoạch triển khai

`QuanSim` giữ menu gốc, `menu_filter` chỉ giới hạn ứng viên mới; `None` nghĩa là toàn menu và set rỗng không chọn món. Tuning quyết định bàn và lịch, dùng `sort_by_id`, Streams và reservation ledger. Q3 đã được kiểm thử trong DaySim thật bằng `tests/test_p2_q3_day_integration.py`; kết quả hiện xác nhận bàn giao kho, reservation, ngày mới và headless. Ba lỗi DaySim/Runner còn lại được ghi expected failure và bàn giao cho Integrator; không sửa file của chủ module ở nhánh này. Contract chỉ được cập nhật sau khi có nguồn Ticket-02 và PO/Integrator xác nhận.
