# Hợp đồng tích hợp — NhomF7

> **Trạng thái:** đề xuất của PO (nganhduong123), chờ Integrator (invzble-z) duyệt. Chủ file: invzble-z.
> Nguồn: PRD-0 (Test Contract v1.0), TICKET-02 (v1.1), TICKET-03 (v1.2), code trên `main` lúc `8216a95`, rà lại lúc `721088a` (sau lát 4a `sim/day.py`), xem mục 8 và 10.
> Đổi hợp đồng: mở PR, báo cả nhóm, Integrator duyệt. Đổi tên trường/sự kiện phải sửa cùng lúc sim, test và `chonoi/web/mock/*.json`.

## 1. Phiên bản và quy tắc chuyển

| `contract_version` | Phase | Thay đổi chính | Trạng thái trên `main` |
|---|---|---|---|
| `"1.0"` | 1 | gather + quan độc lập, kho đếm | ✅ đã chạy, tag `phase-1` |
| `"1.1"` | 2 | số chuẩn, 6 món, 2 bếp/4 bàn, cá bơi/sinh, Cá Sấu, `--mode day`, Shop, pause | 🟡 manifest `"1.1"` (`b85711d`), `--mode day` + Shop + pause chạy được (`721088a`). Còn lệch ticket (mục 8), lệch payload (mục 10), chưa có Cá Sấu (`sim/monsters.py`) |
| `"1.2"` | 3 | kho cá thể `{id,kind,fresh}`, độ tươi, giữ chỗ theo id, giá theo fresh | ❌ chưa làm |

- Mọi số liệu chỉ đọc từ `game.contract.json`, không hard-code trong luật (`AGENTS.md`).
- Bên đọc kho chọn schema theo `contract_version` (mục 2). Chỉ lật sang `"1.2"` khi cả gather và quán đã đọc/ghi được kho cá thể, để `main` luôn xanh.

## 2. Schema file kho (gather → quán)

### v1.0 / v1.1: kho đếm ([inventory.sample.json](inventory.sample.json))
```json
{"items":{"bong_sung":2,"ca_loc":1}}
```
- Đúng một khóa `items`: object `kind → số nguyên ≥ 0`. Bên ghi bỏ khóa có lượng 0. Kho rỗng là `{"items":{}}`.
- Kind thuộc danh mục: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo` (v1.0 chỉ có 4 loại đầu không có `ca_keo`, `keo_neo`).
- Sai schema, kind lạ, số âm/không nguyên → mã 2. Trần giỏ không áp lên kho quán.

### v1.2: kho cá thể ([inventory.v12.sample.json](inventory.v12.sample.json))
```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```
- `items` là mảng `{id, kind, fresh}`, xuất theo id. Kho rỗng là `{"items":[]}`.
- `id` duy nhất, khác rỗng, cấp `I1, I2, …` theo thứ tự vào giỏ, tăng xuyên pha và Ngày. `fresh` hữu hạn trong `[0,100]`.
- Khi chạy v1.2, file kho đếm, id trùng, kind lạ, fresh ngoài miền → mã 2.

### Quy tắc ghi (mọi phiên bản)
- `gather --inventory-out` ghi **đúng một lần** khi có `gather_end`, nội dung khớp `gather_end.data.inventory`. Ngất ghi kho rỗng.
- Ghi file tạm cùng thư mục rồi thay thế nguyên tử. Chạm `--ticks` trước `gather_end` thì không tạo/không ghi đè.
- Trong `--mode day`, kho bàn giao trong bộ nhớ ở cùng tick đổi pha, cùng schema với file.

## 3. CLI headless

```
<headless_cmd> --mode gather|quan|day --seed <int>
  [--scenario <file.json>] [--inputs <file.json>]
  [--inventory <file.json>] [--inventory-out <file.json>]
  [--days <N>] --ticks <N> --out <file.jsonl> [--snapshot-every <N>]
