# ADR-0002: Kho cá thể `{id, kind, fresh}` và độ tươi (Contract v1.2)

- Trạng thái: **chấp nhận** (mục 1–5 theo `docs/plan/phase-3.md` §1). Phần triển khai còn dở, xem cột "Hiện trạng".
- Ngày, người quyết: 2026-11-21. Integrator (invzble-z) chốt, PO (nganhduong123) ghi. Rà hiện trạng ở `main` @ `48c96b3`.

## Bối cảnh
TICKET-03 đổi kho đếm `{"items":{kind: n}}` thành kho cá thể `{"items":[{id, kind, fresh}]}`, kèm theo:
- hao tươi 0.5/s ở giỏ, 0.25/s ở kho quán;
- hàng ươn khi `fresh < 30`, phát event `spoiled`;
- giữ chỗ theo id tươi nhất;
- giá món theo trung bình độ tươi.

Đây là breaking change ở file kho, gather, quán và `day`. Rủi ro chính có hai:
- **Sai số làm tròn ở ngưỡng 30 và ở `floor` giá.** Nếu dùng float, `30 − k/120` có thể rơi lệch 1 tick.
- **Nhiều người cùng đổi một schema.** Nếu mỗi người tự định nghĩa kiểu cá thể, `main` sẽ đỏ nhiều lần.

## Các lựa chọn đã cân nhắc
1. **float**: đơn giản nhưng sai ở ngưỡng với fixture như `33.3`. Loại.
2. **Số nguyên 240 đơn vị/điểm** (ticket gợi ý): chỉ đúng khi fixture là bội của 1/240. Ví dụ `33.33 × 240 = 7999.2`, không nguyên. Loại.
3. **`fractions.Fraction`** đọc từ chuỗi thập phân (`Fraction(str(x))`): đúng với mọi đầu vào JSON, chỉ đổi sang float khi ghi JSON. **Chọn.**

## Quyết định
| # | Quyết định | Hiện trạng (`48c96b3`) |
|---|---|---|
| 1 | `fresh` lưu bằng `Fraction`. Gather trừ `Fraction(1,120)` mỗi tick, quán trừ `Fraction(1,240)`, kẹp đáy 0. So `fresh < 30` và `floor` giá trên Fraction | ✅ gather (`1ae5ba7`), ✅ giá quán (`base_price` theo Fraction, AC-P3-05). ❌ hao tươi kho quán chưa có (`QuanSim` vẫn gộp kho thành map đếm) |
| 2 | Một kiểu dùng chung `Item(id, kind, fresh)` trong `chonoi/inventory.py` | ✅ `Item` trong `inventory.py` (`0748ff3`). Gather đã dùng `Item` (`_HoldItem = Item`) |
| 3 | Một bộ đếm `I<n>` qua `IdAllocator`. Chạy độc lập thì nối tiếp hậu tố lớn nhất đã nạp; trong `day`, `DaySim` giữ bộ đếm xuyên pha và Ngày | ✅ gather cấp `I<n>`, `ids.reserve` id đã nạp. `day` giữ id xuyên Ngày (AC-P3-08, `48c96b3`) |
| 4 | Adapter đọc theo `contract_version`: 1.0/1.1 là kho đếm, 1.2 là kho cá thể. Chỉ lật `"1.2"` khi Lặn và Quán xong | 🟡 `inventory.py` đọc/ghi 2 schema theo version, manifest đã có khối `freshness` (`0748ff3`). Manifest vẫn `"1.1"`; `scenario.py` chưa nhận mảng cá thể |
| 5 | Thứ tự trong tick: hao tươi hàng có sẵn **đầu bước**, hàng mới `fresh=100` hao từ bước sau. Quán: hao kho (gồm hàng giữ) → `spoiled` theo id → xử lý đơn có hàng vừa ươn → bếp → tương tác → thanh toán/kiên nhẫn → khách mới | ✅ gather đúng thứ tự (`tests/test_p3_gather.py`). Quán chưa có |

Khối manifest: `freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.

## Hệ quả
| Module | File | Ảnh hưởng | Chủ |
|---|---|---|---|
| Adapter, manifest | `chonoi/inventory.py`, `game.contract.json`, `docs/contracts/` | `Item`, đọc/ghi 2 schema, khối `freshness`, lật `"1.2"` | invzble-z |
| Scenario | `chonoi/scenario.py` | `gather.hold`, `quan.stock`, `customers[].reserved` thành mảng cá thể/id, kiểm id duy nhất → mã 2 | WorkOfMinh |
| Gather | `sim/gather.py` | ✅ giỏ cá thể, hao, `spoiled` | NguyenQuangDunghe161764 |
| Mất hàng | `sim/gather.py`, `sim/monsters.py` | `faint.lost`/`monster_hit.lost` thành mảng cá thể LIFO | comtrang378-ship-it |
| Quán | `sim/quan.py` | Kho cá thể, hao 0.25/s, giữ theo id tươi nhất (Quoosc). ✅ giá theo tươi, `cook_started.items` (ttkien0710) | Quoosc, ttkien0710 |
| `day` | `sim/day.py` | Bàn giao cùng tick, id xuyên Ngày, Shop không hao | invzble-z |
| Client | `chonoi/web/` | ✅ HUD độ tươi đọc cả 2 schema (`docs/proof/phase-3/hud-fresh/`) | nganhduong123 |
| Test cũ | `tests/` | Fixture kho đếm phải đổi khi lật `"1.2"`; ghi lý do trong commit (`AGENTS.md`) | chủ từng lát |

Cách sửa fixture khi lật v1.2: xem `CHANGELOG.md` mục Unreleased.
