# Tiến độ dự án Smart Inventory Market — Bản dễ đọc

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
| **P14 — Product / Supplier / Inventory modules** | ⚪ **TODO** | Sẽ làm chức năng quản lý sản phẩm, loại hàng, nhà cung cấp, tồn kho, stock transaction và purchase order. |
| **P15 — Sales + Forecast API** | ⚪ **TODO** | Sẽ nhận lịch sử sales, lưu database, gọi model XGBoost và trả forecast 7/14/28 ngày. |
| **P16 — Inventory Decision Engine** | ⚪ **TODO** | Sẽ biến forecast thành stockout risk, overstock risk, reorder point và số lượng đề xuất nhập. |
| **P17 — React UI** | ⚪ **TODO** | Sẽ làm giao diện web chính thức. |
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
