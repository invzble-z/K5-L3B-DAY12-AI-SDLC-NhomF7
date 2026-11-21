# Ma trận truy vết Phase 3 — Q3/Quoosc

Main hiện dùng contract v1.3. Q3 đã thêm kiểm tra inventory/scenario vật lý theo contract root, ID và freshness được giữ qua gather → inventory file → quan, và kho được bàn giao qua Day. Kết quả tích hợp ở [v1.3 tests](../proof/phase-4/q3-focused-tests.txt), [headless Day](../proof/phase-4/day-headless-run.txt), và [full regression](../proof/phase-4/q3-full-regression.txt).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả trên Quoosc |
|---|---|---|---|
| AC-P3-01 | Inventory parse/validate v1.2/v1.3 và legacy v1.1 | `tests.test_p3_inventory`, `tests.test_p3_v13_integration` | Đạt; mặc định root v1.3 dùng physical Item list; v1.1 tương thích khi chỉ định rõ |
| AC-P3-02 | Freshness Gather/Quan, pause Day | `tests.test_p3_gather`, `tests.test_p3_q3_freshness`, `test_day_pause_freezes_physical_freshness_and_ticks` | Đạt trong simulation tests; UI v1.3 chưa được chụp/review riêng |
| AC-P3-03 | Threshold crossing và event `spoiled` một lần theo ID | `tests.test_p3_gather`, `tests.test_p3_q3_freshness` | Đạt theo test |
| AC-P3-04 | Freshest-first, ID tie, atomic reservation, retry, idempotency | `tests.test_p3_q3_freshness` | Hành vi kỹ thuật đạt; event schema `unfulfillable` còn chờ PO/Integrator ở clarify #16 |
| AC-P3-05 | Giá theo freshness và tip | [`quan-price-test.txt`](../proof/phase-3/quan-price-test.txt) | Đạt; thứ tự decay trước interaction được phản ánh trong oracle |
| AC-P3-06 | Monster hit/faint, mất item LIFO theo Item | `tests.test_p2_monsters.MonsterBehaviorTest`, full suite | Đạt; test kiểm tra kind/order; inventory vật lý giữ ID |
| AC-P3-07 | Headless gather → file kho → Quan đọc lại | `tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it`, `test_root_version_is_propagated_and_gather_to_file_to_quan_keeps_id_fresh` | Đạt; ID/freshness giữ qua file và mã thoát 0 |
| AC-P3-08 | Day handoff và allocator liên tục | `tests.test_p3_inventory.InventoryPhase3Tests.test_day_handoff_individual_items_and_id_continuity` | Đạt; vật phẩm còn lại chuyển đúng một lần và ID kế tiếp không đụng |
| AC-P3-09 | HUD live/mock v1.2 | [`hud-fresh/README.md`](../proof/phase-3/hud-fresh/README.md), [`hud-fresh/run.txt`](../proof/phase-3/hud-fresh/run.txt) | Bằng chứng UI v1.2 cũ vẫn áp dụng; chưa xác nhận HUD khi root manifest là v1.3 |
| AC-P3-10 | Full repository regression | [`q3-full-regression.txt`](../proof/phase-4/q3-full-regression.txt) | 216 tests, OK, exit 0; Phase 1 verifier 9/9 bước |

## Giới hạn nghiệm thu

- `unfulfillable` hiện phát `{customer_id, table_id, dish_id}` theo đề xuất, đơn vẫn waiting, reservation rỗng. Cần đóng clarify #16 trước khi gọi schema này là contract đã duyệt.
- Không sửa `game.contract.json` hay schema shared; implementation theo manifest v1.3 đã có trên main `dd090f6`.
- Chưa có xác nhận UI v1.3 hoặc review QA/Integrator cho toàn ma trận AC-P3.
