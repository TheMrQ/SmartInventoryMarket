# Tiến độ dự án Smart Inventory Market — Bản dễ đọc

> File này dùng để xem nhanh dự án đang ở đâu và từng giai đoạn đã làm gì.
> Các file kỹ thuật khác vẫn là nguồn chi tiết cho Codex/AI, còn file này ưu tiên cách viết đơn giản, dễ đọc cho sinh viên và giảng viên.

## Đề tài

**Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning**

Hiểu đơn giản:

**Xây dựng hệ thống quản lý tồn kho cho siêu thị, có khả năng dự báo nhu cầu hàng hóa bằng Machine Learning và đề xuất khi nào cần nhập thêm hàng, nhập bao nhiêu.**

## Tiến độ từng giai đoạn

| Giai đoạn | Trạng thái | Đã làm gì? |
| --- | --- | --- |
| **P0 — Chọn đề tài và lập kế hoạch** | 🟢 **DONE** | Chốt hướng làm hệ thống quản lý tồn kho thông minh cho siêu thị. Sản phẩm cuối không chỉ dự báo nhu cầu mà còn dùng kết quả dự báo để hỗ trợ quyết định nhập hàng. |
| **P1 — Khởi tạo project** | 🟢 **DONE** | Tạo GitHub repo, môi trường Python, FastAPI cơ bản, React/Vite cơ bản, cấu trúc thư mục và bộ tài liệu để lưu tiến độ lâu dài. Backend có endpoint kiểm tra hệ thống chạy được. |
| **P2 — Tìm và so sánh dataset** | 🟢 **DONE** | Xem và so sánh nhiều dataset bán lẻ khác nhau để tìm nguồn dữ liệu phù hợp cho forecasting và inventory. |
| **P3 — Chốt dataset và kiến trúc ban đầu** | 🟢 **DONE** | Chọn M5 Forecasting - Accuracy làm dataset chính cho forecasting. Chốt hướng dùng sales thật từ M5 và mô phỏng inventory vì M5 không có tồn kho thật. Chọn MySQL, MySQL Workbench, FastAPI, SQLAlchemy và React cho hệ thống. |
| **P4 — Tải và kiểm tra dataset M5** | 🟢 **DONE** | Tải dữ liệu M5 chính thức từ Kaggle và kiểm tra file, số dòng, số cột, ngày, sản phẩm, store, giá bán và chất lượng dữ liệu. |
| **P5 — Chốt phạm vi thí nghiệm** | 🟢 **DONE** | Chọn store **CA_1**, nhóm **FOODS**, tổng cộng **1,437 SKU**. Chốt dự báo **28 ngày** và chia dữ liệu theo thời gian thành TRAIN, VALIDATION và TEST. Không dùng random split. |
| **P6 — Làm baseline** | 🟢 **DONE** | Tạo hai cách dự báo đơn giản là **Seasonal Naive** và **Moving Average 28 ngày** để làm mốc so sánh với Machine Learning. |
| **P7 — Tạo feature cho Machine Learning** | 🟢 **DONE** | Tạo **25 feature** từ lịch sử bán hàng, rolling mean/std, ngày tháng, sự kiện, product và price. Kiểm tra để feature không nhìn thấy dữ liệu tương lai. Có khoảng **2.67 triệu dòng train**. |
| **P8 — Train LightGBM** | 🟢 **DONE** | Train một global LightGBM cho toàn bộ 1,437 SKU. Kết quả tốt hơn Seasonal Naive nhưng chưa tốt bằng Moving Average. |
| **P9 — Train XGBoost** | 🟢 **DONE** | Train XGBoost với cùng dữ liệu và cách đánh giá. Trên validation, XGBoost đạt **MAE 1.402449, RMSE 2.568234, WAPE 66.647316%** và tốt hơn các phương pháp trước đó. |
| **P10 — So sánh và chọn model** | 🟢 **DONE** | So sánh XGBoost, LightGBM và các baseline. Sau đó thử giảm số feature còn 20, 16 và 11. Các bản giảm feature đều kém hơn, nên chốt **XGBOOST_V1 + FEATURE_SET_V1 gồm 25 feature**. |
| **P11 — Thiết kế mô phỏng tồn kho và nghiệp vụ** | 🟢 **DONE** | Chốt cách mô phỏng tồn kho: lead time 7 ngày, kiểm tra hàng mỗi ngày, safety stock, lost sales, hàng đang về và quy tắc đặt hàng. Đồng thời chốt các luồng nghiệp vụ như sales, recommendation, manager duyệt, purchase order, nhận hàng và điều chỉnh kho. |
| **P12 — Kiểm tra forecast cuối và so sánh chính sách nhập hàng** | 🟢 **DONE** | Model đã được train lại bằng TRAIN + VALIDATION và chỉ mở TEST đúng một lần để đánh giá cuối. TEST đạt **MAE 1.454969, RMSE 2.651296, WAPE 64.450274%**. Trong mô phỏng tồn kho, cách nhập hàng dùng XGBoost giảm thiếu hàng nhưng phải giữ tồn kho trung bình cao hơn. |
| **P13 — MySQL + FastAPI core** | 🟡 **IN_PROGRESS** | Đã cài MySQL Server và MySQL Workbench, tạo database **smart_inventory_market** và user dành cho ứng dụng. Bước tiếp theo là tạo schema bằng SQLAlchemy + Alembic, kết nối FastAPI với MySQL và tạo ERD. |
| **P14 — Product / Supplier / Inventory modules** | ⚪ **TODO** | Sẽ làm các chức năng quản lý sản phẩm, loại hàng, nhà cung cấp, tồn kho, stock transaction và purchase order. |
| **P15 — Sales + Forecast API** | ⚪ **TODO** | Sẽ cho hệ thống nhận lịch sử sales, lưu database, gọi model XGBoost và trả ra forecast 7/14/28 ngày qua API. |
| **P16 — Inventory Decision Engine** | ⚪ **TODO** | Sẽ biến forecast thành stockout risk, overstock risk, reorder point và recommended quantity. |
| **P17 — React UI** | ⚪ **TODO** | Sẽ làm giao diện chính thức theo phong cách **trắng + xanh dương**, sạch, hiện đại và chuyên nghiệp. |
| **P18 — Kiểm thử và hoàn thiện** | ⚪ **TODO** | Sẽ test toàn hệ thống, sửa lỗi, kiểm tra các nghiệp vụ và chuẩn bị evidence cuối. |
| **P19 — Báo cáo và bảo vệ** | ⚪ **TODO** | Sẽ gom methodology, experiment, biểu đồ, ERD, screenshots và kết quả hệ thống để viết luận văn và chuẩn bị slide/demo bảo vệ. |

