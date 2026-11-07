# P24 — Hướng dẫn kiểm thử thủ công (snapshot chỉ đọc)

## P24-07 — Premium visual identity và avatar after login — MANUAL VERIFICATION REQUIRED

Đợt này không seed, reset, migration, hay thay đổi dữ liệu P22/MySQL. Các thay đổi UI chỉ dùng dữ liệu API hiện có. Browser walkthrough dưới đây là bằng chứng bắt buộc; lint/build không thay thế screenshot hoặc thao tác thực tế.

## P24-08 — Purchase Order operational workspace — MANUAL VERIFICATION REQUIRED

Dot nay chi thay doi React/CSS va doc cac API hien co. Khong approve, receive, cancel, tao PO, seed, reset, hay sua MySQL/P22 trong luc kiem thu giao dien.

### Q.1 Kiem tra bang Purchase Orders (chi doc)

- **Trang:** Purchase Orders. Tim `SIM_M5_CA1_FOODS_V1-PARTIAL`.
- **Ky vong:** hang hien PO number, supplier name + code neu co, status **In transit**, Fulfillment `6 / 8 received`, `2 remaining`, ngay expected arrival (hoac `Not scheduled`), so line va Actions theo thu tu **Manage** roi workflow action neu co.
- **PASS:** Fulfillment lay tong tu PO items, khong tao cot so qua hep; hover/focus va Manage/workflow cu van hoat dong. ResultCount la mot summary surface goc 11px, khong phai pill status badge.
- **Evidence:** screenshot bang da loc va ResultCount; khong click workflow action.

### Q.2 Controlled partial receipt — baseline truoc mutation

- **Trang/Thao tac:** o PO `SIM_M5_CA1_FOODS_V1-PARTIAL`, click **Manage**. Chi quan sat, sau do **Close**.
- **Ky vong UI truoc mutation:** Product hien `Food Item 2-006` va `FOODS_2_006`, status **In transit**, Ordered **8**, Received **6**, Remaining **2**. Inventory context hien On-hand **9**, Incoming **2**, Position **11**. Truong **Receive now** co label ro rang, max **2**, va dong giai thich receipt.
- **PASS:** khong co `Product #22`, modal khong can horizontal scroll o desktop cho PO mot line; Escape, click outside, focus keyboard va Close van hoat dong. Khong co API mutation khi chi mo/dong modal.
- **Evidence:** screenshot modal desktop, screenshot mobile hep neu co, va Network khong co `POST /receive`.

### Q.3 Controlled receipt — COMPLETED MANUALLY

- **Status:** owner da da thuc hien dung mot lan controlled receipt 2 units. Khong repeat, reset, hay restore baseline partial.
- **Current expected UI/DB:** status **RECEIVED**; Ordered **8**, Received **8**, Remaining **0**; On-hand **11**, Incoming **0**, Position **11**; dung mot stock transaction **RECEIPT** quantity **2**. Receipt controls va Cancel khong hien, completed fulfillment state hien thi.
- **Evidence:** giu screenshot/network/database evidence cua thao tac da hoan thanh. Moi test confirmation moi phai dung fixture/mock hoac cancel truoc final confirmation.

### Q.4 Linked recommendation va responsive states (chi doc)

- **Trang:** mo `SIM_M5_CA1_FOODS_V1-LINKED-DRAFT` bang **Manage**.
- **Ky vong:** overview hien `Linked recommendation #<id>` voi status/approved quantity neu API da tai; DRAFT chi hien Save line/Remove, khong hien receipt control. PO RECEIVED hien completed state va khong hien receipt input.
- **Responsive/a11y:** kiem tra 1280px, 760px va 480px: metadata grid stack an toan, line item thanh card doc duoc, action reachable, dialog nam trong viewport. Bat Reduced Motion: thong tin/progress van hien, khong co motion khong can thiet.
- **Evidence/PASS:** screenshot linked draft, completed PO neu da co san, va mot viewport hep. Khong danh dau browser PASS neu chua co cac anh nay.

## P24-08b — Confirmation dialog va timestamp local — MANUAL VERIFICATION REQUIRED

Baseline da thay doi hop le sau controlled receipt cua owner. **Khong** receive lai, reset, seed, hay khoi phuc PO `SIM_M5_CA1_FOODS_V1-PARTIAL`. PO nay phai la **RECEIVED**, Ordered **8**, Received **8**, Remaining **0**, On-hand **11**, Incoming **0**, Position **11**.

### P24-08b.1 Confirmation dialog (khong mutation)

- **Trang:** Purchase Orders. Mo mot DRAFT PO de thu **Remove**, va mot PO co the cancel de thu **Cancel purchase order**; dong dialog bang Cancel/Keep action hoac Escape. Khong xac nhan action destructive trong buoc nay.
- **Ky vong:** khong co browser dialog `localhost:5173 says`. Thay vao do la app dialog co backdrop, icon, title, mo ta ro rang, secondary Keep/Cancel va danger action. Escape/backdrop huy dialog; focus keyboard hien ro; Reduced Motion khong co motion thua.
- **Receipt:** neu co PO IN_TRANSIT khac an toan cho manual test, click **Confirm receipt** chi mo dialog. Dialog phai liet ke so units, product/SKU neu co, va giai thich on-hand tang/incoming giam/audited transaction. Click Cancel khong gui `POST /receive`.
- **Evidence/PASS:** screenshot moi loai dialog va Network cho Cancel. Khong danh PASS neu co native confirm hoac API mutation truoc final Confirm.

### P24-08b.2 Timestamp local va date-only

- **Trang:** Inventory → Transaction History. Tim receipt vua co cua `FOODS_2_006`.
- **Ky vong:** neu stored value la gan `2026-11-07 15:02:23 UTC`, browser o Asia/Ho_Chi_Minh hien gan `Nov 7, 2026, 10:02 PM` theo locale browser. Khong cong them 7 gio trong UI; timezone browser quyet dinh ket qua.
- **Kiem tra them:** PO Manage cho Received at, Inventory Updated, va Restock Recommendation expiry (neu co) deu dung local browser time. Sale date, order date, expected arrival, va forecast date van la calendar date, khong bi dich ngay.
- **Evidence/PASS:** screenshot Transaction History va Received at, kem browser timezone/locale neu co. **FAIL:** receipt hien 3:02 PM o Vietnam, date-only bi dich ngay, hoac invalid value lam crash UI.

### Avatar sau logout/login

- **Baseline:** dùng chính tài khoản Manager đã có avatar; không ghi email, password, cookie hoặc tên file upload vào evidence.
- **Thao tác:** Logout bằng sidebar, đăng nhập lại cùng tài khoản, rồi quan sát ngay avatar ở sidebar và trang **My Account** mà không hard refresh. Sau đó refresh một lần, rồi Remove photo để kiểm tra fallback.
- **Kỳ vọng:** response login đã có `avatar_url` an toàn dạng `/uploads/avatars/<generated-name>`; avatar hiển thị ngay, không cần timer hoặc refresh. Remove photo trả initials/UserRound ở cả hai vị trí và lần login sau vẫn fallback.
- **PASS/Evidence:** screenshot ngay sau login (sidebar), Account ngay sau login, sau refresh và sau Remove. **FAIL:** avatar chỉ hiện sau refresh, `/uploads` 404, URL lộ filesystem path, hoặc Logout thay đổi role/account khác.

### Premium identity trên tám trang

- **Trang/viewport:** Dashboard, Products, Inventory, Suppliers, Purchase Orders, Sales, Forecasts, Inventory Insights, My Account; chụp desktop và một viewport hẹp. Không tạo PO/sale/receipt cho kiểm tra thị giác.
- **Thao tác:** kiểm tra heading icon/hierarchy, table header/row/badge, actions, loading/empty/error hiện có; hover/focus bằng bàn phím; bật `prefers-reduced-motion` nếu có. Mở một modal hiện có rồi đóng bằng Escape/close, không submit.
- **Kỳ vọng:** canvas #F6F8FC, heading navy rõ, blue #2563EB có mục đích; icon semantic nhất quán; warning/risk dùng amber/red tiết chế; table vẫn đọc được, active sidebar ribbon và responsive drawer giữ nguyên.
- **PASS/Evidence:** screenshot Dashboard, Products, Suppliers, Forecasts, Inventory Insights, Account và một modal/focus/reduced-motion khi có thể. **FAIL:** contrast yếu, layout/table clip, focus không rõ, motion rõ khi reduced motion, hoặc sidebar/route thay đổi.

### Forecast target-period trong Inventory Insights

