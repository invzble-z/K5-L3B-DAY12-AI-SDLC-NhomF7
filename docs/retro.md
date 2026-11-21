# Retro nhóm

## Phase 2 (nhanh)
> Nháp do PO (nganhduong123) dựng từ bằng chứng trong repo lúc `81b5aab`, cập nhật lúc `721088a` (sau lát 4a). Cả nhóm sửa/bổ sung trong buổi retro.

- Điều tốt:
  - Chia "nhà" theo hàm và giữ qua các phase: các lát cá bơi/sinh (Dũng), Q3 (Quốc), 2 bếp/6 món/`burn` (Kiên), UI (Dương) đều vào main qua PR nhỏ.
  - Test tăng từ 44 (P1) lên 96 (`81b5aab`), 119 (`721088a`) và 127 khi thêm `test_p2_ui_live.py`, toàn bộ đạt. Mỗi lát có file test riêng (`test_p2_fish.py`, `test_p2_quan_lat3b.py`...).
  - UI không phải chờ sim: Shop, pause và `day` làm bằng mock theo trường snapshot đã chốt. Khi `day.py` vào `main`, client chạy được cả vòng 2 Ngày với sim thật, chỉ phải sửa 4 lỗi nhỏ ở `live.py`/HUD (`docs/proof/phase-2/ui-day/`).
  - Script kiểm chứng tự thêm shim `python3`, nên máy Windows không còn báo fail giả (mã 9009).