```
- `--inventory` chỉ với `quan`, `--inventory-out` chỉ với `gather`. `--days` chỉ với `day`, nguyên 1–5, mặc định 1 (v1.1).
- Mã thoát: 0 kết thúc lượt hoặc chạm `--ticks`; 2 cờ/dữ liệu sai, fixture mâu thuẫn; 1 lỗi thực thi/ghi.
- Kiểm dữ liệu lúc khởi tạo **trước** khi ghi JSONL hoặc kho.

## 4. File inputs và nút

| Trường | Kiểu | Pha | Có từ |
|---|---|---|---|
| `tick` | nguyên ≥ 0, tăng nghiêm ngặt | mọi pha | v1.0 |
| `move` | `[a, b]` trong `[-1,1]`, chuẩn hóa nếu dài > 1. `b` dương là xuống (gather) / về bắc (quán) | gather, quan | v1.0 |
| `interact` | bool, cạnh lên | gather (cập bến, hái), quan (nấu, bưng, phục vụ) | v1.0 |
| `catch` | bool, cạnh lên | gather, chỉ dưới nước | v1.0 |
| `pause` | bool, cạnh lên | gather, quan, shop | v1.1 |
| `shop_done` | bool, cạnh lên | shop | v1.1 |
| `buy` | chuỗi khác rỗng, chỉ có tác dụng ở frame khai báo | shop: `oxygen`, `hp` (+ `weapon`, `net`, `buy:<kind>`, `sell:<kind>` nếu bật mở rộng) | v1.1 |
| `attack`, `photo` | bool, cạnh lên | gather, chỉ khi bật mở rộng Lao / Sổ tay | v1.1 |

- Trước frame đầu: `move = [0,0]`, mọi nút `false`. Frame chỉ cập nhật trường có mặt.
- Giữ nút qua đổi pha không tạo cạnh mới. Nút đúng kiểu nhưng sai pha hoặc mở rộng chưa bật thì bỏ qua.
- Trường lạ, sai kiểu, tick lặp/giảm → mã 2. Shop gặp `buy` không hỗ trợ → event `buy_failed` (`reason:"unknown"`), không phải mã 2.
- **Pause:** xét cạnh `pause` trước. Bước vào pause chỉ tăng `tick` ngoài và phát `paused`. Trong pause bỏ qua cạnh hành động và `buy`; `sim_tick`, `phase_tick`, lịch, timer và (v1.2) độ tươi đứng yên. Cạnh `pause` tiếp theo phát `resumed` và chạy gameplay ngay bước đó.

**Hiện trạng code (`721088a`):** headless `--mode day` dùng `BUTTONS_V11` (thêm `pause`, `shop_done`, `buy`); `--mode gather|quan` vẫn `BUTTONS_V10` nên file inputs của hai mode này có `pause` sẽ bị mã 2. `chonoi/live.py` nhận đủ nút v1.1 và `buy` (ADR 0001); chạy riêng gather/quan thì bản chơi tự giữ trạng thái tạm dừng.

## 5. Giao diện sim ↔ client web (`chonoi/live.py`)

Client không chứa luật; chỉ đọc snapshot và gửi input. Chi tiết ở [ADR 0001](../adr/0001-client-web-module.md).

| Endpoint | Hướng | Nội dung |
|---|---|---|
| `GET /state` | sim → client | Snapshot hiện tại (mục 6) + `meta` (tuning của pha đang chạy: `gather`/`quan`/`shop`), `menu` (tuning menu), `events` (event mới từ lần đọc trước), `finished`, `reason`, `error` |
| `POST /input` | client → sim | `{"move":[a,b], "interact":bool, "catch":bool, "pause":bool, "shop_done":bool, "attack":bool, "photo":bool, "buy":"oxygen"}`, mọi trường tùy chọn. Sai kiểu → HTTP 400 |
| `POST /restart` | client → sim | Dựng lại lượt từ đầu |
| `POST /bench` | client → sim | Chỉ ở `/?bench=1` (P4): `{frame_ms[] (ms, > 0), frames, measured_s > 0, warmup_s, first_frame_epoch_ms, width, height, dpr}`. Body tối đa 1 MB. Sai kiểu → HTTP 400 |
| `GET /bench` | sim → bench | `{ready, result}`; `chonoi/bench.py` cũng chờ được `LiveGame.bench_event` trong cùng tiến trình |
| `GET /<file>` | — | File tĩnh trong `chonoi/web/`, chặn thoát thư mục |

- `/state` của bản chơi có thêm trường **chỉ để hiển thị** (không có trong JSONL): `shift_earned` (pha quán), `days_completed`, `max_days` (mode day). `chonoi.live --mode day --days 1–5`, mặc định 5.
- Màn DayIntro (4 s), EveningIntro, DayResult, Summary là của bản chơi, **không** có trong headless. Client gửi `pause` để timer đứng yên khi hiện các màn này (`docs/clarify.md` #3).
- Chế độ mock (`/?mock=day-gather`, `day-quan`, `day-shop`, `day-summary`, `gather`, `quan`) đọc `chonoi/web/mock/*.json`. Mock phải có đúng tên trường như snapshot thật.
- Hiệu ứng, hạt và RNG của giao diện tách khỏi `Streams` của mô phỏng. Bản chơi không được làm đổi JSONL headless.

## 6. Snapshot

| Phạm vi | Trường |
|---|---|
| Chung | `type:"snapshot"`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state` (`playing`/`finished`/`paused` từ v1.1), `time_left_ticks`, `money`, `earned`, `reputation`, `score` |
| gather | `player` (`pos`, `vel`, `heading_deg`, `oxygen_ticks`, `hp`, `zero_oxy_ticks`, `catch_cd_ticks`, `oxygen_max_ticks`, `hp_max`, `at_surface`, `invuln_ticks` từ v1.1), `hold`, `hold_count`, `hold_capacity`, `nodes[]`, `fish[]`, `monsters[]` (v1.1) |
| quan | `player`, `stock`, `hand`, `stoves[]` (`id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`), `tables[]` (`id`, `pos`, `customer_id`), `customers[]` (`id`, `table_id`, `dish_id`, `order_tick`, `state`, `patience_ticks_left`, `eat_ticks_left`, `order_status`, `reserved`, `base_price`, `tip`) |
| day (v1.1, mọi pha) | `day`, `day_plan`, `upgrades` (cấp đã mua), `active_upgrades` (cấp đang áp dụng), `phase` ∈ `gather`/`quan`/`shop` |
| shop (v1.1) | `stock` (kho dư từ ca), `time_left_ticks` tới lúc đóng |

- Snapshot ở tick 0 sau khi dựng fixture, ở bội số `--snapshot-every`, ở tick dừng. Tối đa một snapshot mỗi tick. Snapshot đổi pha ghi pha mới với `phase_tick:0`.
- Mảng thực thể sắp theo id (`ids.sort_by_id`), `hold` theo thứ tự nhặt. Tọa độ 3 chữ số thập phân.
- `stock` trong snapshot quán là kho **khả dụng** (đã trừ phần giữ) theo giả định `docs/clarify.md` #4.

## 7. Vòng ngày (`--mode day`, v1.1)

```
DayIntro → gather → EveningIntro → quan → DayResult → Shop → DayIntro … (Summary sau Ngày cuối)
```
(Các màn Intro/Result/Summary chỉ có ở bản chơi.)

**Thứ tự event đổi pha** (cùng tick, pha mới chạy gameplay từ bước sau):
1. `day_start {}` → `day_plan {dishes, ingredients}` → `phase_start {}` (pha gather).
2. `gather_end` (của pha cũ) → dựng quán với kho bàn giao → `phase_start {}` (quan), kể cả khi ngất (kho rỗng).
3. `quan_end` → dựng Shop → `phase_start {}` (shop).
4. Shop: xử lý một `buy` trước cạnh `shop_done`. Đóng bằng nút → `shop_end {reason:"done"}`, hết 600 tick hoạt động → `shop_end {reason:"time"}`. Đóng Shop thì `days_completed += 1`, rồi kết thúc hoặc dựng Ngày kế ngay tick đó.
5. **Chỉ khi dựng Ngày mới** mới sao `upgrades` sang `active_upgrades`. Oxy và Máu hồi đầy theo cấp có hiệu lực, giỏ làm mới, kho dư bị bỏ sau Shop.

- Giữ qua Ngày: `money`, `earned`, `reputation`, cấp nâng cấp (và bộ đếm id `I<n>` ở v1.2).
- Shop mua: đủ đúng giá vẫn mua được, trừ `money`, giữ `earned` và điểm. Thiếu tiền → `buy_failed {action, reason:"funds"}`, đã tối đa → `reason:"max_level"`.
- Quán trong `day`: lọc menu theo id món trong kế hoạch **trước** khi lọc nguyên liệu khả dụng. Quán độc lập dùng cả 6 món.
- Dòng `end` của `day` có thêm `days_completed`. Đủ số Ngày → `reason:"days_complete"`. Event trong chế độ day có thêm trường `day` ở vỏ.

## 8. Lệch giữa `game.contract.json` (`8216a95`) và TICKET-02 — cần Integrator sửa

| Khóa | Ticket yêu cầu | Đang có trên `main` |
|---|---|---|
| `tuning.day_plan` | **Mảng** 5 object `{day, dishes, ingredients}` | Map `"1"`…`"5"` |
| `day_plan` D2 | `ca_loc_nuong_trui ×2, lau_ca_linh_dien_dien ×2` | `canh_chua_ca_loc ×3, ca_loc_nuong_trui ×2` |
| `day_plan` D3 | `goi_bong_sung ×2, canh_chua_ca_loc ×2, ca_keo_nuong ×2` | `lau_ca_linh_dien_dien ×2, ca_keo_nuong ×3` |
| `day_plan` D4 | `lau_mam ×1, ca_loc_nuong_trui ×2, goi_bong_sung ×1` | `lau_mam ×2, goi_bong_sung ×4` |
| `day_plan` D5 | `lau_mam ×1, lau_ca_linh_dien_dien ×1, ca_loc_nuong_trui ×1` | `lau_mam ×3, canh_chua_ca_loc ×3` |
| `gather.fish_initial` | Số `8` | Mảng 6 đàn cố định, **không có đàn `ca_keo`**, trong khi kế hoạch D3–D5 cần `ca_keo` (D3 cần 6). Sim đã đọc được khóa ticket (`7858a39`), manifest chưa khai nên vẫn không lấy đủ |
| Khóa cá | `fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_ticks`, `fish_spawn_clearance`, `fish_x`, `fish_depths`, `fish_spawn_x`, `fish_spawn_depths`, `fish_weights` | Manifest vẫn chỉ có khối `fish_motion {speed, turn_every_ticks, max_turn_deg, min_depth}`. `sim/gather.py` (`7858a39`) đã đọc được các khóa ticket, chỉ thiếu trong manifest |
| `gather.monsters` | `species.ca_sau {patrol_speed, chase_speed, detect_radius, exit_radius, depths, hit_radius, recoil_ticks, recoil_dist}`, `spawns[]` (M1, M2 từ Ngày 3), `invuln_ticks:90`, `loss_ratio:0.5` | Đã khớp; M1 từ Ngày 1, M2 từ Ngày 3, scenario có thể thay danh sách |
| `shop` | `{max_ticks, upgrades}` | ✅ đã thêm `max_ticks: 600` (`721088a`) |

Đã khớp: `contract_version:"1.1"`, 6 món trong `menu`, B1/B2, T1–T4, N1–N6, `fish_yield` đủ 3 loài, `shop.upgrades.oxygen/hp`.

## 9. Danh sách event

| Event | `data` | Phát bởi | Có từ |
|---|---|---|---|
| `gather` / `node_regrown` | `node_id, kind, amount` / `node_id` | gather | v1.0 |
| `hold_full` | `action` (gather/catch), `node_id` hoặc `fish_id`, `required`, `free` | gather | v1.0 |
| `fish_caught` | `fish_id, kind, yield` | gather | v1.0 |
| `dive` / `surface` | `pos` | gather | v1.0 |
| `oxygen_empty` / `choke` | `oxygen_ticks:0` / `hp` | gather | v1.0 |
| `faint` | `cause` (`choke`/`monster`), `lost` (LIFO), `hp:0` | gather | v1.0, `monster` từ v1.1 |
| `gather_end` | `reason` (time/docked/fainted), `inventory` (mục 2) | gather | v1.0 |
| `fish_spawned` | `id, kind, pos` | gather | v1.1 |
| `monster_hit` | `monster_id, hp, lost, pos` (vị trí người chơi) | gather | v1.1 |
| `customer_arrived` / `no_dish` | `order_id, table_id, dish_id` / `{}` | quan | v1.0 |
| `cook_started` / `dish_ready` / `dish_picked` | `stove_id, order_id, dish_id` (+ `items, base_price` khi bắt đầu nấu) | quan | v1.0 |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` | quan | v1.0 |
| `paid` | `order_id, table_id, base_price, tip, amount, reason` (finished_eating/closing) | quan | v1.0 |
| `customer_left` | `order_id, table_id, reason` (patience/closing), `reputation` | quan | v1.0 |
| `quan_end` | `reason:"time", money, earned, shift_earned, reputation` | quan | v1.0 |
| `dish_burnt` | `stove_id, order_id, dish_id, order_status` | quan (mở rộng `burn`) | v1.1 |
| `day_start` / `phase_start` | `{}` | day | v1.1 |
| `day_plan` | `dishes, ingredients` | day | v1.1 |
| `paused` / `resumed` | `{}` | mọi pha | v1.1 |
| `bought` | `upgrade, level, price, money` | shop | v1.1 |
| `buy_failed` | `action, reason` (funds/max_level/out_of_stock/unknown) | shop | v1.1 |
| `shop_end` | `reason` (done/time) | shop | v1.1 |
| `spoiled` | `item_id, kind, location` (hold/stock) | gather, quan | v1.2 |

Ở v1.2: `items` trong `cook_started` và `lost` trong `faint`/`monster_hit` đổi thành mảng cá thể `{id,kind,fresh}`.

## 10. Lệch giữa code (`721088a`) và hợp đồng — cần chủ lát chọn một bên rồi sửa cùng lúc sim, test, mock

PO rà bằng cách đọc `chonoi/sim/*.py` và chạy `headless --mode day --seed 1`. Chưa đổi gì trong sim.

| Chỗ | Hợp đồng (mục 6, 9) | Code đang phát | Chủ |
|---|---|---|---|
| Khóa khách trong event quán | `order_id` | `customer_id` (`customer_arrived`, `cook_started`, `served`, `paid`, `customer_left`) | Quoosc, ttkien0710 |
| `paid.data` | `base_price, tip, amount, reason` | `price, money, tip, reputation, patience_ratio, dish_id`, không có `reason` | ttkien0710 |
| Event cháy món | `dish_burnt` | `dish_burned` (+ `dish_discarded` khi dọn bếp) | ttkien0710 |
| `state` trong snapshot/end của `day` | `playing`/`finished`/`paused` | `running`/`finished`/`paused` (gather/quan riêng vẫn `playing`) | invzble-z |
| `money`, `earned`, `score` trong pha quán của `day` | tăng khi khách trả tiền | chỉ cộng khi đóng ca (`DaySim` giữ riêng). Bản chơi hiện `shift_earned` để bù | invzble-z |
| Event đổi pha đầu Ngày 1 | ở tick dựng Ngày | `day_start`/`day_plan`/`phase_start` phát ở tick 1 (bước đầu tiên), snapshot tick 0 đã là pha gather | invzble-z |
| `monsters[]` trong snapshot | `kind` (theo mock/§6) | `sim/monsters.py` đã có, nhưng phát `species` (+ `waypoint_index`, `recoil_ticks`). Client đọc cả hai | comtrang378-ship-it |

Client web đọc được cả hai cách đặt tên (`dish_id`/`dish`, `price`) nên không vỡ khi các lát đổi theo hợp đồng.