- **Trang:** Inventory Insights. Chọn một SKU M5 có decision, ví dụ `FOODS_1_001`; chỉ mở **View insight**, không tạo recommendation.
- **Thao tác:** ghi Available, Incoming, Inventory position, lead-time demand, safety stock, reorder point, target stock, recommended order. Mở **How was this calculated?**.
- **Kỳ vọng:** Demand coverage có lead-time demand và `Forecast demand across N-day target period`; `N = lead time + fixed one-day review period`. Giá trị persisted phải giải thích: inventory position = on-hand + incoming; reorder point = lead-time demand + safety stock; target stock = target-period demand + safety stock. Không có mutation khi mở insight.
- **PASS/Evidence:** screenshot detail/calculation mở, có SKU/giá trị nhưng không lộ secret. **FAIL:** UI tự tính giá trị khác API, thiếu review day, hoặc mở insight đã tạo recommendation/PO/mutation.

## P24-06 — My Account, avatar và mật khẩu — MANUAL VERIFICATION REQUIRED

Đợt này thêm Account self-service và migration metadata nullable. **Không dùng P22 product/PO/sale để kiểm tra.** Chỉ dùng chính tài khoản Manager đang đăng nhập; không chụp hoặc ghi password, cookie, token hay đường dẫn filesystem.

### Account navigation and profile

- **Trang bắt đầu:** bất kỳ trang protected nào, ví dụ Dashboard. Click avatar/tên/role ở sidebar. Thu sidebar desktop rồi hover/focus avatar để xác nhận tooltip **My Account**; click để mở `/account`. Trên mobile drawer, mở profile và kiểm tra Logout là nút riêng.
- **Kỳ vọng UI:** header **My Account**, identity card có tên/email/role, Profile Information và Security. Role/email read-only. Avatar/sidebar không làm thay đổi active ribbon.
- **PASS/Evidence:** profile route mở được, tooltip chỉ ở collapsed desktop, focus rõ, layout không clip ở mobile. Chụp Account desktop, collapsed tooltip và viewport hẹp. FAIL nếu avatar không clickable, Logout vô tình điều hướng Account, hoặc role/email editable.

### Safe display-name and avatar checks

- **Baseline:** ghi lại tên và có/không avatar trước khi thử. Không thay email/role. Dùng ảnh JPEG/PNG/WEBP vô hại nhỏ hơn 3 MB, không phải dữ liệu P22.
- **Thao tác:** nhập tên hợp lệ có khoảng trắng đầu/cuối, bấm **Save profile**, refresh. Sau đó **Change photo**, refresh và xem sidebar expanded/collapsed; bấm **Remove** và refresh. Thử SVG hoặc file sai định dạng để xác nhận thông báo lỗi rõ ràng.
- **Kỳ vọng UI/DB:** tên được trim và đồng bộ identity/sidebar. `role`, `is_active`, `password_hash` không đổi. Avatar hợp lệ hiện ở identity/sidebar; `users.avatar_filename` là generated filename nullable, API chỉ trả `/uploads/avatars/<generated-name>`, Remove trả về fallback và DB `NULL`.
- **PASS/Evidence:** JPEG/PNG/WEBP ≤3 MB thành công; SVG/malformed/oversize bị từ chối; không có path thật/binary/secret trong UI/evidence. Chụp avatar desktop/collapsed/mobile.

### Password and session policy

- **Baseline:** mở hai session trình duyệt riêng cho cùng account (normal + private), ghi nhận cả hai vào được Dashboard. Không ghi password vào tài liệu evidence.
- **Thao tác:** ở session A nhập current password, new password (ít nhất 8 ký tự và một uppercase), confirmation giống nhau → **Change password**. Xác nhận session A tiếp tục vào Account/Dashboard; refresh protected page ở session B; thử login lại bằng mật khẩu cũ và mới.
- **Kỳ vọng UI/DB:** session A còn hợp lệ; session B bị yêu cầu đăng nhập; mật khẩu cũ bị từ chối, mật khẩu mới được chấp nhận. Chỉ `users.password_hash` đổi; `auth_sessions` khác có `revoked_at`, session hiện tại không bị revoke. Form clear sau success; không có password/secret trong UI, URL, toast hoặc log.
- **PASS/Evidence:** screenshot Account success và session-B redirect/error, che toàn bộ password input. FAIL nếu session hiện tại logout, session khác vẫn hợp lệ, hoặc mật khẩu cũ dùng được.

### P24-06b Avatar delivery và sidebar profile card

- **Upload/persistence:** chọn một JPEG/PNG/WEBP hợp lệ dưới 3 MB. Sau toast thành công, xác nhận ngay **cùng ảnh** xuất hiện trên Account và sidebar, không logout/reload; sau đó refresh browser và xác nhận vẫn thấy ảnh. Bấm **Remove** và xác nhận `avatar_url` về null cùng fallback initials/UserRound ở cả hai vị trí.
- **Expanded/mobile card:** với sidebar mở, xác nhận avatar, Display Name, Manager role và Logout nằm trong một surface navy đủ rộng, không phải name pill nhỏ hoặc Logout tách rời. Avatar/name/role/account portion mở `/account`; Logout chỉ logout, không điều hướng Account. Lặp lại ở mobile drawer.
- **Collapsed desktop:** chỉ còn avatar; không tail/logout bị clip. Hover/focus hiện tooltip **My Account**; click avatar mở `/account`.
- **Evidence/PASS:** chụp sau upload ở Account + expanded sidebar, sau refresh, sau Remove fallback, profile card mobile và collapsed tooltip/navigation. FAIL nếu ảnh không xuất hiện ngay, refresh mất ảnh, click Logout vào Account, hoặc `/uploads` URL bị 404 trên Vite dev server.

Trạng thái: `IN_PROGRESS` — tài liệu này là hướng dẫn kiểm thử browser; không phải bằng chứng browser đã hoàn tất.

## A. Snapshot cơ sở dữ liệu đã xác minh (chỉ đọc)

Ngày chụp: 2026-11-07. Dữ liệu dưới đây được truy vấn trực tiếp từ MySQL local, không đọc CSV M5 thô và không thay đổi bất kỳ bản ghi nào.

- Scenario: `SIM_M5_CA1_FOODS_V1` (ID 1), store `CA_1`, lịch sử `d_1`–`d_1913`, 36 SKU.
- Selection SHA-256: `2284aced3531888a0d4b38cd6a7216fcd2c6e1aaae3773b6456c168e6ddc9e95`.
- Sales quan sát M5: 68,868 dòng, từ 2011-01-29 đến 2016-04-24.
- Forecast: run ID **18**, `XGBOOST_V1`, `FEATURE_SET_V1`, origin 2016-04-24, horizon 28; 1,008 dòng dự báo đã lưu.

### Danh mục, tồn kho và mapping nhà cung cấp

`SL về` là incoming quantity; `Vị trí` = on-hand + incoming. Mapping hiển thị là supplier preferred của scenario (`SUP_01/02/03`) và lead time thực tế trong MySQL.

