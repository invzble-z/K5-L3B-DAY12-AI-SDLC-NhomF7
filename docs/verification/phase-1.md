# Ma trận truy vết Phase 1

Kiểm chứng mới nhất được thực hiện sau khi đồng bộ main `dd090f6` vào Quoosc. Bộ xác minh Phase 1 đạt 9/9 bước; full suite có 216 tests, không fail/error/expected failure. Log mới nhất: [verify-run.txt](../proof/phase-1/verify-run.txt).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| G1: oxy, ngạt, máu, ngất | Unit test oxy cạn, choke, faint | `tests.test_p1_logic.GatherLogic` + full suite | Đạt |
| G2: hái, bắt cá, giỏ LIFO | Test hái/bắt, hold_full, regrow | `tests.test_p1_logic.GatherLogic`, `tests.test_p1_g2` | Đạt; kho vật lý theo contract 1.3 |
| G2: kho, cập bến, cộng dồn | Headless gather → inventory → quan; legacy v1.1 có test riêng | `tests.test_smoke_p1.Integration`, `tests.test_live.LiveInventoryPersistenceTest` | Đạt |
| Q3: khách, giữ chỗ, kiên nhẫn, ID/lịch | Fixtures, reservation, patience, replay, validation | [`Q3 proof`](../proof/phase-1/q3/README.md), `tests.test_p1_q3` | Logic và validator đạt theo các quyết định PO được ghi; một số đối chiếu ticket gốc còn provisional |
| Contract D: `hand: null` | Scenario v1.3 chấp nhận tay rỗng; kiểm tra ID reservation duy nhất | `tests.test_p3_v13_integration.ContractV13InventoryTests.test_v13_scenario_checks_unique_reservation_ids_and_accepts_null_hand` | Đạt |
| Contract D: assigned thiếu món / mâu thuẫn state | Không tự suy diễn semantics nghiệp vụ ngoài contract | `tests.test_p1_q3` và `docs/clarify.md` | Chưa xác nhận; cần PO chốt nguồn chuẩn |
| Headless | Replay, sample inventory, input sai exit 2/không ghi file | [`verify-run.txt`](../proof/phase-1/verify-run.txt) | Đạt, 9/9 bước, exit 0 |
| HUD hoàn chỉnh | Live UI review | Phase UI proofs | Phase 1 chỉ xác nhận HUD đọc snapshot; không tuyên bố review UI mới |

## Đánh giá

- Full suite sau cập nhật: 216 tests, tất cả pass, không còn expected failures; [log](../proof/phase-4/q3-full-regression.txt).
- Root contract v1.3 được chuyển vào tuning; file inventory count bị từ chối theo schema v1.3. Test legacy chỉ dùng version 1.1 tường minh.
- `inventory.json` cục bộ được bảo toàn nguyên byte trong lúc kiểm thử; đây là dữ liệu người dùng, không nằm trong diff.
- Ticket PRD-0/Test Contract gốc không có trong checkout. Kết quả kỹ thuật không thay cho xác nhận PO/giảng viên các semantics chưa có nguồn chuẩn.
