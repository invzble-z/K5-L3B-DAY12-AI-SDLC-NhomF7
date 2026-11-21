# invzble-z — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Vai trò Integrator / Release Lead: quản lý `game.contract.json`, điều phối merge PR.
  - Phase 2: Cập nhật Contract v1.1, lập trình Lát 4a (`sim/day.py`, chế độ `--mode day`, đổi pha Gather->Quán->Shop, bàn giao kho, pause/resume), gắn tag `phase-2`.
  - Phase 3: AC-P3-01 & AC-P3-08 (`Item`, adapter 2 schema kho, khối `freshness`, bàn giao cá thể và `IdAllocator` xuyên Ngày trong `day.py`, `tests/test_p3_inventory.py`).
  - Phase 4: AC-P4-01 (Contract v1.3, khai `bench_cmd`, `soak_cmd`, `tests/test_p4_contract.py`), điều phối release.
- Tôi đã review:
  - Review và merge PR #3, PR #4, PR #12, PR #13, PR #14, PR #15 và nhánh của các thành viên.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Khi viết `DaySim`, AI import `from .sim.gather` gây lỗi `ModuleNotFoundError`; khi làm v1.3 adapter, AI định áp dụng cứng kho cá thể làm gãy test v1.1 cũ. Phát hiện nhờ chạy `unittest discover` và sửa điều kiện linh hoạt.
- Điều tôi học được:
  - Lock contract và adapter tương thích ngược là chìa khóa để 7 người phát triển song song mà không vỡ nhánh chính.
