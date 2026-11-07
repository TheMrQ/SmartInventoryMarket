# Tiến độ dự án Smart Inventory Market — Bản dễ đọc

## Kết quả P16 dễ hiểu

```text
Forecast đã lưu + Tồn kho + PO sắp về + Lead time nhà cung cấp + Safety stock
                                      ↓
                                  Mức rủi ro
                                      ↓
                           Số lượng đề xuất đặt
                                      ↓
                        Người quản lý duyệt/sửa/từ chối
```

Engine ưu tiên nhà cung cấp preferred; nếu chỉ có một nhà cung cấp active thì dùng nhà đó. Nhiều nhà cung cấp active nhưng không có preferred sẽ báo lỗi thay vì tự chọn. Đề xuất không làm đổi tồn kho, không tự tạo hay gửi PO. Model forecast hiện tại vẫn chỉ phù hợp SKU M5, còn engine quyết định có thể tái sử dụng khi hệ thống có forecast hợp lệ cho siêu thị thật.

> File này giúp sinh viên và giảng viên xem nhanh dự án đã làm đến đâu. Tài liệu kỹ thuật chi tiết vẫn nằm trong các file khác của `docs/`.

## Giai đoạn hiện tại / Giai đoạn tiếp theo / Vướng mắc đã biết

- **Giai đoạn hiện tại:** `P24 — Kiểm thử và đánh giá đầu-cuối` là **IN_PROGRESS**. Đã có snapshot MySQL chỉ đọc và hướng dẫn manual; chưa có browser evidence.
- **Giai đoạn tiếp theo:** thực hiện walkthrough browser/live-workflow, chụp ảnh và ghi baseline trước mỗi mutation.
- **Vướng mắc đã biết:** P22 dừng an toàn vì MySQL local chưa có tài khoản `MANAGER`/`ADMIN` active; script không tự tạo hay mạo danh người dùng. P18/P19 vẫn cần ảnh/chạy thử thủ công, P24 cần evidence browser/workflow. Model M5 hiện tại không thể dự báo SKU siêu thị mới tùy ý; một siêu thị mới phải huấn luyện/đánh giá lại bằng POS, danh mục, lịch và giá của chính siêu thị đó.

## Đề tài

**Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning**

Hiểu đơn giản: xây dựng hệ thống quản lý tồn kho cho siêu thị, dùng lịch sử bán hàng để dự báo nhu cầu và hỗ trợ người quản lý quyết định nhập thêm hàng.

## Tiến độ từng giai đoạn