| ID | SKU | Tên hiển thị | On-hand | SL về | Vị trí | Supplier / lead | Rủi ro | Safety | Target | Đề xuất |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 4 | FOODS_1_001 | Food Item 1-001 (M5 simulation) | 0 | 0 | 0 | SUP_01 / 3d | STOCKOUT_RISK | 4 | 8 | 8 |
| 5 | FOODS_1_002 | Food Item 1-002 (M5 simulation) | 0 | 0 | 0 | SUP_02 / 4d | STOCKOUT_RISK | 3 | 6 | 6 |
| 9 | FOODS_1_003 | Food Item 1-003 (M5 simulation) | 0 | 0 | 0 | SUP_03 / 5d | STOCKOUT_RISK | 4 | 8 | 8 |
| 10 | FOODS_1_004 | Food Item 1-004 (M5 simulation) | 0 | 0 | 0 | SUP_01 / 6d | STOCKOUT_RISK | 0 | 1 | 1 |
| 11 | FOODS_1_005 | Food Item 1-005 (M5 simulation) | 0 | 0 | 0 | SUP_02 / 7d | STOCKOUT_RISK | 5 | 16 | 16 |
| 12 | FOODS_1_006 | Food Item 1-006 (M5 simulation) | 0 | 0 | 0 | SUP_03 / 3d | STOCKOUT_RISK | 5 | 12 | 12 |
| 13 | FOODS_1_008 | Food Item 1-008 (M5 simulation) | 1 | 0 | 1 | SUP_01 / 4d | REORDER_NEEDED | 2 | 3 | 2 |
| 14 | FOODS_1_009 | Food Item 1-009 (M5 simulation) | 1 | 0 | 1 | SUP_02 / 5d | REORDER_NEEDED | 0 | 1 | 0 |
| 15 | FOODS_1_010 | Food Item 1-010 (M5 simulation) | 2 | 0 | 2 | SUP_03 / 6d | REORDER_NEEDED | 3 | 5 | 3 |
| 16 | FOODS_1_011 | Food Item 1-011 (M5 simulation) | 8 | 0 | 8 | SUP_01 / 7d | REORDER_NEEDED | 5 | 14 | 6 |
| 17 | FOODS_1_012 | Food Item 1-012 (M5 simulation) | 9 | 0 | 9 | SUP_02 / 3d | REORDER_NEEDED | 6 | 18 | 9 |
| 18 | FOODS_1_013 | Food Item 1-013 (M5 simulation) | 10 | 0 | 10 | SUP_03 / 4d | REORDER_NEEDED | 9 | 21 | 11 |
| 6 | FOODS_2_001 | Food Item 2-001 (M5 simulation) | 23 | 0 | 23 | SUP_01 / 5d | OVERSTOCK_RISK | 4 | 10 | 0 |
| 7 | FOODS_2_002 | Food Item 2-002 (M5 simulation) | 31 | 5 | 36 | SUP_02 / 6d | OVERSTOCK_RISK | 5 | 15 | 0 |
| 19 | FOODS_2_003 | Food Item 2-003 (M5 simulation) | 23 | 0 | 23 | SUP_03 / 7d | OVERSTOCK_RISK | 4 | 10 | 0 |
| 20 | FOODS_2_004 | Food Item 2-004 (M5 simulation) | 22 | 0 | 22 | SUP_01 / 3d | OVERSTOCK_RISK | 5 | 10 | 0 |
| 21 | FOODS_2_005 | Food Item 2-005 (M5 simulation) | 6 | 8 | 14 | SUP_02 / 4d | OVERSTOCK_RISK | 3 | 6 | 0 |
| 22 | FOODS_2_006 | Food Item 2-006 (M5 simulation) | 9 | 2 | 11 | SUP_03 / 5d | OVERSTOCK_RISK | 3 | 6 | 0 |
| 23 | FOODS_2_007 | Food Item 2-007 (M5 simulation) | 12 | 0 | 12 | SUP_01 / 6d | HEALTHY | 7 | 12 | 0 |
| 24 | FOODS_2_008 | Food Item 2-008 (M5 simulation) | 1 | 0 | 1 | SUP_02 / 7d | REORDER_NEEDED | 0 | 1 | 0 |
| 25 | FOODS_2_009 | Food Item 2-009 (M5 simulation) | 6 | 0 | 6 | SUP_03 / 3d | REORDER_NEEDED | 3 | 6 | 0 |
| 26 | FOODS_2_010 | Food Item 2-010 (M5 simulation) | 8 | 0 | 8 | SUP_01 / 4d | HEALTHY | 4 | 8 | 0 |
| 27 | FOODS_2_011 | Food Item 2-011 (M5 simulation) | 8 | 0 | 8 | SUP_02 / 5d | HEALTHY | 4 | 8 | 0 |
| 28 | FOODS_2_012 | Food Item 2-012 (M5 simulation) | 8 | 0 | 8 | SUP_03 / 6d | HEALTHY | 4 | 8 | 0 |
| 8 | FOODS_3_001 | Food Item 3-001 (M5 simulation) | 9 | 0 | 9 | SUP_01 / 7d | HEALTHY | 4 | 9 | 0 |
| 29 | FOODS_3_002 | Food Item 3-002 (M5 simulation) | 1 | 0 | 1 | SUP_02 / 3d | REORDER_NEEDED | 0 | 1 | 0 |
| 30 | FOODS_3_003 | Food Item 3-003 (M5 simulation) | 6 | 0 | 6 | SUP_03 / 4d | REORDER_NEEDED | 3 | 6 | 0 |
| 31 | FOODS_3_004 | Food Item 3-004 (M5 simulation) | 10 | 0 | 10 | SUP_01 / 5d | REORDER_NEEDED | 5 | 10 | 0 |
| 32 | FOODS_3_005 | Food Item 3-005 (M5 simulation) | 7 | 0 | 7 | SUP_02 / 6d | HEALTHY | 3 | 7 | 0 |
| 33 | FOODS_3_006 | Food Item 3-006 (M5 simulation) | 8 | 0 | 8 | SUP_03 / 7d | HEALTHY | 4 | 8 | 0 |
| 34 | FOODS_3_007 | Food Item 3-007 (M5 simulation) | 34 | 0 | 34 | SUP_01 / 3d | HEALTHY | 7 | 34 | 0 |
| 35 | FOODS_3_008 | Food Item 3-008 (M5 simulation) | 1 | 0 | 1 | SUP_02 / 4d | REORDER_NEEDED | 0 | 1 | 0 |
| 36 | FOODS_3_009 | Food Item 3-009 (M5 simulation) | 7 | 0 | 7 | SUP_03 / 5d | HEALTHY | 3 | 7 | 0 |
| 37 | FOODS_3_010 | Food Item 3-010 (M5 simulation) | 9 | 0 | 9 | SUP_01 / 6d | HEALTHY | 4 | 9 | 0 |
| 38 | FOODS_3_011 | Food Item 3-011 (M5 simulation) | 34 | 0 | 34 | SUP_02 / 7d | HEALTHY | 11 | 34 | 0 |
| 39 | FOODS_3_012 | Food Item 3-012 (M5 simulation) | 17 | 0 | 17 | SUP_03 / 3d | HEALTHY | 8 | 17 | 0 |

Ngoài mapping preferred trên, các SKU FOODS_1_001, FOODS_1_002, FOODS_2_001, FOODS_2_002 và FOODS_3_001 còn có mapping `DEMO_SUPPLIER_A/B` không preferred. UI/engine phải chọn mapping preferred của scenario.

### Purchase orders và recommendations hiện có

| PO | Trạng thái | SKU | Đặt | Đã nhận | Còn lại |
| --- | --- | --- | ---: | ---: | ---: |
| SIM_M5_CA1_FOODS_V1-INCOMING | IN_TRANSIT | FOODS_2_005 | 8 | 0 | 8 |
| SIM_M5_CA1_FOODS_V1-PARTIAL | IN_TRANSIT | FOODS_2_006 | 8 | 6 | 2 |
| SIM_M5_CA1_FOODS_V1-COMPLETE | RECEIVED | FOODS_2_007 | 6 | 6 | 0 |
| SIM_M5_CA1_FOODS_V1-LINKED-DRAFT | DRAFT | FOODS_1_002 | 6 | 0 | 6 |

Recommendations: IDs 6 and 12 are `ACCEPTED` for FOODS_1_002 (6 approved); IDs 7 and 13 are `MODIFIED` for FOODS_1_003 (8 recommended, 7 approved). Recent audit evidence includes receipt IDs 40 and 44 for FOODS_2_006 (3 each), receipt ID 41 for FOODS_2_007 (6), and initial-stock adjustments with the `SIM_M5_CA1_FOODS_V1` marker.

### Sản phẩm đại diện P24 và tổng forecast 28 ngày

| Mục đích | SKU | Giá trị snapshot | Tổng forecast 28 ngày |
| --- | --- | --- | ---: |
| Healthy | FOODS_2_007 | on-hand 12, incoming 0, position 12, target 12 | 17.7864 |
| Reorder-needed | FOODS_1_008 | on-hand 1, position 1, safety 2, target 3, đề xuất 2 | 9.2323 |
| Stockout-risk | FOODS_1_001 | on-hand 0, position 0, safety 4, target 8, đề xuất 8 | 21.0583 |
| Overstock-risk / incoming | FOODS_2_005 | on-hand 6, incoming 8, position 14, target 6 | 11.5672 |
| Controlled sale | FOODS_3_012 | on-hand 17, position 17, target 17 | 71.1064 |
| Controlled receipt | FOODS_2_006 | on-hand 9, incoming 2, position 11; PO PARTIAL còn 2 | 9.5944 |

## B. Quy trình kiểm thử thủ công

Mỗi lần mutation phải ghi lại baseline mới trên UI/database trước khi bấm nút. Các con số snapshot ở trên chỉ đúng tại thời điểm chụp.

### 1. Tìm kiếm Products (không mutation)

- **Trang:** Products. **Baseline:** danh sách đủ 36 SKU scenario có thể thấy khi xóa tìm kiếm.
- **Thao tác:** click ô Search, gõ liên tục `FOODS_1` (không dừng giữa các ký tự); thử `Food Item 2-005`; sau đó xóa toàn bộ ô.
- **Kỳ vọng UI:** caret/focus luôn ở ô input; chỉ sau khoảng 300 ms bảng mới cập nhật; bảng cũ vẫn hiển thị với “Updating products…” trong lúc tải; `FOODS_1` trả 12 SKU FOODS_1; tên trả SKU tương ứng; xóa ô trả danh sách đầy đủ; tìm chuỗi không tồn tại hiện “No products found”.
- **PASS:** không remount/focus loss, không spinner toàn trang, API error hiện thông báo có nút Try again. **FAIL:** chỉ gõ được một ký tự, kết quả cũ quay lại sau kết quả mới, hoặc trang biến mất.
- **Evidence:** screenshot lúc `FOODS_1`, lúc empty result, và DevTools Network cho debounce nếu có.