## Kết quả P12 dễ hiểu

### Kết quả dự báo cuối trên TEST

- **MAE:** 1.454969
- **RMSE:** 2.651296
- **WAPE:** 64.450274%

Model được chọn trước khi TEST được mở và không có tuning lại sau khi xem TEST.

### So sánh hai cách nhập hàng

| Chỉ số | MA28 min-stock | XGBoost forecast reorder |
| --- | ---: | ---: |
| Lost sales | 5,362 | 4,365 |
| Stockout SKU-days | 1,565 | 1,222 |
| Fill rate | 94.097% | 95.194% |
| Average on-hand | 11.806 | 12.569 |
| Reorder events | 13,215 | 12,681 |
| SKUs có stockout | 549 | 492 |
| Normalized cost proxy | 515,039 | 540,233 |

Hiểu đơn giản:

**Dùng forecast của XGBoost giúp giảm số hàng bị thiếu và tăng tỷ lệ đáp ứng nhu cầu, nhưng đổi lại hệ thống phải giữ nhiều hàng tồn kho hơn và cost proxy cao hơn.**

Đây là trade-off giữa **khả năng phục vụ khách** và **chi phí/tồn kho**, không phải kết quả kiểu "XGBoost thắng toàn bộ".

## Toàn bộ thesis chia thành 4 chặng

```text
CHẶNG 1 — Chuẩn bị dữ liệu
P0 → P5
Dataset + phạm vi + train/validation/test

CHẶNG 2 — Machine Learning
P6 → P10
Baseline → Features → LightGBM → XGBoost → chọn model

CHẶNG 3 — Inventory Intelligence
P11 → P12
Quy tắc tồn kho → mô phỏng → kiểm tra forecast có giúp nhập hàng hay không

CHẶNG 4 — Xây sản phẩm
P13 → P19
Database → Backend → Decision Engine → UI → Test → Luận văn
```

## Sản phẩm cuối dự kiến làm được gì?

```text
Sales History
      ↓
XGBoost Forecast
      ↓
Forecast 7 / 14 / 28 ngày
      ↓
Current Inventory + Incoming Stock
      ↓
Stockout / Overstock Risk
      ↓
Recommended Reorder Quantity
      ↓
Manager Accept / Modify / Reject
      ↓
Purchase Order
      ↓
Receive Goods
      ↓
Inventory Updated
```

Mục tiêu cuối cùng là một **website quản lý tồn kho cho siêu thị có hỗ trợ dự báo và đề xuất nhập hàng**, chứ không chỉ là một mô hình Machine Learning đứng riêng lẻ.