| Giai đoạn | Trạng thái | Đã làm gì và ý nghĩa |
| --- | --- | --- |
| **P0 — Chọn đề tài và kế hoạch** | 🟢 **DONE** | Chốt hướng làm hệ thống tồn kho thông minh; kết quả dự báo phải hỗ trợ quyết định nhập hàng. |
| **P1 — Khởi tạo project** | 🟢 **DONE** | Tạo GitHub, Python, FastAPI, React/Vite và tài liệu ghi nhớ dài hạn. |
| **P2 — So sánh dataset** | 🟢 **DONE** | So sánh nhiều dataset bán lẻ để chọn nguồn phù hợp cho forecasting và inventory. |
| **P3 — Chốt dataset và kiến trúc** | 🟢 **DONE** | Chọn M5 cho forecasting; chọn MySQL, Workbench, FastAPI và SQLAlchemy cho sản phẩm. |
| **P4 — Tải và kiểm tra M5** | 🟢 **DONE** | Tải và kiểm tra file, cột, ngày, sản phẩm, cửa hàng, giá và chất lượng dữ liệu M5. |
| **P5 — Chốt phạm vi thí nghiệm** | 🟢 **DONE** | Chọn CA_1 / FOODS với 1.437 SKU, horizon 28 ngày và train/validation/test theo thời gian. |
| **P6 — Baseline** | 🟢 **DONE** | Tạo Seasonal Naive và Moving Average 28 ngày làm mốc so sánh. |
| **P7 — Feature ML** | 🟢 **DONE** | Tạo 25 feature quá khứ, lịch, sự kiện, product và giá; kiểm tra không nhìn dữ liệu tương lai. |
| **P8 — LightGBM** | 🟢 **DONE** | Train LightGBM global cho 1.437 SKU; tốt hơn Seasonal Naive nhưng chưa hơn Moving Average. |
| **P9 — XGBoost** | 🟢 **DONE** | Train XGBoost; validation đạt MAE 1.402449, RMSE 2.568234, WAPE 66.647316%. |
| **P10 — So sánh/chọn model** | 🟢 **DONE** | So sánh baseline, LightGBM, XGBoost và giảm feature; giữ XGBOOST_V1 + 25 feature vì tốt nhất trên validation. |
| **P11 — Thiết kế inventory intelligence** | 🟢 **DONE** | Chốt mô phỏng lead time 7 ngày, safety stock, lost sales, luồng review và purchase order. |
| **P12 — Final forecast và so sánh nhập hàng** | 🟢 **DONE** | Mở TEST đúng một lần theo protocol, đánh giá model cuối và chạy mô phỏng hai chính sách nhập hàng. |
| **P13 — MySQL + FastAPI core** | 🟢 **DONE** | Đã tạo database MySQL, 14 bảng quan hệ, migration Alembic và kiểm tra FastAPI kết nối được database. Chưa làm CRUD nghiệp vụ. |
| **P14 — Product / Supplier / Inventory modules** | 🟢 **DONE** | Đã có API cho category, product, supplier, supplier-product, xem tồn kho, điều chỉnh kho có audit, purchase order, chuyển trạng thái và nhận hàng. Product mới có tồn kho bằng 0; chỉ adjustment và receipt mới đổi on-hand. |
| **P15 — Sales + Forecast API** | 🟢 **DONE** | Đã có import CSV lịch sử bán hàng, ghi nhận bán hàng thực tế trừ tồn kho có audit, và API dự báo 7/14/28 ngày bằng XGBoost đã chốt. Chỉ SKU M5 tương thích mới được dự báo. |
| **P16 — Inventory Decision Engine** | 🟢 **DONE** | Đã có engine tính rủi ro và số lượng đề xuất từ forecast, tồn kho, PO sắp về, lead time, safety stock; mọi đề xuất đều cần người duyệt. |
| **P17 — React UI** | 🟢 **DONE** | Dashboard React đã hoàn thiện UX: tên gọi thân thiện, sidebar gọn, focus màu xanh, panel bo tròn, dữ liệu demo local thật và biểu đồ nối doanh số lịch sử với forecast XGBoost; không dùng TEST future demand. |
| **P18 — Xác thực và tinh chỉnh UI** | 🟡 **PENDING_VERIFICATION** | Đã có xác thực phiên và các tinh chỉnh UI; lint/build không thay thế ảnh/chạy thử thủ công cần thiết. |
| **P19 — Thử nghiệm trực quan Inventory Control Room V1/V2** | 🟡 **PENDING_VERIFICATION** | Dashboard thử nghiệm dùng dữ liệu API thật; cần evidence trực quan desktop/mobile trước khi mở rộng sang trang khác. |
| **P20 — Kiểm tra chức năng** | 🟢 **DONE** | Đã kiểm tra source, test, MySQL chỉ đọc và build; ghi rõ những khoảng trống cần hoàn thiện. |
| **P21 — Sửa tính toàn vẹn và quy trình nghiệp vụ** | 🟢 **DONE** | Actor audit lấy từ session server; sale có idempotency key duy nhất; đề xuất đã duyệt tạo đúng một PO nháp liên kết; UI có sửa draft/nhận một phần/hủy; forecast phân biệt SKU M5 hợp lệ; tám trang có retry khi query lỗi. |
| **P22 — Mô phỏng siêu thị dựa trên M5** | 🟢 **DONE** | Apply scenario 36 SKU M5 đã tạo mapping, 68.868 dòng sales quan sát, forecast XGBoost V1 đã lưu, tồn kho/PO synthetic có provenance và rerun idempotent. |
| **P23 — Nghiên cứu XGBoost V2** | 🟢 **DONE** | V2 chạy tách biệt trên validation `d_1886`–`d_1913`; WAPE/MAE tốt hơn V1 nhưng RMSE không tốt hơn nên V1 vẫn là model mặc định. Không dùng lại TEST V1. |
| **P24 — Kiểm thử và đánh giá đầu-cuối** | 🟡 **IN_PROGRESS** | Đã sửa focus/search, tách đơn vị đo với tồn kho thực, sửa overflow Suppliers và đối soát MySQL live; còn browser evidence và workflow mutation có kiểm soát. |
| **P25 — Báo cáo luận văn và bảo vệ** | ⚪ **PLANNED** | Tổng hợp methodology, ERD, kết quả, giới hạn, ảnh demo và bằng chứng tái lập. |

## Kết quả P12 dễ hiểu

### Dự báo cuối trên TEST

- **MAE:** 1.454969
- **RMSE:** 2.651296
- **WAPE:** 64.450274%

Model đã được chọn trước khi mở TEST. Sau khi xem TEST không có tuning hoặc chọn lại model.