### 2. Forecast và inventory insight (không mutation)

- **Trang:** Forecasts rồi Inventory Insights. **SKU:** `FOODS_1_001`.
- **Baseline:** forecast 28 ngày là 21.0583; stock 0, safety 4, target 8, đề xuất 8.
- **Thao tác:** chọn SKU và 28 days; mở Inventory Insights.
- **Kỳ vọng:** model `XGBOOST_V1`, feature set `FEATURE_SET_V1`, origin 2016-04-24; UI không được tạo model mới chỉ vì mở trang.
- **PASS:** số liệu quyết định nhất quán với snapshot/forecast đã lưu. **Evidence:** screenshot Forecasts và Insights.

### 3. Kiểm tra rủi ro và hàng về (không mutation)

- **Trang:** Inventory / Inventory Insights. **SKU:** `FOODS_2_005`.
- **Baseline:** available 6, incoming 8, position 14, risk `OVERSTOCK_RISK`, PO `SIM_M5_CA1_FOODS_V1-INCOMING` là IN_TRANSIT, 8/0/8.
- **Thao tác:** tìm SKU, mở PO tương ứng.
- **PASS:** tất cả số liệu khớp baseline; không nhận hàng khi chỉ xem. **Evidence:** screenshot Inventory và PO.

### 4. Linked draft PO (không mutation)

- **Trang:** Purchase Orders. **PO:** `SIM_M5_CA1_FOODS_V1-LINKED-DRAFT`.
- **Baseline:** DRAFT, FOODS_1_002, ordered 6, received 0, remaining 6; recommendation ID 6 hoặc 12 là ACCEPTED.
- **Thao tác:** mở Manage; kiểm tra liên kết/review information, sau đó Cancel/đóng modal, không submit.
- **PASS:** draft không tự làm tăng stock và không tự chuyển trạng thái. **Evidence:** screenshot PO detail và recommendation.

### 5. Partial receipt (mutation có kiểm soát)

- **Trang:** Purchase Orders. **PO:** `SIM_M5_CA1_FOODS_V1-PARTIAL`, SKU `FOODS_2_006`.
- **Baseline bắt buộc trước khi thao tác:** IN_TRANSIT; ordered 8, received 6, remaining 2; on-hand 9, incoming 2, position 11.
- **Thao tác:** nhận đúng quantity 2 một lần, xác nhận; không refresh/submit lại trong khi request đang chạy.
- **Kỳ vọng tính toán:** PO chuyển RECEIVED, received 8, remaining 0; on-hand tăng **9 → 11**, incoming **2 → 0**, position **11 → 11**; thêm một `RECEIPT` stock transaction quantity 2.
- **PASS:** đúng một receipt; refresh không nhân đôi. **FAIL:** nhận quá 2, stock không đổi, hoặc retry tạo receipt thứ hai.
- **Evidence:** screenshot trước/sau PO và Inventory, cùng transaction row mới. Lưu baseline mới vì snapshot ban đầu không còn đúng sau test này.

### 6. Controlled sale (mutation có kiểm soát)

- **Trang:** Sales. **SKU:** `FOODS_3_012`.
- **Baseline bắt buộc:** on-hand 17, incoming 0, position 17. Chọn ngày hiện tại, quantity **1**, source duy nhất dạng `P24-MANUAL-SALE-YYYYMMDD`.
- **Thao tác:** record sale một lần; không click lại khi nút loading.
- **Kỳ vọng tính toán:** on-hand/position giảm **17 → 16**; một stock transaction `SALE` quantity 1 và một operational sale với idempotency key được tạo; retry cùng request không được trừ thêm.
- **PASS:** một lần trừ kho duy nhất; historical M5 rows không bị sửa. **Evidence:** screenshot form/result, Inventory, Sales và transaction row.

### 7. API error/no-result recovery (không mutation)

- **Trang:** Products. **Thao tác:** tìm một chuỗi không tồn tại; sau đó dùng DevTools offline hoặc chặn request search rồi bấm Try again khi mạng lại bình thường.
- **Kỳ vọng:** no-result là thông báo thành công, không phải error; lỗi API là callout rõ ràng, input/bảng cũ còn mount và có Try again.
- **PASS:** khôi phục được mà không mất chuỗi đang gõ. **Evidence:** screenshot no-result và callout error.

## C. Phân loại bằng chứng

- **Đã xác minh:** mục A là snapshot MySQL chỉ đọc tại thời điểm ghi tài liệu.
- **Kỳ vọng sau hành động:** các biến đổi số học ở mục 5–6; phải đối chiếu lại sau thao tác, không dùng snapshot cũ thay cho kết quả mới.
- **Chưa xác minh browser:** toàn bộ thao tác UI, focus, API error handling, modal, receipt và sale phải do người dùng thực hiện/capture trong P24.

## D. P24-02 — Live reconciliation bổ sung (chỉ đọc, 2026-11-07)

Đây là kết quả truy vấn **current MySQL**, không suy luận lại từ snapshot P22 cũ.

- Đủ 36 `demo_product_sources`; cả 36 `products.unit` hiện là `unit`. Đây là **đơn vị đo**, không phải tồn kho. Bảng Products hiện hiển thị riêng `Unit of Measure` và `On-hand Stock` từ API inventory.
- Forecast run 18 có đúng 28 persisted rows cho mỗi SKU scenario. Tổng 7/14/28 ngày của sáu SKU đại diện:

| SKU | Risk hiện tại | On-hand + incoming = position | 7 ngày | 14 ngày | 28 ngày |
| --- | --- | --- | ---: | ---: | ---: |
| FOODS_1_001 | STOCKOUT_RISK | 0 + 0 = 0 | 5.8180 | 11.4284 | 21.0583 |
| FOODS_1_008 | REORDER_NEEDED | 1 + 0 = 1 | 1.5868 | 4.0268 | 9.2323 |
| FOODS_2_005 | OVERSTOCK_RISK | 6 + 8 = 14 | 3.3465 | 6.3171 | 11.5672 |
| FOODS_2_006 | OVERSTOCK_RISK | 9 + 2 = 11 | 2.7252 | 5.0193 | 9.5944 |
| FOODS_2_007 | HEALTHY | 12 + 0 = 12 | 4.2341 | 8.5596 | 17.7864 |
| FOODS_3_012 | HEALTHY | 17 + 0 = 17 | 16.8213 | 34.6650 | 71.1064 |

- PO lines/receipts vẫn khớp snapshot: incoming FOODS_2_005 8/0/8; partial FOODS_2_006 8/6/2; complete FOODS_2_007 6/6/0; linked draft FOODS_1_002 6/0/6.
- **Audit finding, not a repair:** 37 scenario stock transactions có `created_by_user_id=4`, nhưng 5 transaction có actor null; cả 4 reviewed recommendations có actor 4. Không sửa dữ liệu scenario trong P24-02. Khi browser/P24 kiểm thử receipt/sale mới, phải xác nhận actor server-bound khác null cho record mới.

## E. Bản đồ workflow đã kiểm thử tự động

| UI/API | Service/DB expectation | Isolated automated evidence |
| --- | --- | --- |
| Login/logout và protected writes | session, CSRF, role check | backend auth/session tests |
| Products / Suppliers | catalog + mapping persisted, không đổi stock | `test_business_api.py` |
| Adjustment | on-hand đổi một lần và `stock_transactions` audit | `test_business_api.py`, `test_inventory_decisions.py` |
| Record sale / retry | on-hand giảm một lần; key idempotency không double-sell | `test_sales_forecasts_api.py` |
| Historical CSV import | cập nhật `sales_daily`, không giảm stock | `test_sales_forecasts_api.py` |
| Forecasts | only eligible M5 SKU; 7/14/28 outputs | `test_sales_forecasts_api.py` |
| Recommendation / linked PO | review state, exactly one linked draft | `test_inventory_decisions.py`, `test_business_api.py` |
| Draft edit, transition, receipt | allowed state transitions only; partial receipt changes stock/incoming | `test_business_api.py` |
| UI loading/empty/error/retry | cached operational data stays mounted | frontend workflow/search tests |

Automated tests use isolated SQLite/disposable records and never mutate the P22 MySQL scenario. Browser workflows remain unverified until the owner captures the prescribed evidence.

## F. Quy ước bằng chứng — phải đọc trước khi bấm nút

