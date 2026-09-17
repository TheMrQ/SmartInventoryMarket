# Database Schema

Status: **PLANNED — NOT FROZEN**. No migrations or database business logic have been implemented.

## Database Technology Decision

- **Database engine:** MySQL
- **Backend access:** SQLAlchemy from FastAPI
- **Design/admin tool:** MySQL Workbench

MySQL Workbench is a GUI/tool for ERD design, schema inspection, SQL execution, and database administration. It is not the database engine. MySQL is the actual relational database. This decision does not authorize migrations or creation of the final database yet.

## Expected Entities and Relationships

- `users` — authenticated manager/admin and inventory-staff identities.
- `categories` — product grouping; one category can group many products.
- `products` — sellable inventory items, belonging to a category.
- `suppliers` — vendor records.
- `supplier_products` — planned many-to-many supplier/product association for supplier-specific information.
- `inventory` — current stock state associated with a product in the single-store MVP.
- `stock_transactions` — auditable stock-in, stock-out, and adjustment events associated with products/inventory.
- `purchase_orders` — orders made to a supplier.
- `purchase_order_items` — product lines belonging to a purchase order; incoming amounts later inform inventory decisions.
- `sales_daily` — daily product sales history for application reporting and forecast inputs. Initial history will be imported from a POS CSV export; later production use should receive new sales through a POS/API or database integration boundary.
- `forecasts` — generated future-demand outputs associated with products and model/run metadata.
- `model_metrics` — persisted evaluation results associated with a forecast-model run.
- `reorder_recommendations` — decision-engine recommendations referencing product/inventory context and forecast demand.

Column definitions, constraints, identifiers, and final relationship cardinalities will be designed only after requirements and dataset audit justify them. Do not treat this document as a frozen schema.
