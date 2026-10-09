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
| **P17 — React UI** | 🟢 **DONE** | Dashboard React đã được polish theo nhận diện xanh, có animation nhẹ, biểu đồ forecast xanh và dữ liệu demo local thật: forecast XGBoost, tồn kho có audit, PO đang về và recommendation do engine tính. |
| **P18 — Kiểm thử và hoàn thiện** | ⚪ **TODO** | Sẽ test toàn hệ thống, kiểm tra nghiệp vụ và chuẩn bị evidence cuối. |
| **P19 — Báo cáo và bảo vệ** | ⚪ **TODO** | Sẽ tổng hợp methodology, biểu đồ, ERD, screenshot và demo để viết luận văn/bảo vệ. |

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