- **P22 ORIGINAL BASELINE** là trạng thái scenario ngay sau khi P22 được áp dụng. Nó là chứng cứ lịch sử, **không** là dữ liệu để ghi đè hoặc “dọn sạch”.
- **CURRENT MYSQL SNAPSHOT** là kết quả truy vấn chỉ đọc lúc 2026-11-07, sau các công việc P24-01/P24-02. Những con số này có thể thay đổi sau một kiểm thử thủ công hợp lệ.
- **MANUAL TEST MUTATION** là thay đổi có chủ ý do người kiểm thử thực hiện. Trước mỗi mutation phải ghi baseline mới (giờ chụp, ID, số lượng, trạng thái); sau đó lưu ảnh và đối chiếu database. Không dùng baseline cũ để kết luận sau mutation.
- Các mục có nhãn **MANUAL VERIFICATION REQUIRED** chưa có bằng chứng browser trong môi trường Codex. Chúng không phải PASS và không được dùng làm khẳng định demo.

## G. Môi trường, an toàn và khởi động

### G.1 Nhận diện môi trường đúng

| Mục | Giá trị cần xác nhận |
| --- | --- |
| Branch | `experiment/inventory-control-room` |
| HEAD trước P24-02 | `8572592` (`fix(products): retain search focus during query updates`) |
| HEAD P24-02 hiện có khi viết hướng dẫn | `129c96f` (`fix(ui): reconcile catalog stock and supplier layout`) |
| Database | local MySQL `smart_inventory_market` (không ghi mật khẩu/URL vào ảnh hoặc tài liệu) |
| Scenario | `SIM_M5_CA1_FOODS_V1`, ID 1, store `CA_1`, 36 SKU |
| Selection hash | `2284aced3531888a0d4b38cd6a7216fcd2c6e1aaae3773b6456c168e6ddc9e95` |
| Test account | đăng nhập tài khoản local đang active có role `MANAGER`; chỉ xác nhận display name/role trên UI, không chụp hay ghi email/mật khẩu/token |

Khởi động trong hai terminal riêng, từ repository root:

```powershell
.\.venv\Scripts\uvicorn.exe backend.app.main:app --reload
Set-Location frontend
npm run dev
```

Trước khi kiểm thử, mở UI, kiểm tra tài khoản đang hiển thị `MANAGER`, rồi xác nhận scenario có 36 sản phẩm M5 và forecast run 18. Nếu bất kỳ dấu hiệu nào khác, dừng lại: có thể đang nối nhầm database hoặc API. Không chạy `setup_m5_supermarket_scenario.py --apply`, không reset/seed database, không sửa raw M5, forecast/model artifact hay P22 records để “khôi phục” trạng thái.

### G.2 CURRENT MYSQL SNAPSHOT — đối soát chỉ đọc

| Bảng/phạm vi | Count hiện tại | Ghi chú |
| --- | ---: | --- |
| `products` / `demo_product_sources` scenario | 36 / 36 | tất cả source kind `OBSERVED_M5` |
| `sales_daily` | 68,868 | 2011-01-29 đến 2016-04-24; không phải giao dịch POS 2026 |
| `forecast_runs` / `forecast_values` toàn DB | 11 / 1,456 | không xóa các run ngoài scenario |
| scenario forecast run 18 / values | 1 / 1,008 | 36 SKU × 28 ngày |
| `inventory` | 36 | một row cho mỗi scenario product hiện tại |
| `suppliers` / `supplier_products` | 5 / 41 | tất cả 5 supplier hiện active |
| `reorder_recommendations` | 15 | NEW 4, ACCEPTED 2, MODIFIED 2, EXPIRED 7 |
| `purchase_orders` / `purchase_order_items` | 5 / 5 | 4 PO có marker scenario; không suy ra PO thứ năm là P22 nếu không có marker |
| `stock_transactions` / `operational_sales` | 42 / 0 | chưa có manual sale mới trong snapshot |

Actor audit hiện tại: `ADJUSTMENT_IN` có 29 actor khác null và 5 actor null; `ADJUSTMENT_OUT` có 5 khác null; `RECEIPT` có 3 khác null; chưa có `SALE`. Năm row null là lịch sử/pre-existing, không được sửa lại. Mọi `SALE`, adjustment hoặc receipt mới phải có `created_by_user_id` của Manager đã đăng nhập; nếu null, ghi **FAIL** và mở defect riêng.

## H. Xác minh read-only trên tám trang

Mỗi case dưới đây là **MANUAL VERIFICATION REQUIRED** cho đến khi có ảnh/browser evidence. Trên từng trang: (1) tải lại bình thường, (2) dùng Tab/Shift+Tab để nhìn focus, (3) thử sidebar expanded/collapsed, (4) thu viewport desktop hẹp và mobile-like, (5) ghi nhận icon, badge, độ tương phản và không có horizontal overflow. Chỉ dùng DevTools Offline/chặn request trên bản local để thử lỗi; không gửi mutation khi network bị chặn.

| Trang | Data/API đối chiếu | Thao tác read-only và kết quả cần có |
| --- | --- | --- |
| Dashboard | inventory, decisions, recommendations, orders | Chỉ số/risk/PO phải phản ánh snapshot, không mock số liệu; loading/error/retry không che vĩnh viễn workspace. |
| Products | `/api/products`, `/api/inventory`, `/api/categories` | Xem H.1; Unit of Measure và On-hand Stock là hai dữ liệu khác nhau. |
| Inventory | `/api/inventory`, `/api/stock-transactions` | `FOODS_2_005` phải cho 6 on-hand, 8 incoming, position 14 trước mutation; transaction list không được tự thay đổi khi chỉ xem. |
| Suppliers | `/api/suppliers`, `/api/supplier-products` | Xem H.2; badge active, mapping và lead time không bị clip. |
| Purchase Orders | `/api/purchase-orders` | Xem H.4; không mở receipt/transition khi chỉ đối soát. |
| Sales | `/api/sales` | Filter lịch sử M5 chỉ đọc; import/record sale là mutation, tách ở I.1/I.2. |
| Forecasts | `/api/forecasts/latest`, `/api/forecast-runs`, `/api/forecasts/eligibility` | Xem H.3; không Generate forecast mới trong bước read-only. |
| Inventory Insights | `/api/inventory-decisions`, `/api/reorder-recommendations` | Xem H.3; badge risk và decision phải khớp data path thực tế. |

**Loading/empty/error:** “empty” không an toàn để tạo trên persistent scenario, vì vậy chỉ chấp nhận empty do search không tồn tại (`NO-SUCH-SKU-P24`) hoặc fixture isolated. Khi request thật lỗi, UI phải hiển thị lỗi rõ ràng + Retry; lỗi không được trông như thành công. Ghi screenshot riêng cho normal, error/retry và responsive; không đánh PASS chỉ vì lint/build pass.

### H.1 Products — focus, debounce, Unit of Measure và tồn kho

- **Current baseline:** `FOODS_1_001` ID 4: unit `unit`, on-hand **0**; `FOODS_2_007` ID 23: unit `unit`, on-hand **12**; `FOODS_1_008` ID 13: on-hand **1**. Không có product không có inventory row ở snapshot này (36 products/36 inventory); vì vậy không tự tạo “untracked” product chỉ để đạt case.
- **Thao tác:** vào Products; gõ liên tục `FOODS_1`, không dừng giữa các ký tự; tiếp theo gõ `Food Item 2-005`, rồi clear; cuối cùng gõ `NO-SUCH-SKU-P24`.
- **Kỳ vọng:** input giữ focus/caret; debounce khoảng 300 ms, table trước còn mount với “Updating products…”; `FOODS_1` trả 12 SKU scenario; no-result là kết quả thành công, không phải lỗi. Badge hiển thị số kết quả nhìn thấy, không tự nhận là total toàn cục vì API limit 100. Header là **Unit of Measure**; giá trị `unit` không phải số lượng tồn. Cột **On-hand Stock** hiển thị `0`, không nhầm với missing; nếu API không có row phải nói `Not tracked`.
- **Không được đổi:** `products.unit`, inventory, sales, PO, recommendation, transaction. **PASS:** các kết quả và baseline khớp; ảnh gồm focus sau `FOODS_1`, result count, zero stock, no-result. **FAIL:** chỉ gõ được một ký tự, full-page spinner/remount, kết quả cũ ghi đè, hoặc `unit` được mô tả là tồn kho.

### H.2 Suppliers — không clipping