| Chỉ số | MIN_STOCK_MA28 | FORECAST_REORDER_XGBOOST_V1 |
| --- | ---: | ---: |
| Lost sales | 5,362 | 4,365 |
| Stockout SKU-days | 1,565 | 1,222 |
| Fill rate | 94.097% | 95.194% |
| Average on-hand | 11.806 | 12.569 |

Dùng forecast XGBoost giảm thiếu hàng và stockout, nhưng cần giữ tồn kho trung bình cao hơn. Đây là đánh đổi giữa phục vụ khách hàng và chi phí/tồn kho; không phải XGBoost tốt hơn trong mọi tình huống.

## Kết quả P13 dễ hiểu

- MySQL Server 8.x là nơi lưu dữ liệu thật của ứng dụng. Database là `smart_inventory_market`.
- MySQL Workbench dùng để xem/quản lý database và vẽ ERD, không phải nơi backend chạy dữ liệu.
- Alembic quản lý phiên bản cấu trúc bảng. Migration đầu tiên đã tạo 14 bảng.
- FastAPI đã kiểm tra được kết nối MySQL qua `/health/db`.
- Chưa có màn hình CRUD hay luồng nghiệp vụ đầy đủ; các phần đó bắt đầu từ P14.

## Kết quả P14 dễ hiểu

- Backend đã có nhóm API `/api` để quản lý sản phẩm, nhà cung cấp, quan hệ nhà cung cấp–sản phẩm, tồn kho và purchase order.
- Không cho sửa trực tiếp số lượng tồn kho. Mọi điều chỉnh phải có lý do và tạo dòng lịch sử `stock_transactions`.
- Purchase order ở `ORDERED` hoặc `IN_TRANSIT` mới được tính là hàng đang về. Draft, approved, cancelled hoặc đã nhận xong không được tính.
- Khi nhận hàng, hệ thống tăng tồn kho, tăng số lượng đã nhận và ghi giao dịch `RECEIPT` trong cùng một transaction. Nhận một phần vẫn là `IN_TRANSIT`; nhận đủ mới thành `RECEIVED`.
- Đã chạy smoke test trên MySQL thật và xóa toàn bộ dữ liệu test có nhãn P14 sau khi kiểm tra.

## Kết quả P15 dễ hiểu

- Import CSV lịch sử chỉ bổ sung/sửa dữ liệu `sales_daily`; không được trừ tồn kho hiện tại vì dữ liệu cũ không phải thao tác bán hàng vừa xảy ra.
- Ghi nhận một lần bán hàng thực tế khóa tồn kho, từ chối bán vượt tồn, giảm `on_hand`, cập nhật tổng bán trong ngày và tạo dòng audit `SALE` trong một giao dịch.
- Model XGBoost hiện tại chỉ học từ M5 CA_1/FOODS. Vì vậy API chỉ nhận SKU M5 có trong danh sách đã đóng băng; SKU siêu thị mới phải huấn luyện lại bằng dữ liệu POS thật.
- Đã kiểm tra SHA-256 của model cục bộ, chạy forecast 7 và 28 ngày thật trên MySQL, và không dùng sales thực tế tương lai d_1914–d_1941 làm đầu vào.

## Luồng tổng thể

```text
P0–P5: Chuẩn bị dữ liệu
P6–P10: Machine Learning
P11–P12: Thí nghiệm inventory intelligence
P13–P19: Xây dựng sản phẩm
```

```text
Sales History
      ↓
XGBoost Forecast
      ↓
Current Inventory + Incoming Stock
      ↓
Reorder Recommendation
      ↓
Manager Review
      ↓
Purchase Order → Receive Goods → Inventory Updated
```

Sau mỗi phase tiếp theo, cần cập nhật file này cùng với `docs/00_project_status.md` để sinh viên và giảng viên luôn thấy tiến độ hiện tại.

## P20 — Kiểm tra chức năng thực tế (2026-11-01)

P20 chưa thêm chức năng mới. Mục tiêu là kiểm tra xem hệ thống đang làm được gì thật sự trước khi tiếp tục phát triển. Kết quả dễ hiểu như sau:

