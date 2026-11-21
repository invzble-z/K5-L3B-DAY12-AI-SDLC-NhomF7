# Phase 2 — phần khách của Quoosc

Main `63f850e`, PR #8 merge `9f60259`: QuanSim nhận menu_filter (None: toàn menu, rỗng: không món, ID lạ: BadInput), order_tick và ledger giữ/tiêu/nhả. Manifest v1.1 có sáu món, hai bếp, bốn bàn. Q3/Q4 đã ghép; [proof sau merge](q3/postmerge-baseline-63f850e.txt): Q3 P1 23, Q3 P2 12, Q4 7, regression 108, 9/9 bước, exit 0.

DaySim chưa có; mode day trả 2. Q4-F1 vẫn tái hiện; chính sách chờ Kiên và PO. Hợp đồng tích hợp là đề xuất chờ duyệt; day_plan và event còn lệch. Chi tiết: [handoff](../../../specs/001-p2-q3-day-customers/handoff.md). QA và phản tư cá nhân chưa được xác nhận. Các log cũ và patch worktree là lịch sử tại [Q3 proof](q3/README.md).