- **Current baseline:** tất cả supplier đều active. `SIM_M5_CA1_FOODS_V1_SUP_01/02/03` có tên dài `Synthetic Supplier N — SIM_M5_CA1_FOODS_V1`, mỗi supplier 12 mappings; lead time mapping 3–7 ngày. `DEMO_SUPPLIER_A` có 3 mappings, 3–7 ngày; `DEMO_SUPPLIER_B` có 2 mappings, 4–6 ngày. Không có inactive supplier ở snapshot nên case inactive badge là **NOT APPLICABLE**, không bịa record.
- **Thao tác:** kiểm tra `SIM_M5_CA1_FOODS_V1_SUP_02`, thu viewport, đổi sidebar expanded/collapsed và mobile-like; xem tên/code/status/mapping/lead time.
- **Kỳ vọng:** text wrap, grid item `min-width: 0`, table wrapper scroll ngang chỉ khi cần; pill không overlap/clip, cột không nhảy. Không được đổi mapping/supplier. **Evidence:** ảnh desktop hẹp + mobile-like + một sidebar collapsed; **MANUAL VERIFICATION REQUIRED**.

### H.3 Forecasts và Inventory Insights — nguồn số và công thức thực tế

**CURRENT MYSQL SNAPSHOT forecast:** run **18**, model `XGBOOST_V1`, feature set `FEATURE_SET_V1`, version `selected_trainval_final_sha256_1b484f30`, history end/origin 2016-04-24, forecast 2016-04-25 đến 2016-05-22, horizon 28, mỗi SKU có 28 rows. Prediction persisted có min 0.0223, max 9.7609 nên không âm.

| SKU (product ID) | 7 ngày | 14 ngày | 28 ngày | Current risk |
| --- | ---: | ---: | ---: | --- |
| FOODS_1_001 (4) | 5.8180 | 11.4284 | 21.0583 | STOCKOUT_RISK |
| FOODS_1_008 (13) | 1.5868 | 4.0268 | 9.2323 | REORDER_NEEDED |
| FOODS_2_005 (21) | 3.3465 | 6.3171 | 11.5672 | OVERSTOCK_RISK |
| FOODS_2_006 (22) | 2.7252 | 5.0193 | 9.5944 | OVERSTOCK_RISK |
| FOODS_2_007 (23) | 4.2341 | 8.5596 | 17.7864 | HEALTHY |
| FOODS_3_012 (39) | 16.8213 | 34.6650 | 71.1064 | HEALTHY |

Đối chiếu 7/14/28 là tổng `predicted_demand` của horizon day 1–7/1–14/1–28 từ `forecast_values`, không phải số tự nhập trên UI. Dữ liệu quan sát trước origin là M5 2011–2016; phần prediction sau 2016-04-24 là demo dự báo lịch sử M5, **không** phải lời dự báo nhu cầu thực tế tháng 11-2026. Câu nói ngắn khi bảo vệ: “Hệ thống minh họa chuỗi quyết định trên nguồn M5 đã truy xuất được; khi triển khai cho siêu thị mới, cần dữ liệu POS và huấn luyện/đánh giá lại.”

Decision engine `InventoryDecisionService.analyze` dùng: `incoming =` PO qualifying từ repository; `position = on_hand + incoming`; expected lead demand = tổng các prediction ngày 1 đến lead time; `safety_stock = ceil(1.645 × std(28 observed daily sales) × sqrt(lead_time))`; `reorder_point = ceil(expected_lead + safety_stock)`; `target_stock = ceil(sum(days 1..lead_time+1) + safety_stock)`. Risk: `position < expected_lead` = STOCKOUT_RISK; `position <= reorder_point` = REORDER_NEEDED; `position > target_stock + day-1 prediction` = OVERSTOCK_RISK; còn lại HEALTHY. `recommended_quantity = ceil(max(0, target_stock - position))` chỉ khi position <= reorder point.

Do đó vẫn có thể **có on-hand dương mà stockout risk**: position hiện tại có thể thấp hơn forecast demand trong lead time trước khi hàng mới về. Đối chiếu bắt buộc cho mỗi SKU: `inventory_position = on_hand + incoming`; ví dụ FOODS_2_005: 6 + 8 = 14; FOODS_2_006: 9 + 2 = 11.

### H.4 Purchase Orders — chỉ xem trước khi mutation

| PO ID / number | Supplier | Status | Dòng hàng ordered/received/remaining | Mốc hiện tại |
| --- | --- | --- | --- | --- |
| 4 / `SIM_M5_CA1_FOODS_V1-INCOMING` | `...SUP_02` | IN_TRANSIT | FOODS_2_005 8/0/8 | order 2026-11-06, ETA 2026-11-11 |
| 5 / `SIM_M5_CA1_FOODS_V1-PARTIAL` | `...SUP_03` | IN_TRANSIT | FOODS_2_006 8/6/2 | order 2026-11-06, ETA 2026-11-11 |
| 6 / `SIM_M5_CA1_FOODS_V1-COMPLETE` | `...SUP_01` | RECEIVED | FOODS_2_007 6/6/0 | received 2026-11-06 10:30:56 |
| 7 / `SIM_M5_CA1_FOODS_V1-LINKED-DRAFT` | `...SUP_02` | DRAFT | FOODS_1_002 6/0/6 | source recommendation ID 6; no order/ETA yet |

`IN_TRANSIT` lines contribute to Incoming Stock; DRAFT and RECEIVED do not. Thus FOODS_2_005 has incoming 8 and FOODS_2_006 has incoming 2. Read-only check opens details then closes without transition/receipt. Linked draft confirms recommendation ID 6 (`ACCEPTED`, approved 6) points to PO 7. A draft never increases on-hand.

## I. Controlled mutation protocol — preserve P22 evidence

Không chạy các case này trên P22 rows khi một fixture/disposable record có thể dùng. Mỗi case bắt đầu bằng ảnh + truy vấn baseline, có một dòng log “người thực hiện / thời gian / endpoint / request idempotency”, và kết thúc bằng ảnh UI + kiểm tra record/actor. Nếu không có disposable test SKU/PO/recommendation trong UI, **dừng và ghi MANUAL VERIFICATION REQUIRED** thay vì đổi scenario gốc.

### I.1 Operational sale và idempotency

- **Preferred target:** tạo/được chỉ định SKU test disposable có inventory, không dùng FOODS_3_012 trừ khi owner cho phép mutation P22. Baseline phải ghi product ID, on-hand, incoming, position, `sales_daily`/`operational_sales`/`stock_transactions` count liên quan và risk/recommendation.
- **Thao tác thật:** Sales → Record sale, quantity 1 không vượt on-hand, source duy nhất `P24-MANUAL-SALE-YYYYMMDD`, ghi idempotency key của request. Bấm một lần, đợi kết quả. Chỉ nếu UI/API hiện cho reuse request, resend chính request/key đó một lần.
- **Expected DB:** đúng một `operational_sales`, một `sales_daily` daily aggregate cập nhật/tạo, đúng một `stock_transactions` `SALE` quantity 1 có actor Manager. On-hand và position giảm 1; incoming không đổi; không âm; SKU không liên quan, raw M5 history, forecast rows, PO không đổi. Same key + same payload trả kết quả ban đầu; same key + khác payload bị reject, không double-sell.
- **PASS/FAIL:** PASS chỉ với before/after truy vấn + ảnh Sales/Inventory/transaction; thiếu actor, hai SALE rows hoặc negative stock là FAIL. Cleanup: không “xóa” sale evidence; ghi lại ID/giá trị cuối, chỉ rollback bằng adjustment có audit nếu owner phê duyệt.

### I.2 Historical CSV import

Sử dụng CSV fixture riêng cho disposable product/date, không import lại raw M5. Ghi `inventory.on_hand` trước/sau. Import chỉ tạo/cập nhật `sales_daily`, không tạo `SALE` transaction/operational sale và không giảm on-hand. Lý do: historical sale là quan sát quá khứ phục vụ analytics/forecast; operational sale là sự kiện vật lý hôm nay nên mới thay đổi kho. Nếu UI không có disposable product, không import vào scenario: **MANUAL VERIFICATION REQUIRED**.

### I.3 Stock adjustment

Trên product disposable, ghi baseline on-hand/incoming/position + transaction count. Thử adjustment IN hợp lệ, sau đó OUT không vượt tồn; mỗi lần phải có reason, actor Manager và một transaction (`ADJUSTMENT_IN` hoặc `ADJUSTMENT_OUT`). Position thay đổi đúng cùng lượng vì incoming không đổi. Quantity malformed, operation không hỗ trợ hoặc OUT khiến on-hand âm phải bị reject và không tạo row. Không dùng P22 product để thử điều chỉnh chỉ nhằm kiểm tra form.

### I.4 Recommendation review và linked draft PO

Chỉ dùng NEW recommendation disposable. Ghi ID, status NEW, recommended quantity, product, supplier và current linked PO = none. Test một action đang có (ACCEPT dùng đúng suggested quantity, MODIFY cần quantity, REJECT không quantity). Kỳ vọng `reviewed_by_user_id`/timestamp được ghi theo server actor. Nếu ACCEPT/MODIFY được chuyển thành draft PO: endpoint `/api/reorder-recommendations/{id}/purchase-order` phải tạo đúng một PO DRAFT liên kết, supplier/line quantity đúng approved quantity; retry không tạo PO thứ hai do unique link. Tạo draft không tăng on-hand/incoming. Không review NEW scenario IDs 14–17 nếu chưa có sự đồng ý vì chúng là evidence P22.

