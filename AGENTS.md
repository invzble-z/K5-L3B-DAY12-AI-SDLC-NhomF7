# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Phase 2, lát cá: `python -m unittest tests.test_p2_fish -v`
- Phase 3, giỏ và độ tươi: `python -m unittest tests.test_p3_gather -v`
- Phase 3, quán Q3 giữ chỗ theo ID: `python -m unittest tests.test_p3_q3_freshness -v`
- Phase 4, soak DaySim: `python -m unittest tests.test_p4_soak -v`; chạy thật: `python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan|day` (mở địa chỉ in ra; WASD, E, Space, Esc tạm dừng, R chơi lại; `day` mặc định 5 Ngày, `--days N`)
- Phase 3–4 phía client: `python -m unittest tests.test_p3_hud_fresh tests.test_p4_ui_bench_contrast -v`. Bench client: mở `/?bench=1` trên `chonoi.live --mode gather --seed 42`
- Phase 2, lát 4b (bản chơi live): `python -m unittest tests.test_p2_ui_live -v`. Chạy đúng lệnh test ở trên, **đừng** thêm `-X utf8` (3 test `test_p1_contract` đọc stderr sẽ lỗi `NoneType.strip`, có sẵn trên `main`)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
Skill nằm trong `.agents/skills/<tên>/SKILL.md`; đọc SKILL.md trước khi làm việc tương ứng.
- `python-fact-grounded-coding`: dùng trước khi sửa logic Python; phải lấy bằng chứng từ test/runtime trước rồi mới chốt thay đổi. Soát quy ước: `python .agents/skills/python-fact-grounded-coding/scripts/check_rules.py`.
- `phase-1-verification`: chạy toàn bộ unittest, headless gather/quán (tất định, mã 2, nạp kho), ghi `docs/proof/phase-1/verify-run.txt` rồi cập nhật `docs/verification/phase-1.md`. Lệnh: `python .agents/skills/phase-1-verification/scripts/verify_phase1.py`.
- Windows: `python3` thường là lối tắt Microsoft Store (mã 9009) nên 21 test hộp đen fail dù luật đúng; script kiểm chứng tự tạo shim `python3`, không sửa `game.contract.json`.
