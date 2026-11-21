# Kiểm chứng Phase 2 — phần Q3

Kiểm tra nhánh Quoosc sau khi pull/merge main `dd090f6` vào `0de1da6`. Các defect kỹ thuật Q3 DaySim/Runner đã được sửa và có test regression. Kết quả cuối: [focused tests](../proof/phase-4/q3-focused-tests.txt), [full regression](../proof/phase-4/q3-full-regression.txt), [headless Day 1/3](../proof/phase-4/day-headless-run.txt).

| Phạm vi | Kiểm chứng | Kết quả |
|---|---|---|
| DaySim → QuanSim, inventory, reservation/release/consume | `tests.test_p2_q3_day_integration`, `tests.test_p3_inventory` | Đạt; kho cá thể và ID được bàn giao qua ngày |
| `day_plan` filter, gồm map/list và kế hoạch rỗng | `test_empty_day_plan_is_an_empty_quan_filter`, `test_empty_day_plan_does_not_spawn_customer_for_unplanned_dish` | Đạt; `{}` giữ filter rỗng, không mở toàn menu |
| Reputation đầu ca và qua ngày | `test_day_level_reputation_is_passed_into_first_quan_shift`, `test_reputation_earned_in_quan_survives_into_next_day` | Đạt; tôn trọng override của fixture |
| Pause và đồng hồ | `test_sim_tick_stays_still_while_paused` | Đạt; outer tick tiếp tục, active sim/phase tick và timer dừng |
| Q4-F1 orphan dish | [`test_p2_q4_f1_reuse.py`](../../tests/test_p2_q4_f1_reuse.py) | Tái sử dụng món đúng dish_id; reservation của khách nhận được giải phóng; test kiểm tra kho, payment một lần và state eating |
| `no_dish` theo PO #11 | `tests.test_p2_q3_no_dish` | Đạt: đúng lượt, không backlog/ID mới, ca tiếp tục |
| Headless Day 1 và Day 3 | [`day-headless-run.txt`](../proof/phase-4/day-headless-run.txt) | Cả hai exit 0; replay Day 3 deterministic |
| Regression toàn repo | [`q3-full-regression.txt`](../proof/phase-4/q3-full-regression.txt) | 216 tests, OK, exit 0 |

## Bằng chứng QA trên các mốc Phase 2

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| QA: Kho nguyên liệu Phase 2 | Chạy `quan --inventory --ticks 0` với `ca_keo` và `keo_neo` trên `8216a95` | [Log kiểm tra kho](../proof/phase-2/inventory-new-items-8216a95.txt) | Chưa đạt tại `8216a95`. Cả hai trả mã `2` vì bị báo là nguyên liệu lạ. |
| QA: Xác minh trên tag `phase-2` | Chạy regression, kiểm tra kho ở tick 0 và chạy smoke D1/D3 trên `ba17f4d` | [Log xác minh Phase 2](../proof/phase-2/qa-phase-2-ba17f4d.txt) | Đạt trên tag. 128/128 test, kho nhận mỗi loại `1`, D1/D3 hoàn thành đủ số ngày. |
| QA: Khởi tạo `earned` từ day scenario | Khai báo `money=200`, `earned=200`, rồi mua oxy và đóng Shop trên `ba17f4d` | [Log kiểm tra earned](../proof/phase-2/earned-initialization-ba17f4d.txt) | Chưa đạt trên tag. `earned=0` ngay từ tick 0, trước giao dịch. Mua oxy và hoàn tất D1 vẫn đạt. |

## Trạng thái phần việc

- Kỹ thuật T07, T09a và tích hợp manifest Day: hoàn thành theo tests/headless hiện có.
- Q4-F1 đã có implementation fix và integration test. Cần ttkien0710 review thay đổi trong `chonoi/sim/quan.py` trước khi ghi nhận module review.
- Đề xuất schema/event `unfulfillable` vẫn cần Integrator/PO duyệt theo `docs/clarify.md` #16; không tính là contract được nghiệm thu.
- QA review chính thức T10 và các câu hỏi về nguồn ticket/schema ở `docs/clarify.md` vẫn chưa được ghi nhận. Tác vụ kỹ thuật có thể hoàn thành độc lập, nhưng không tự ghi nhận phê duyệt.