### I.5 Purchase order state/receipt

Tạo disposable DRAFT PO + line riêng. Test draft edit, allowed transition, invalid transition rejection, partial receipt, final receipt và over-receipt rejection. Với partial amount `q` trên line đang IN_TRANSIT: `received_after = received_before + q`; `remaining = ordered - received_after`; on-hand tăng q; incoming giảm q; **position giữ nguyên** nếu không có mutation khác; một `RECEIPT` transaction quantity q có actor Manager. Khi remaining = 0, PO RECEIVED. Cấm replay receipt; retry/double click không được cộng hai lần. Không dùng PO 5 P22 mặc định; nó được giữ như read-only reference 8/6/2.

### I.6 Authentication, authorization, error/retry

Kiểm tra Manager login hợp lệ, login sai bị từ chối không lộ credential, protected route/API từ session không hợp lệ bị từ chối, và UI phản ánh role hiện có. Không thêm behavior phân quyền mới trong P24. Với failure giả lập an toàn: check lỗi rõ ràng, Retry, form value còn khi thích hợp, request mutation failed không toast thành công và double click/retry không tạo duplicate. Riêng Products lặp lại H.1 để xác nhận failure không remount input.

## J. Functional traceability audit (source → MySQL)

| Workflow | UI/API | Route → service | Bảng/refresh |
| --- | --- | --- | --- |
| Product search | `CatalogPages.jsx` → `api.products` | `api/business.py:list_products` → `BusinessService.products` | `products`; React Query key `['products', search]`, 300 ms debounce/previous table |
| Inventory lookup | `CatalogPages.jsx`/Dashboard → `api.inventory` | `list_inventory` → `BusinessService.inventory_views` | `inventory`, PO incoming view; queries invalidate after adjustment/receipt |
| Operational sale | `OperationalPages.jsx:SalesPage` → `api.recordSale` | `sales_forecasts.py:record_sale` → `SalesService.record_sale` | `operational_sales`, `sales_daily`, `stock_transactions`, `inventory`; refresh sales/inventory/transactions/decisions |
| Historical import | `SalesImportDialog` → `api.importSales` | `import_sales` → `SalesService.import_csv` | `sales_daily` only; refresh sales/forecasts |
| Adjustment | `InventoryPage` → `api.adjust` | `create_adjustment` → `BusinessService.adjustment` | `inventory`, `stock_transactions`; refresh inventory/transactions/decisions |
| Supplier mapping | `SuppliersPage` → `api.createSupplierProduct` | `create_supplier_product` → `BusinessService.supplier_product_create` | `supplier_products`; refresh mappings/decisions |
| Forecast retrieval | `ForecastsPage` → `api.latestForecast` | `latest_forecast` → `ForecastService.latest` / `_as_response` | `forecast_runs`, `forecast_values`; no inference on read |
| Insight calculation | `DecisionsPage` → `api.decisions` | `inventory_decisions` → `InventoryDecisionService.analyze` | products, inventory, supplier_products, forecast values, qualifying POs; read-only calculation |
| Recommendation review | `DecisionsPage` → `api.reviewRecommendation` | `review_recommendation` → `InventoryDecisionService.review` | `reorder_recommendations`; actor from server session |
| Linked draft | recommendation dialog → `api.createPurchaseOrderFromRecommendation` | `create_purchase_order_from_recommendation` → `BusinessService.recommendation_purchase_order_create` | `purchase_orders`, items; unique recommendation link |
| PO receipt | `OperationalPages.jsx:PurchaseOrderDetail` → `api.receiveOrder` | `receive_purchase_order` → `BusinessService.receive_purchase_order` | PO/items, inventory, `stock_transactions`; refresh orders/inventory/transactions |

## K. Manual evidence checklist and current status

For every completed case, attach: route/viewport, timestamp, screenshot before/after, API response or non-sensitive DB query output, IDs affected, expected/actual values, PASS/FAIL. Redact email, cookie, CSRF token, password and connection strings. The following items are currently **NOT VERIFIED in a browser**: all eight normal route walkthroughs; responsive/mobile visual results; sidebar/focus visual checks; loading/error/retry interaction; search focus during live request; any new authenticated actor; sale/import/adjustment/review/PO mutation flow; and receipt replay protection.

Automated evidence is distinct: backend tests use isolated SQLite/disposable fixtures, while frontend search tests cover debounce/search parameters/retained results. Automated coverage is not a substitute for the browser acceptance items above.

### K.1 Automated verification at this documentation checkpoint

| Command | Result |
| --- | --- |
| `.\\.venv\\Scripts\\python.exe -m pytest` | **79 passed**, 2 third-party `starlette.testclient` deprecation warnings |
| `frontend: npm test` | **6 passed** |
| `frontend: npm run lint` | **passed** |
| `frontend: npm run build` | **passed**; Vite reports one advisory that the minified JS chunk is 783.39 kB (not a failure) |
| `git diff --check` | must pass again immediately before commit |

The bare `pytest` executable is **not** the supported invocation on this workstation: it failed collection with four `ModuleNotFoundError: backend` errors because its import context omitted the repository root. Use the virtual-environment module command shown above; it is the valid complete-suite result.

## L. P24-03 — Premium UX, search and motion acceptance

Trạng thái: **MANUAL VERIFICATION REQUIRED**. P24-03 chỉ thay đổi React/CSS và client-side filtering trên dữ liệu API đã tải; không chạy seed, reset hay mutation MySQL/P22.

### L.1 Inventory search và transaction history

- **Trang:** Inventory. **CURRENT MYSQL SNAPSHOT:** `FOODS_2_005` (product ID 21) là on-hand 6, incoming 8, position 14.
- **Thao tác:** gõ `FOODS_2_005`, sau đó `Food Item 2-005`; clear bằng nút X; chọn/clear các transaction type.
- **Kỳ vọng:** search không gọi mutation, không mất focus, không có full-page loading; result count thay đổi; `FOODS_2_005` là kết quả duy nhất và giữ 6 / 8 / 14. Empty state phải là “No matching inventory items”; header table luôn còn. Transaction type chỉ lọc history, không thay primary Inventory search.
- **Evidence/PASS:** ảnh desktop và <=550px, focus-visible, clear action, filtered row và empty state. Các inventory/transaction database rows phải **không đổi**.

### L.2 Suppliers và product mappings

- **Trang:** Suppliers. **CURRENT MYSQL SNAPSHOT:** search `SIM_M5_CA1_FOODS_V1_SUP_02` hoặc `Synthetic Supplier 2` phải tìm supplier active có 12 mappings; lead time scenario 3–7 days.
- **Thao tác:** search supplier theo code/name, clear; filter Product mappings theo `FOODS_2_005`, supplier code và chuỗi không tồn tại.
- **Kỳ vọng:** name/code/contact/status không clip ở desktop hẹp, sidebar collapsed, và <=550px; Preferred badge không overlap; mapping filter vẫn cho thấy product, supplier code, lead time. Không sửa preferred/lead time/mapping.
- **Evidence/PASS:** ảnh wide/1024/mobile-like và empty mapping state. Nếu browser chưa thực hiện: **MANUAL VERIFICATION REQUIRED**.

### L.3 Purchase Orders search và status filter

- **Trang:** Purchase Orders. Dùng các PO chỉ đọc: `SIM_M5_CA1_FOODS_V1-INCOMING` (IN_TRANSIT), `...-PARTIAL` (IN_TRANSIT), `...-LINKED-DRAFT` (DRAFT).
- **Thao tác:** search từng PO, tìm tên supplier, chọn IN_TRANSIT/DRAFT, sau đó kết hợp search + status và clear.
- **Kỳ vọng:** count và table phản ánh giao cắt của hai filter; “No matching purchase orders” không giống API error; filtering không transition/receive/cancel PO. Controls không clip trên mobile-like viewport.
- **Evidence/PASS:** ảnh search, combined filter, empty state; PO status, lines, quantities, stock và audit rows phải **không đổi**.

### L.4 Motion, tabs, accessibility và Products regression

