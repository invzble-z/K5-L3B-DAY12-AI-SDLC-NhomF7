# Báo cáo cá nhân Phase 1–4 — Phạm Trấn Quốc

## 1. Thông tin và tổng quan

- **Dự án:** Quán Ăn Chợ Nổi, Day 12 — AI-SDLC.
- **Thành viên:** Phạm Trấn Quốc; MSSV **2A202604113**; GitHub **Quoosc**.
- **Nhóm:** NhomF7; vai trò chính: developer Q3.
- **Phạm vi:** khách hàng, reservation và kiên nhẫn trong Quán; hỗ trợ tích hợp và kiểm thử.
- **Công nghệ:** Python, unittest, JSON/JSONL, Git và mô phỏng headless.
- Trách nhiệm cốt lõi là xây dựng hành vi khách và ranh giới giữa đơn hàng với kho.
- Sau đó công việc mở rộng sang kiểm thử liên pha, review Q4 và soak DaySim.
- Nguồn phân công: [TEAM](../../TEAM.md), [kế hoạch chung](../plan/phan-chia-cong-viec.md).

## 2. Nhiệm vụ được phân công

| Phase | Nhiệm vụ | Vai trò | File chính | Kết quả |
|---|---|---|---|---|
| 1 | Khách, giữ chỗ, kiên nhẫn | Chủ Q3 | [quan.py](../../chonoi/sim/quan.py) | Logic và test Q3 |
| 2 | Bốn bàn, lọc món, lịch khách | Chủ Q3; hỗ trợ Day/Q4 | [Day integration](../../tests/test_p2_q3_day_integration.py) | Kiểm thử và sửa giao diện tích hợp |
| 3 | Độ tươi và reservation theo ID | Chủ Q3 kho Quán | [freshness tests](../../tests/test_p3_q3_freshness.py) | Hao tươi, spoil và retry |
| 4 | Soak nhiều ngày | Chủ AC-P4-03 | [soak.py](../../chonoi/soak.py) | Soak và replay |

- Q4 bếp, phục vụ và thanh toán do Kiên phụ trách; tôi review ranh giới với Q3.
- DaySim và contract thuộc phạm vi Integrator; tôi sửa các điểm tích hợp và để chủ module review.
- Các kế hoạch gốc: [P1](../plan/phase-1.md), [P2](../plan/phase-2.md), [P3](../plan/phase-3.md), [P4](../plan/phase-4.md).

## 3. Phase 1 — mục tiêu khách hàng

- Khách có thể được khởi tạo từ scenario hoặc đến theo lịch mô phỏng.
- Mỗi khách chiếm một bàn, chọn một món và giữ đủ nguyên liệu cho công thức.
- Đồng hồ kiên nhẫn quyết định khi nào khách rời quán.
- Phần Q3 cung cấp trạng thái đơn để Q4 có thể nấu và phục vụ.
- Các trạng thái và quyết định tạm thời được mô tả trong [proof Q3](../proof/phase-1/q3/README.md).

## 4. Phase 1 — phương pháp triển khai

- `QuanSim` khởi tạo khách, bàn và thông tin món từ tuning hoặc fixture.
- Chọn món phải xét công thức và lượng kho khả dụng.
- Reservation bảo vệ nguyên liệu cho đơn trước khi bếp tiêu thụ.
- Khi khách rời, phần chưa tiêu thụ được giải phóng theo trạng thái reservation.
- Kiên nhẫn được cập nhật qua từng bước mô phỏng; sự kiện thông báo khách rời.
- Snapshot cho phép quan sát trạng thái bàn, khách và kho tại thời điểm kiểm tra.
- Ngẫu nhiên dùng `Streams`, còn thứ tự thực thể theo quy ước ID của dự án.
- [Commit Q3 P1](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/1ac400e) ghi nhận lifecycle khách và reservation.

## 5. Phase 1 — kiểm chứng

- [Test Q3](../../tests/test_p1_q3.py) bao phủ khởi tạo, lịch đến, bàn, reservation và kiên nhẫn.
- Fixture sai được kiểm tra trước khi headless ghi kết quả.
- Replay cùng seed và input kiểm tra tính lặp lại của luồng mô phỏng.
- Verifier ghi cả headless, input sai mã 2 và khả năng nạp kho mẫu.
- `hand: null` có test ở đường scenario v1.3.
- Semantics `assigned` và mâu thuẫn Contract D vẫn cần nguồn PRD/Test Contract chính thức.
- Do đó, kết quả test thể hiện hành vi kỹ thuật hiện có, chưa thay thế xác nhận nghiệp vụ.
- Chi tiết: [verification Phase 1](../verification/phase-1.md).

