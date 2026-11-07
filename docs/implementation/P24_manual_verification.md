# P24 — Hướng dẫn kiểm thử thủ công (snapshot chỉ đọc)

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