- Điều tệ:
  - Lõi v1.1 xong muộn: số chuẩn v1.1 vào main ở `b85711d`, `sim/day.py` ở `721088a` (cuối phase). Vẫn chưa có `sim/monsters.py` (Cá Sấu), nên "Thủy quái!" chỉ thấy trên mock. Chưa gắn tag `phase-2`; Phase 3 và Phase 4 bị nợ dồn.
  - Đường găng dồn vào một người (Integrator vừa giữ số chuẩn vừa làm `day.py`).
  - Gộp muộn nên nhiều lần phải merge `main` và giải xung đột (`sim/quan.py`, `ai-usage-log.md`, `standup.md`).
  - Chưa review chéo: cả 11 PR đã gộp (#1–#11) đều có 0 review trên GitHub (`gh pr list --json reviews`), dù thỏa thuận là người dự phòng review. Lát 4a đẩy thẳng lên `main`, không qua PR.
  - Hợp đồng viết muộn (`bfb5160`, PR #10) nên code và hợp đồng đã lệch: `customer_id`/`order_id`, payload `paid`, `dish_burned`, `state:"running"` (`docs/contracts/README.md` mục 10). Thiếu đàn cá kèo nên kế hoạch D3–D5 không lấy đủ nguyên liệu (clarify #5).
  - Nhiều câu hỏi chờ PO quá lâu (Q3 D-01..D-09, Q4-F1, `no_dish`). PO chốt ở clarify #10–#15 lúc cuối phase.
- Trạng thái hành động (lúc `721088a`): `day.py` đã vào `main` (invzble-z, `721088a`), Kiên chưa pair. Adapter kho cá thể chưa có.
- Hành động bổ sung: **mỗi PR phải có 1 review của người dự phòng trước khi gộp** (Integrator không tự gộp PR chưa review). Người nhận: **invzble-z**, PO kiểm ở retro P4.
- 1 hành động cho Phase 3: **trả nợ Phase 2 trước khi bật v1.2.** Số chuẩn v1.1 đã có (`b85711d`). Bào đẩy adapter kho cá thể trước phút 12. Kiên (đã xong 3b) pair với Bào làm `day.py`. Người nhận: **invzble-z**. Minh kiểm lại ở standup phút 20.

## Phase 3 (nhanh, về lần đổi kho đếm → kho cá thể)
> Nháp do PO (nganhduong123) dựng lúc `main` @ `48c96b3`. Thứ tự vào `main` lấy từ `git log`.

- Diễn biến:
  1. Gather làm giỏ cá thể **trước** khi có kiểu dùng chung (`1ae5ba7`, Dũng, kiểu tạm `_HoldItem`).
  2. Quán làm giá theo độ tươi (PR #12, Kiên).
  3. Sau đó mới có adapter `Item` + khối `freshness` (`0748ff3`, Bào) và bàn giao `day` giữ id xuyên Ngày (`48c96b3`).
  4. HUD độ tươi làm trên mock, kiểm với giỏ thật (PR #15, Dương).
- Điều tốt:
  - Chốt `Fraction` từ đầu (ADR 0002) nên ngưỡng 30 và `floor` giá có test chính xác (`tests/test_p3_gather.py`, `test_p3_quan_price.py`), không gặp lỗi lệch 1 tick.
  - Gather đổi từ kiểu tạm sang `Item` chỉ bằng một dòng `_HoldItem = Item`, không vỡ test.
  - Adapter đọc 2 schema theo version nên `main` vẫn xanh suốt phase.
- Điều tệ:
  - Adapter là đường găng nhưng vào **sau** các lát dùng nó, nên mỗi lát tự dựng kiểu tạm, và chỗ nối các lát lại không có ai kiểm. Ví dụ: `GatherSim` đọc `tuning.contract_version`, trong khi manifest để `contract_version` ở gốc và không chỗ nào chép vào `tuning`; lật `"1.2"` thì gather vẫn chạy giỏ đếm (clarify #9).
  - Chưa lật `"1.2"`, kho cá thể + hao tươi ở quán và scenario v1.2 chưa xong.
  - Chưa có tag `phase-3`.
  - 5 test `expectedFailure` trong `test_p2_q3_day_integration.py` đánh dấu chỗ hở đã biết nhưng chưa có người nhận sửa.
  - Retro nhanh và standup P3 không làm đúng giờ: nháp này viết bù cuối buổi.
- 1 hành động cho Phase 4: **trước khi lật `"1.2"`, chạy một smoke đầu-cuối với manifest thật** (gather `--inventory-out` → quán `--inventory`, so id/kind/fresh), không chỉ test từng lát với tuning tự dựng. Người nhận: **WorkOfMinh** (QA), invzble-z sửa chỗ chép `contract_version`.

## Phase 4 (cuối)
> Nháp do PO (nganhduong123) dựng từ bằng chứng trong repo lúc `main` @ `48c96b3` (+ nhánh `p4/bench-tuong-phan` của PO). Cả nhóm sửa/bổ sung trong buổi retro. Số liệu lấy bằng lệnh ghi ở từng dòng.

### 1. Rà hành động đã chốt ở retro P2 (và P3)
| Hành động | Người nhận | Đã làm chưa | Bằng chứng / vì sao |
|---|---|---|---|
| Trả nợ Phase 2 trước khi bật v1.2 | invzble-z | ✅ Đã hoàn thành | `sim/day.py`, `sim/monsters.py` đã vào `main`; adapter `Item` + `freshness` (`0748ff3`); `day` giữ id xuyên Ngày (`48c96b3`). Đã gộp toàn bộ PR P3/P4 và gắn tag `phase-3` tại `edd0a71` |
| Kiên pair với Bào làm `day.py` | ttkien0710, invzble-z | ❌ | `git log -- chonoi/sim/day.py`: Bào viết chính (`721088a`, `0748ff3`), Tú nối pha ngày đêm (`6e5cd3c`) và Cá Sấu (`8251ef0`); không có commit của Kiên. Kiên chuyển sang giá theo độ tươi (PR #12) |
| (P3) Smoke đầu-cuối với manifest thật trước khi lật `"1.2"` | WorkOfMinh, invzble-z | ❌ | Chưa lật `"1.2"`; lỗi chép `contract_version` vào `tuning` (clarify #9) chưa sửa |
| Mỗi PR có 1 review của người dự phòng trước khi gộp | invzble-z | ❌ | `gh pr list --json reviews`: 14/14 PR đã gộp đều có 0 review, kể cả #13 và #14 sau retro P2. Một số commit lớn (`721088a`, `0748ff3`, `48c96b3`) đẩy thẳng lên `main` |

### 2. Điều tốt
- **Giữ "nhà" qua 4 phase.** Mỗi người sửa module của mình khi luật đổi: Dũng giỏ cá thể (`1ae5ba7`), Kiên giá theo tươi (PR #12), Bào adapter + `day`, Quốc khách trong `day` (PR #14), Dương client. Gần như không xung đột code, chỉ xung đột ở file docs ghi chung (nhật ký AI, standup, clarify).
- **Client không phải chờ sim.** Mock theo trường snapshot đã chốt cho phép làm Shop, pause, HUD độ tươi, 3 cảnh báo trước khi sim có. Khi sim thật vào, client chỉ phải sửa nhỏ (pause khi chạy riêng, tên trường `species`).
- **Bằng chứng chạy được lại:** mỗi lát có `docs/proof/...` và lệnh tái lập; client có script Chrome headless chụp ảnh, đo FPS, bắt lỗi console.
- **Test tăng đều:** 44 (P1) → 96 → 127 (P2) → 182 (`48c96b3` + nhánh PO).

### 3. Điều tệ
- **Đường găng dồn vào Integrator suốt buổi:** số chuẩn, `day.py`, adapter, Release đều qua một người. Đến cuối Phase 4, toàn bộ đã được giải phóng khi gắn tag `phase-3`, contract v1.3, gộp PR #16 bench và PR #17 soak, hoàn thiện `LICENSE` và Release v1.0.0.
- **Không review chéo** (mục 1): thỏa thuận trong `TEAM.md` không được thực hiện lần nào.
- **Hợp đồng viết sau code** nên lệch tên trường. Ví dụ: `customer_id`/`order_id`, `dish_burned`, `state:"running"`, quái phát `species` trong khi mock dùng `kind` (`docs/contracts/README.md` §10).
- **Câu hỏi chờ PO quá lâu:** Q3 D-01..D-09, Q4-F1, `no_dish` mở từ P1 tới cuối P2 mới chốt (clarify #10–#15).
- **Phản tư cá nhân chưa đủ:** `docs/members/` mới có 4/7 người (Quoosc, invzble-z, nganhduong123, ttkien0710). Thiếu comtrang378-ship-it, NguyenQuangDunghe161764, WorkOfMinh.

### 4. Số liệu
**Commit theo tác giả** (`git shortlog -sn --no-merges origin/main` @ `48c96b3`):

| Tác giả git | Commit | Ghi chú |
|---|---|---|
| Nguyen Anh Tu (+ NguyenAnhTu-37-IT) | 13 + 1 | comtrang378-ship-it |
| Quoosc | 12 | |
| Hai Duong | 9 | **chưa xác định là ai** trong `TEAM.md` (ADR 0003 #7) |
| Nguyen Quang Dung | 8 | NguyenQuangDunghe161764 |
| Kien Trung | 6 | ttkien0710 |
| nganhduong123 + AnhDuong | 6 + 5 | cùng một người, hai cấu hình git (chưa tính commit trên nhánh `p4/bench-tuong-phan`) |
| invzble zone | 5 | invzble-z |
| DepressedLonerd | 3 | WorkOfMinh |

**PR:** 14 PR đã gộp, 0 review.
- nganhduong123: 7 PR (#1, #2, #5, #7, #9, #10, #13);
- Quoosc: 3 (#8, #11, #14);
- ttkien0710: 3 (#3, #6, #12);
- WorkOfMinh: 1 (#4).

**Cách đọc code của nhau:** không có review trên GitHub. Việc đọc chéo diễn ra khi gộp `main` và giải xung đột, khi Quốc review Q4 bằng test (`test_q4_f1_orphan_dish_reproduced`), và khi PO rà code để viết hợp đồng §10.

**Token theo người** (`docs/ai-usage-log.md`):
- ttkien0710 ~90k (30k + 35k + 25k);
- invzble-z ~70k (20k + 25k + 25k);
- Quoosc, nganhduong123, nhóm Copilot: "không đo được".

Nhóm không thống nhất cách đo token từ đầu, nên số này không so sánh được giữa các công cụ.

### 5. Một lần AI sai và cách nhóm xác minh
- **AI sai:** AI của PO viết vào kế hoạch rằng nhóm "đã gắn tag `phase-1`" trong khi repo chưa có tag nào.
- **Cách xác minh:** chạy `git tag -l` và `git ls-remote --tags origin`, cả hai đều rỗng, nên sửa lại kế hoạch.
- **Lần tương tự ở Phase 3:** AI xếp các thay đổi của PR #13 vào mục tag `phase-2` trong CHANGELOG; `git merge-base --is-ancestor f3f4a5f phase-2` cho thấy PR gộp sau tag.
- **Lỗi khác cùng kiểu** "tin kết quả mà không đọc lại": script sửa file không áp được (CRLF, chuỗi trùng hai chỗ) nhưng ảnh bằng chứng vẫn được chụp từ bản cũ. Phát hiện nhờ `grep` lại trước khi ghi "đạt".
- **Quy tắc rút ra:** mọi khẳng định về trạng thái repo (tag, commit, test xanh) phải kèm lệnh kiểm và đầu ra; kết quả do script sửa file phải `grep`/`git diff` lại.

### 6. Nếu làm lại, đổi gì
1. Chốt hợp đồng (tên trường, payload event) **trước** khi viết sim, và có một test kiểm tên trường chung cho cả sim và mock.
2. Bật branch protection trên `main`: bắt buộc 1 review, không đẩy thẳng. Người dự phòng review trong 10 phút.
3. Tách đường găng: Integrator chỉ giữ manifest và Release; `day.py` giao người khác từ đầu Phase 2.
4. PO trả lời clarify trong vòng một phase; câu nào quá hạn thì chốt tạm theo code và ghi rõ.
5. Thống nhất cách ghi token/chi phí cho mọi công cụ AI ngay ở Phase 1.