## 6. Phase 2 — yêu cầu mở rộng

- Phase 2 mở rộng quán lên bốn bàn và menu sáu món.
- DaySim cần chuyển nguyên liệu từ buổi Gather sang ca Quán.
- Kế hoạch ngày giới hạn danh sách món được chọn trong chế độ Day.
- `order_tick` hỗ trợ thông tin thứ tự đơn cho giao diện với bếp.
- Lịch khách và `no_dish` cần thống nhất với quyết định của PO.
- Tôi làm phần khách và hỗ trợ tích hợp; bếp hai lò vẫn là lát Q4.
- Nguồn: [spec Q3 Phase 2](../../specs/001-p2-q3-day-customers/spec.md).

## 7. Phase 2 — lọc món và lịch khách

- `menu_filter=None` cho phép toàn menu; tập rỗng biểu thị không có món trong kế hoạch.
- Danh sách món tiếp tục được lọc theo khả năng đáp ứng recipe từ kho khả dụng.
- Số lượng trong kế hoạch là mục tiêu hiển thị theo PO #10, không phải quota bán.
- Khách đến theo các mốc được cấu hình; PO #11 mô tả lịch 120 + 900·k.
- Nếu bàn đầy, lượt đến bị bỏ qua và không tích lũy thành backlog.
- Nếu có bàn nhưng không có món khả thi, Quán phát `no_dish {}`.
- Trong trường hợp đó không tạo khách, không cấp ID khách và ca vẫn tiếp tục.
- Test dùng keyword `menu_filter` để tránh nhầm tham số inventory.
- Bằng chứng: [no_dish tests](../../tests/test_p2_q3_no_dish.py), [clarify](../clarify.md).

## 8. Phase 2 — tích hợp DaySim

- DaySim bàn giao kho Gather cho Quan trong cùng phiên mô phỏng.
- Tôi kiểm tra việc áp dụng filter kế hoạch vào ca Quán.
- Kế hoạch rỗng được truyền thành tập rỗng, tránh mở toàn bộ menu ngoài kế hoạch.
- Uy tín cấp Day được truyền vào ca và giữ lại sau khi ca kết thúc.
- `sim_tick` được tách khỏi outer tick để đứng yên khi pause.
- Phase tick và thời gian còn lại cũng được kiểm tra trong trạng thái tạm dừng.
- Kho cá thể và bộ cấp ID được kiểm tra khi chuyển qua ngày tiếp theo.
- Năm expected failures cũ được chuyển thành test thường sau khi sửa lỗi tương ứng.
- [Test tích hợp](../../tests/test_p2_q3_day_integration.py) và [headless Day](../proof/phase-4/day-headless-run.txt) ghi các trường hợp này.

## 9. Phase 2 — review Q4-F1

- Q3 và Q4 cùng hoạt động trong `quan.py`, nên vòng đời đơn phải nhất quán.
- Tôi tái hiện khách rời khi món đang nấu; món tiếp tục nấu và có thể được nhấc lên.
- Finding ban đầu chỉ chứng minh món mồ côi, chưa chứng minh cách xử lý sau đó.
- PO #13 chốt tạm: món được giao cho khách khác chờ đúng loại, không hoàn nguyên liệu đã nấu.
- Reservation chưa tiêu của khách nhận phải được giải phóng khi giao món.
- Tôi bổ sung fix và [integration test](../../tests/test_p2_q4_f1_reuse.py) cho đường dùng lại.
- Test kiểm tra item ID còn lại, state `eating`, reservation và một lần thanh toán.
- [Review gốc](../proof/phase-1/q3/q4-review.md) là finding kỹ thuật, không phải phê duyệt GitHub.
- Review chính thức phần bếp và phục vụ vẫn cần chủ Q4 xác nhận nếu chưa có bằng chứng mới.

## 10. Phase 2 — kết quả kiểm thử

- Unit test kiểm tra chọn món, lượt đến, bàn đầy và `no_dish`.
- Integration test ghép DaySim với QuanSim và kiểm tra các lần chuyển pha.
- Headless Day 1 và Day 3 có log mã thoát 0 ở lần chạy được ghi.
- Replay Day 3 trong log có SHA-256 trùng nhau.
- [Verification Phase 2](../verification/phase-2.md) phân biệt kết quả kỹ thuật và review còn chờ.