- Đã chạy **65 kiểm thử tự động và đều đạt**. Các kiểm thử nghiệp vụ chạy trên database SQLite tạm thời, vì vậy chứng minh được luật xử lý trong code nhưng chưa thay thế cho việc bấm thử toàn bộ trên MySQL và trình duyệt thật.
- MySQL local đang ở migration mới nhất, model XGBoost đã khóa có đúng mã kiểm tra SHA-256, và dữ liệu M5/model cần thiết đang có trên máy. P20 không xóa dữ liệu, không train lại model và không chạy script seed demo vì script đó có thể thay đổi database.
- Luồng cốt lõi đã có: tạo sản phẩm thì tồn kho bằng 0; import lịch sử bán không trừ tồn; bán hàng thực tế trừ tồn và ghi audit; điều chỉnh kho/nhận hàng ghi audit; PO chỉ được tính hàng sắp về ở trạng thái `ORDERED`/`IN_TRANSIT`; đề xuất nhập hàng không tự đổi tồn kho.
- P21 tiếp theo hoàn thiện vòng nghiệp vụ: lấy người thực hiện từ phiên đăng nhập ở backend thay vì tin `user_id` do client gửi; biến đề xuất đã duyệt thành PO nháp có liên kết và chống tạo trùng; thêm idempotency cho thao tác bán; hoàn thiện UI PO nhận một phần/sửa nháp/hủy; báo lỗi tải dữ liệu rõ ràng; báo trước SKU nào đủ điều kiện forecast M5.
- P22 sau đó tạo bộ dữ liệu mô phỏng M5 lặp lại được: chỉ dùng doanh số lịch sử, lịch/sự kiện và giá M5 thật cho SKU CA_1/FOODS đủ điều kiện; product trong app phải có mapping truy vết được tới M5 item/store/SKU. Tồn kho, nhà cung cấp, lead time và PO là dữ liệu tổng hợp có marker riêng; reset chỉ được phép xóa đúng record có scenario manifest, không đụng dữ liệu người dùng khác. Không dự báo SKU mới tùy ý; siêu thị mới phải huấn luyện/đánh giá lại bằng dữ liệu POS của mình.

Chi tiết kỹ thuật, ma trận 8 trang, mức độ lỗi, bằng chứng test và kế hoạch P21–P24 nằm ở `docs/implementation/P20_functional_audit.md`.

## P22 — Mô phỏng siêu thị dựa trên M5 (đang BLOCKED)

- Đã thêm manifest/provenance cho scenario `SIM_M5_CA1_FOODS_V1`, chọn cố định 36 SKU nguyên gốc CA_1/FOODS (mỗi department 12 SKU), có hash để rerun không đổi. Dữ liệu thật chỉ là sales, calendar/event/SNAP và sell price M5 đến `d_1913`; không đọc actual TEST `d_1914`–`d_1941`.
- Tồn kho, supplier, lead time, PO, receipt, stock transaction và review đều được gắn marker synthetic; không được gọi là dữ liệu Walmart quan sát được. Script dry-run mặc định, `--apply` mới ghi dữ liệu và không reset/truncate database.
- Migration cộng thêm `f6b8c4d92a10` đã lên MySQL local và check không drift. Apply dừng trước khi import/forecast/PO vì không có user `MANAGER` hoặc `ADMIN` active. Đây là bảo vệ attribution P21. Chủ project cần chạy `scripts/db/provision_manager.py` với password nhập cục bộ, sau đó mới chạy `setup_m5_supermarket_scenario.py --apply`.

## P21 — Hoàn thiện tính toàn vẹn và quy trình nghiệp vụ (2026-11-01)

- Server lấy actor audit từ phiên đăng nhập cho điều chỉnh kho, bán hàng, PO, nhận hàng và review; ID actor gửi từ client không thể mạo danh người khác.
- Mỗi lần bán vận hành cần idempotency key. Cùng key và cùng payload trả lại kết quả đã ghi; cùng key nhưng khác payload bị từ chối. Database giữ unique key nên hai request trùng không thể tạo hai lần trừ tồn/audit.
- Đề xuất `ACCEPTED` hoặc `MODIFIED` có số lượng đã duyệt dương chỉ tạo được một PO `DRAFT` liên kết, sau xác nhận rõ ràng. PO dùng số lượng đã duyệt, chưa làm đổi tồn kho và không tự gửi nhà cung cấp.
- Màn hình PO hiển thị còn lại, sửa/xóa dòng khi nháp, nhận một phần và hủy có xác nhận. Forecast báo rõ SKU nào thuộc M5 CA_1/FOODS để được dùng XGBoost V1; tám trang vận hành có trạng thái lỗi và nút thử lại thay vì nhầm lỗi thành dữ liệu rỗng.
- Đã áp dụng migration cộng thêm `d4e9a6c21f35` lên MySQL local; Alembic head/check đều đạt. Đã chạy 70 test Python, test workflow frontend, lint và build đều đạt. Chưa có browser automation nên P24 phải bấm thử và chụp bằng chứng luồng thực tế.
