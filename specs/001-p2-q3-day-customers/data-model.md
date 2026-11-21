# Dữ liệu

Khách: `id`, `table_id`, `dish_id`, `state`, `order_tick`, `patience_ticks_left`, `eat_ticks_left`, `reserved`. `order_tick` mới là elapsed tick; fixture thiếu dùng 0, giá trị phải là số nguyên không âm. Danh sách bàn từ tuning, sort numeric ID. Kho vật lý trừ tổng reservation để xác định khả dụng. Bộ lọc là tập/list/tuple hoặc keys mapping món hợp lệ; không sửa menu gốc.