## 11. Phase 3 — thay đổi contract kho

- Contract v1.2 chuyển kho từ số lượng theo loại sang các cá thể `{id, kind, fresh}`.
- ID giúp reservation chỉ rõ nguyên liệu nào đang được giữ hoặc đã được tiêu thụ.
- Độ tươi ảnh hưởng tới khả năng sử dụng và giá món khi nấu.
- Manifest v1.3 tiếp tục dùng mô hình kho cá thể và bổ sung lệnh bench/soak.
- Việc chuyển schema ảnh hưởng Gather, file kho, Quan, DaySim và client.
- [ADR kho cá thể](../adr/0002-kho-ca-the.md) ghi quyết định và trách nhiệm các module.
- Tôi tập trung vào kho Quán, reservation Q3 và các điểm tích hợp cần thiết.

## 12. Phase 3 — cơ chế độ tươi

- Tuning quy định độ tươi ban đầu, tốc độ hao và ngưỡng nguyên liệu ươn.
- Trong Quán, độ tươi giảm 0,25 điểm mỗi giây theo cấu hình Phase 3.
- Với 60 tick mỗi giây, lượng giảm mỗi tick là 1/240 điểm.
- `Fraction` giúp phép tính và so sánh ngưỡng ổn định hơn so với cộng float liên tục.
- Khi item vượt qua ngưỡng ươn, Quán phát `spoiled` theo ID.
- Test kiểm tra thứ tự event và tránh phát lại cho cùng lần vượt ngưỡng.
- Khi Day bị pause, test kiểm tra thời gian mô phỏng và độ tươi không giảm.
- Nguồn: [test freshness](../../tests/test_p3_q3_freshness.py) và [verification P3](../verification/phase-3.md).

## 13. Phase 3 — reservation theo ID

- Mỗi recipe phải được giữ đủ nguyên liệu trước khi xem reservation là hợp lệ.
- Hệ thống chọn item sử dụng được có độ tươi cao hơn trước.
- Các item bằng độ tươi được xét theo thứ tự ID ổn định.
- Reservation nguyên khối tránh giữ một phần recipe khi chưa đủ nguyên liệu.
- Một ID vật lý không được giữ cho nhiều khách đồng thời.
- Consume trừ nguyên liệu khi nấu; release chỉ bỏ quyền giữ chưa tiêu.
- Test idempotency kiểm tra thao tác lặp không tạo thêm kho hoặc tiêu thụ hai lần.
- [Commit Q3 P3](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/4a89104) chứa implementation và test liên quan.

## 14. Phase 3 — spoil, retry và tích hợp

- Khi item đã giữ bị ươn, reservation cũ được giải phóng toàn bộ.
- Hệ thống thử chọn lại recipe một lần bằng các item còn sử dụng được.
- Nếu không đủ, khách vẫn chờ, reservation rỗng và đơn đánh dấu `unfulfillable`.
- Payload `{customer_id, table_id, dish_id}` là đề xuất, chưa có xác nhận PO/Integrator ở clarify #16.
- Test kiểm tra retry thất bại, không mất kho và không phát xử lý lặp.
- [Test v1.3](../../tests/test_p3_v13_integration.py) kiểm tra Gather → file → Quan giữ ID và độ tươi.
- Test kho Day kiểm tra handoff và cấp ID tiếp tục qua ngày.
- Test giá của Q4 được chạy trong regression; logic giá là phần Kiên phụ trách.

## 15. Phase 4 — mục tiêu soak

- AC-P4-03 yêu cầu chạy nhiều ngày trong một tiến trình với DaySim thực.
- Kết quả gồm số ngày yêu cầu, ngày hoàn thành, crash và dữ liệu từng ngày.
- Các lần cùng seed được so sánh trên các trường gameplay.
- Thời gian thực thi là phép đo thời gian thực và không đưa vào so sánh replay.
- Phần bench FPS và đóng gói do các thành viên khác phụ trách.
- Nguồn: [spec soak](../../specs/003-p4-q3-soak/spec.md).

## 16. Phase 4 — thiết kế soak

