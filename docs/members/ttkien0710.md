# ttkien0710 (Trần Trung Kiên - MSSV: 2A202604014) — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - P1: Nấu, bưng bê, phục vụ, thanh toán, tip, uy tín ([5d77733](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/5d77733), PR #3).
  - P2: 2 bếp song song, ưu tiên đơn cũ nhất, menu 6 món, mở rộng `burn` ([8b3b93f](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/8b3b93f), PR #6).
  - P3 (AC-P3-05): Kho cá thể, tính `base_price` theo tươi bằng `Fraction`, tip `floor` ([5ceef47](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/5ceef47)).
  - P4 (AC-P4-02): Benchmark `chonoi/bench.py`, đo FPS/1% low, chạy Chrome headless đạt 46.92 FPS ([0d434d0](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/0d434d0)).
- Tôi đã review (kèm link):
  - Đối chiếu logic khách/giữ chỗ Q3 của Quoosc ([7af1a49](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/7af1a49), PR #8) bảo đảm tương thích.
- AI sai ở đâu và tôi phát hiện thế nào:
  - P1: AI thiếu nhả phím `interact` giữa 2 lần bấm.
  - P3: Dùng `round` thay vì `floor` tính tip làm lệch 1 đơn vị tiền.
  - P4: Gọi `load_scenario` thiếu tham số `path`. Phát hiện qua TDD và assertion error.
- Điều tôi học được:
  - Tầm quan trọng của tính tất định (tránh float trong luật), kỹ thuật rebase giải quyết xung đột khi làm song song và phương pháp đo benchmark thực tế.
