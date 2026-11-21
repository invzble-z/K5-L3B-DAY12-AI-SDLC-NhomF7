# Tasks Phase 2 Q3 — sau merge

- [x] T01 DONE — đối chiếu Git và baseline sau khi pull main mới.
- [x] T02 DONE — spec, contract proposal và test plan.
- [x] T03 DONE — customer scheduling, table, menu selection, reservation.
- [x] T04 DONE — menu_filter, order_tick và scenario validation.
- [x] T05 DONE — Q3 regression và headless.
- [x] T06 DONE — review Q4 và ghi finding Q4-F1.
- [x] T07 DONE — sửa DaySim/Runner empty plan, reputation carry-over và active sim_tick khi pause; kiểm tra handoff kho cá thể qua ngày. Headless Day 1/3 exit 0, replay deterministic; [proof](../../docs/proof/phase-4/day-headless-run.txt).
- [ ] T08 PARTIAL — Q4-F1 fix và integration regression đã có tại [test](../../tests/test_p2_q4_f1_reuse.py); chờ ttkien0710 review thay đổi module Q4.
- [x] T09a DONE — `no_dish {}` theo PO #11, gồm filter rỗng/kho thiếu/bàn đầy/no backlog.
- [x] T09b DONE kỹ thuật — xử lý `day_plan` map/list, plan rỗng và filter; đối chiếu ticket gốc/event-state vẫn cần Integrator khi có nguồn chuẩn.
- [ ] T10 PARTIAL — unit/integration/regression/proof mới đều chạy đạt; QA review chính thức chưa được ghi nhận.

Các mục kỹ thuật Q3 đã hoàn tất. T08 chờ review owner Q4; T10 chờ QA/Integrator review. T09a là mục con của T09 nên không cộng riêng vào tổng task. Không tính việc chờ review thành phê duyệt. Xem [verification](../../docs/verification/phase-2.md).