- CLI nhận `--seed`, `--days` và `--out`; số ngày phải dương.
- Bot gửi `interact` lúc bắt đầu Gather để cập bến nhanh.
- Quan chạy theo luật mô phỏng mà không có thao tác điều khiển bổ sung.
- Bot gửi `shop_done` khi vào Shop để tiếp tục ngày kế tiếp.
- Tuning được sao chép và kế hoạch D1–D5 được lặp cho D6–D10.
- Kết quả ngày được ghi sau khi Shop kết thúc, từ số liệu DaySim quan sát được.
- Exception được ghi vào diagnostics; lỗi chạy hoặc ghi file trả mã khác 0.
- Bot đơn giản giúp kiểm tra vòng đời mà không phụ thuộc chiến lược chơi phức tạp.

## 17. Phase 4 — kết quả soak

- Hai lần chạy seed 7 ghi `days_completed=10` và `crashes=0`.
- Các trường `days`, `days_completed`, `crashes` và `results` khớp nhau.
- `earned=0` là quan sát thật vì bot cập bến nhanh và không thu hoạch.
- Kết quả chứng minh vòng đời ổn định dưới policy này, chưa đánh giá cân bằng kinh tế.
- Soak không thay thế benchmark FPS hoặc nghiệm thu gameplay của QA.
- Bằng chứng: [lần 1](../proof/phase-4/soak-q3-run1.json), [lần 2](../proof/phase-4/soak-q3-run2.json), [test](../../tests/test_p4_soak.py).

## 18. Tổng hợp kiểm thử và bằng chứng

| Hạng mục | Phương pháp | Kết quả được ghi | Bằng chứng |
|---|---|---|---|
| Q3 P1/P2 | Unit và fixture | Có kiểm tra lifecycle và no_dish | [Q3 P1](../../tests/test_p1_q3.py), [P2](../../tests/test_p2_q3_no_dish.py) |
| Q3/Q4 | Integration scenario | Kiểm reuse và một lần thanh toán | [Q4-F1](../../tests/test_p2_q4_f1_reuse.py) |
| Day và v1.3 | Integration/headless | Kiểm pause, handoff, ID và freshness | [Day](../../tests/test_p2_q3_day_integration.py), [v1.3](../../tests/test_p3_v13_integration.py) |
| Freshness | Unit test item thật | Kiểm spoil, retry và reservation | [test](../../tests/test_p3_q3_freshness.py) |
| Soak | Hai lần chạy seed 7 | 10/10 ngày, 0 crash, gameplay khớp | [lần 1](../proof/phase-4/soak-q3-run1.json), [lần 2](../proof/phase-4/soak-q3-run2.json) |
| Q3 regression | Full unittest trên cây sau tích hợp Q3 | 216 test OK | [log Q3](../proof/phase-4/q3-full-regression.txt) |
| Verifier mới hơn | Phase 1 verifier ở `d354cdf` | 225 test OK; 9/9 bước | [log theo commit](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/blob/c25199a/docs/proof/phase-1/verify-run.txt) |
| Headless | Day 1/3 và replay | Exit 0; Day 3 trùng byte | [log](../proof/phase-4/day-headless-run.txt) |
| Quy ước | `check_rules.py` trong vòng Q3 trước | Exit 0, 0 lỗi quy ước; có mục cần xem | Kết quả được ghi trong lịch sử phiên kiểm chứng |

- 216 và 225 là hai lần đo ở các cây khác nhau; không cộng hoặc gán về cùng một commit.
- Log 225 nêu commit `d354cdf`, thời điểm 2026-11-21 10:24 UTC; `main` hiện có thể đã đi tiếp.
- Không khẳng định đã chạy lại 225 test trên HEAD báo cáo này.

## 19. Quy trình AI-SDLC và Git

