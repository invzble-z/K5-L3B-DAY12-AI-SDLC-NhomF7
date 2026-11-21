# Bằng chứng Phase 2 Q3

## Tích hợp Day mới nhất

Main mới nhất `ba17f4d`; verification HEAD `5b79199` trên branch `p2/q3-day-integration`:

- [Day integration](day-integration-5b79199.txt): 15 test, 10 đạt, 5 expected failures cho filter rỗng, reputation qua ngày và `sim_tick` khi pause.
- [Headless Day](day-headless-5b79199.txt): Day 1 và Day 3 kết thúc đúng; Day 3 replay cùng seed/input cho cùng SHA-256.
- [Regression](day-regression-5b79199.txt): Day 6/6, Q3/Q4 19/19, Phase 2 fish + Phase 3 14/14, tổng 143 test (5 expected failures), Phase 1 verification 9/9.
- [Findings và bàn giao](day-findings.md): T07 PARTIAL; T08–T10 còn phụ thuộc policy, Integrator, QA và xác nhận cá nhân.

Không có sửa logic runtime trong commit này; test ghi lại hai lỗi DaySim và một lỗi Runner thuộc chủ module Bào. Q4-F1 tiếp tục tái hiện, chưa có quyết định xử lý.

## Kiểm chứng sau merge

Main `63f850e`, manifest v1.1: [log baseline](postmerge-baseline-63f850e.txt) và [log sau cập nhật](postmerge-final-63f850e.txt). Q3 P1 23, Q3 P2 12, Q4 7, regression 108 và 9/9 bước đạt; Day trả 2; Q4-F1 vẫn tái hiện. Q3/Q4 đã ghép; hợp đồng PR #10 chờ Integrator duyệt.

## Lịch sử trước merge (giữ theo thời điểm)

Trên `3ce5cc6` cùng working tree Q3, Python 3.11 Windows, script verification dùng shim Python ngoài repo. `p2-tests.txt`: 10 test, exit 0; `p1-q3-tests.txt`: 23 test, exit 0; `regression-headless.txt`: 98 test, exit 0, 9/9 bước gồm hai lần headless gather/quán cùng seed so byte, nạp kho và đầu vào sai. Các test Phase 2 sử dụng [tuning giả lập](../../../../tests/fixtures/p2/q3/tuning.json), không phải contract chính thức.

Headless `quan` ở đây dùng contract v1.0. Chưa chạy được headless `day` hoặc headless bằng contract v1.1 chính thức do chưa có DaySim/v1.1. Hai bếp trên code hiện tại không dùng lại reservation; test Q4-F1 tái hiện món mồ côi, không biểu thị lỗi đã sửa. Nhánh Q4 `8b3b93f` cần tích hợp/retest thực tế; xem `specs/001-p2-q3-day-customers/contracts/q3-q4-day.md`.

Lệnh tái hiện: `python -m unittest tests.test_p2_q3 tests.test_p2_quoc -v`; `python -m unittest tests.test_p1_q3 -v`; `python .agents/skills/phase-1-verification/scripts/verify_phase1.py --no-proof`.

Kiểm lại trên base `d2daf42` với hai test mới: 12 test P2, 23 test P1 Q3 và 100 regression, exit 0; 9/9 bước headless/invalid/determinism đạt. Các log `current-*` ghi kết quả. Q4 base `5dbdf13` được kiểm riêng: 2/17 test không đạt (filter rỗng, order_tick âm); patch đề xuất tại `q4-5dbdf13-proposed.patch` cho 19/19 đạt, trong đó test Q4-F1 chứng minh lỗi vẫn tái hiện. Đây là kiểm thử worktree tách biệt, chưa phải nhánh tích hợp.