- **Route motion:** click Dashboard → Inventory → Suppliers → Purchase Orders. Chỉ page-content fade/translateY nhẹ; sidebar/topbar đứng yên; reduced-motion preference phải làm chuyển cảnh gần như tức thời. Không chấm PASS nếu chưa quan sát browser.
- **Inventory Insights tabs:** chuyển Inventory Insights ↔ Restock Recommendations. Nội dung mới fade nhẹ, không flicker, không horizontal slide, count/tab width ổn định. Dùng Tab/Shift+Tab để xác nhận focus rõ ràng.
- **Responsive review:** kiểm tra 1280px, 1024px, <=550px: toolbars stack, result count còn thấy, controls không overlap, table chỉ scroll ngang khi cần, sidebar/modal giữ behavior đã duyệt.
- **Products regression:** gõ liền `FOODS_1` (12 kết quả), xem `FOODS_1_001` Unit of Measure `unit` + On-hand Stock 0, rồi `NO-SUCH-SKU-P24` (0). Input phải giữ focus; debounce 300 ms/previous table/error distinction còn nguyên.

Lý do nghiệp vụ: filters này giúp quản lý tìm đúng chứng cứ inventory/supplier/PO trong demo mà không sửa dữ liệu. Motion chỉ mô tả sự đổi page/tab, không mô phỏng forecast hoặc trạng thái kho.

## M. P24-04 composition acceptance — MANUAL VERIFICATION REQUIRED

Kiểm tra desktop/1280/1024/900/550: icon header phải thẳng giữa title line; Suppliers phải là Supplier Directory full-width rồi Product Mappings full-width; `41 mappings` không tách số/từ ở desktop; mapping selects không bị cắt; PO Search và Status là một nhóm ở trái, count ở phải. Đổi transaction type, PO/supplier mapping filter và Insight tabs để xác nhận fade/up nhanh, focus control giữ nguyên. Hover chỉ các dashboard summary/action cards: grow nhẹ + elevation, không làm table/form/modal di chuyển. Bật reduced motion để xác nhận transition/scale gần như tức thời. Không chấm PASS khi chưa có screenshot browser; các kiểm tra này không được mutation MySQL/P22.

## N. P24-04d — Dashboard KPI và tương tác Supplier — MANUAL VERIFICATION REQUIRED

Đợt này chỉ thay đổi React/CSS; **không seed, reset, ghi hoặc sửa MySQL/P22**. Các giá trị Dashboard, mapping, supplier, PO và tồn kho phải giữ nguyên.

### N.1 Dashboard — KPI Snapshot

- **Trang:** Dashboard. Chụp trạng thái bình thường ở desktop và một chiều rộng hẹp phù hợp.
- **Thao tác:** quan sát bốn snapshot Products, Available units, Incoming units và Awaiting review; hover một dashboard summary/action card đã có sẵn.
- **Kỳ vọng UI:** mỗi icon nằm giữa một khung 40px, còn SVG Lucide là glyph 19px không có padding/dot riêng. Products dùng blue, Available dùng green, Incoming dùng cyan, Awaiting review dùng amber; số KPI lớn vẫn navy. Hover dashboard summary/action còn lift/elevation theo thiết kế đã duyệt.
- **PASS:** khung/icon không chồng hoặc lệch, màu đúng ngữ nghĩa, số và dữ liệu không đổi. **FAIL:** SVG tự tạo một nền nhỏ, icon mất cân giữa khung, màu cảnh báo áp dụng sai, hoặc một thao tác hover làm thay đổi số liệu.
- **Evidence:** screenshot Dashboard trước/sau hover, gồm đủ bốn KPI. Không cần và không được thực hiện mutation database.

### N.2 Suppliers — card và row interaction

- **Trang:** Suppliers. Dùng tìm kiếm chỉ đọc `SIM_M5_CA1_FOODS_V1_SUP_02` hoặc `FOODS_2_005`; sau đó clear để xem workspace đầy đủ.
- **Thao tác:** hover riêng Supplier Directory card, Product Mappings card, một supplier row và một mapping row. Lặp lại với Reduced Motion của hệ điều hành/browser bật.
- **Kỳ vọng UI:** chỉ hai workspace card lift rất nhẹ (khoảng 2px), viền/shadow rõ hơn, không scale các panel/table/modal khác. Supplier/mapping row chỉ đổi nền blue-neutral nhẹ và có left accent; row không scale. Với Reduced Motion, card không transform và chuyển động gần như tức thời.
- **PASS:** card và row phản hồi khác nhau, filter/modal/mapping data không thay đổi, không có horizontal scrollbar/clipping. **FAIL:** table row scale, card ngoài Suppliers lift, card dịch khi bật Reduced Motion, hoặc bất kỳ bản ghi supplier/mapping nào bị sửa.
- **Evidence:** screenshot hover card, hover row và Reduced Motion; giữ lại ảnh trước/sau filter để chứng minh đây là kiểm tra chỉ đọc.

## O. P24-05 — Record Sale và interaction system — MANUAL VERIFICATION REQUIRED

Đợt này sửa React/CSS và không tạo operational sale thật. **Không seed, reset, ghi, sửa MySQL/P22 hoặc dùng Record sale để thử trực tiếp trên scenario.** Kiểm thử mutation có kiểm soát vẫn thuộc mục I với fixture disposable và baseline mới.

### O.1 Sales — mở/đóng Record Sale, chỉ kiểm tra UI

- **Trang:** Sales. Chụp bảng Sales hiện có trước khi thao tác.
- **Thao tác:** click **Record sale**; kiểm tra các field Product, Quantity, Sale date, Sell price (optional), Source; click **Cancel** hoặc nút đóng modal.
- **Kỳ vọng UI:** modal xuất hiện bình thường, không blank white page/refresh; các field và hai nút Cancel/Record sale hiển thị; Cancel đóng modal và bảng Sales còn nguyên.
- **PASS:** không có sale request/mutation sau Cancel, không có toast success, không có thay đổi Sales/Inventory/transaction rows. **FAIL:** blank page, lỗi render, modal thiếu field/nút, hoặc dữ liệu thay đổi sau Cancel.
- **Evidence:** screenshot trước click, modal mở, và Sales sau Cancel. Khi có browser developer tools, lưu Network evidence rằng Cancel không gửi `POST /api/sales/record`.

### O.2 Interaction language và Reduced Motion

- **Actionable accent:** hover row có action/inspection rõ ràng: Products (Edit), Inventory (Adjust stock), Purchase Orders (Manage/workflow), Inventory Insights (View insight), Restock Recommendations (Review hoặc Create draft PO). Row không được scale; action và focus keyboard phải rõ.
- **Scan-only:** hover Supplier, Product Mapping, Sales history và Transaction history. Theo P24-05b, chúng cũng dùng nền blue-soft + left inset accent để nhận biết row đang xem, nhưng vẫn cursor mặc định/không có click handler. Recommendation đã linked PO/không còn action cũng scan-only.
- **Card/KPI:** hover bốn Dashboard KPI/snapshot và compact Dashboard action summaries; hover Supplier Directory/Product Mappings workspace. Card lift/elevation nhẹ, lân cận không dịch. Không yêu cầu hay chấp nhận scale modal, form, table row hoặc chart panel.
- **KPI:** Products blue, Available green, Incoming cyan, Awaiting review amber; icon trong frame 40px và glyph Lucide 19px rõ, không thành dot/padding riêng.
- **Reduced Motion:** bật `prefers-reduced-motion`; route/filter/tab movement, card/KPI scale/lift phải tắt hoặc gần như tức thời; hover màu nền có thể còn.
- **Evidence/PASS:** chụp mỗi loại actionable và scan-only, một KPI, một Supplier workspace và Reduced Motion. Không đánh PASS khi chưa có screenshot browser.

## P. P24-05b — Unified row inspection và PO action order — MANUAL VERIFICATION REQUIRED

Đợt này chỉ thay đổi React/CSS; **không approve/receive/cancel PO, không record sale, không seed/reset/sửa MySQL hoặc P22.**

- **Primary tables:** hover một row ở Products, Inventory, Supplier Directory, Product Mappings, Purchase Orders, Sales history, Transaction History, Inventory Insights và Restock Recommendations. Mỗi row phải có cùng nền blue-soft và left inset marker blue; table không đổi width/không layout shift, row không scale.
- **Semantics:** marker có nghĩa row đang được xem, không mặc định là clickable. Supplier/Mapping/Sales/Transaction History vẫn cursor mặc định, không có click handler mới. Actionable row chỉ giữ action sẵn có và focus keyboard rõ ràng.
- **Purchase Orders:** dùng một DRAFT PO chỉ để xem. Header cuối là **Actions**. Thứ tự phải luôn **Manage** trước, sau đó **Approve order**; APPROVED/ORDERED tương ứng là Manage → Place order/Mark as in transit. Không click workflow action. Hai action nằm cùng hàng, gap đều, vẫn thấy rõ khi row hover.
- **Reduced Motion:** bật preference; marker/nền vẫn hiện nhưng transition gần như tức thời và không có transform.
- **Evidence/PASS:** screenshot ít nhất một read-only row, một actionable row, DRAFT Actions column, và Reduced Motion. Không kết luận PASS nếu chưa có browser screenshot.