- Tôi đối chiếu phân công, contract và câu hỏi PO trước khi viết hoặc điều chỉnh test.
- Spec Kit ghi yêu cầu, kế hoạch, test plan và handoff cho Q3 Phase 2–4.
- Scenario và fixture cho phép kiểm tra phần khách độc lập trong lúc module khác tiến triển.
- Integration test sau đó kiểm tra ranh giới thật giữa Day, Quán và kho.
- Regression và proof ghi kết quả, giới hạn và các lỗi còn phụ thuộc xác nhận.
- [PR #8](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/pull/8), [#14](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/pull/14), [#17](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/pull/17) và [#18](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/pull/18) là các mốc tích hợp được lịch sử Git ghi nhận.
- Việc merge và bằng chứng kỹ thuật được báo cáo tách khỏi phê duyệt QA.

## 20. Sử dụng AI

- Nhật ký ghi Codex/GPT-6 hỗ trợ phân tích checkout, code Q3, test, đối chiếu và tài liệu.
- Các kết quả AI được đối chiếu lại với code, contract và đầu ra kiểm thử.
- Nhật ký ghi lượng token không đo được; báo cáo không suy diễn con số.
- Bằng chứng: [ai-usage-log](../ai-usage-log.md).

## 21. Vấn đề và cách xử lý

- **Event thanh toán:** AI kiểm `paid.amount`, nhưng code phát `price` và `tip`.
- Tôi đọc `_tick_customers()`, sửa assertion theo output và chạy lại test tích hợp.
- **DaySim:** test trước đó ghi năm expected failures liên quan filter, reputation và pause.
- Tôi sửa giao diện DaySim/Runner, giữ các test và chạy lại regression sau thay đổi.
- **Giá theo freshness:** oracle ban đầu bỏ qua độ tươi hao trước tương tác.
- Tôi đối chiếu thứ tự tick và chỉnh kỳ vọng test theo `1/240` điểm mỗi tick.
- Mỗi tình huống nhấn mạnh việc tìm nguyên nhân trước khi thay assertion.
- Log và bối cảnh được ghi trong [nhật ký AI](../ai-usage-log.md) và [test Day](../../tests/test_p2_q3_day_integration.py).

## 22. Bài học cá nhân

- Tôi học cách dùng contract làm điểm chung khi các lát được phát triển song song.
- Replay cùng seed giúp phân biệt lỗi logic với thay đổi do nguồn ngẫu nhiên.
- Khi schema thay đổi, tôi cần kiểm tra cả fixture, validator, file kho và nơi tiêu thụ.
- Review chéo giúp phát hiện tình huống không nằm trong happy path của từng lát.
- Tôi cần kiểm tra kết quả AI bằng chứng cứ, kể cả khi code hoặc test trông hợp lý.
- Tôi ghi rõ điểm chưa được PO/QA xác nhận để việc bàn giao không gây hiểu nhầm.

## 23. Đối chiếu công việc với trạng thái

| Phase | Công việc sở hữu | Đã thực hiện | Bằng chứng | Trạng thái |
|---|---|---|---|---|
| 1 | Khách và reservation | Logic, fixture, replay | [Q3 proof](../proof/phase-1/q3/README.md) | Kỹ thuật có test; Contract D còn câu hỏi |
| 2 | Lọc món, lịch, no_dish | Tích hợp Day và Q4-F1 | [test Day](../../tests/test_p2_q3_day_integration.py) | Đã merge PR #18; review Q4 cần xác nhận |
| 3 | Freshness và giữ theo ID | Decay, spoil/retry, v1.3 | [test P3](../../tests/test_p3_q3_freshness.py) | Có test; schema event còn chờ duyệt |
| 4 | AC-P4-03 soak | CLI, test và hai lượt replay | [proof](../proof/phase-4/soak-q3-run1.json) | Kỹ thuật có proof; QA/Integrator cần xác nhận |

## 24. Hạn chế và phần cần xác nhận

- PRD-0/Test Contract gốc chưa có đủ trong checkout để chốt mọi semantics Contract D.
- `unfulfillable` vẫn là payload đề xuất theo clarify #16, không tự nhận đã duyệt.
- Review owner Q4 và nghiệm thu QA/Integrator cần được xác nhận bằng review thực tế.
- Proof HUD v1.2 đã có; không suy diễn thành review UI v1.3 mới.
- Bản phản tư ngôi thứ nhất là nội dung trình bày cho Quốc; trải nghiệm cá nhân cần Quốc xác nhận.

## 25. Kết luận cá nhân

Tôi đóng góp vào vòng đời khách, reservation và kiểm thử giao diện giữa khách với bếp qua bốn Phase.
Phần việc phát triển từ kho đếm và scenario Q3 sang kho cá thể, tích hợp DaySim và soak nhiều ngày.
Kết quả được hỗ trợ bằng code, test và proof, đồng thời các điểm cần PO và QA xác nhận được giữ rõ ràng.

Qua dự án, tôi thấy AI-SDLC có giá trị khi yêu cầu, implementation và bằng chứng được liên kết với nhau.
Tôi sẽ tiếp tục dùng kiểm thử và review chéo để kiểm tra giả định, nhất là khi nhiều module cùng thay đổi contract.
Việc giải thích giới hạn của kết quả cũng quan trọng đối với bàn giao và bảo trì sau này.
