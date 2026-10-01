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

## CHECKPOINT-011 Business Requirements for Later Schema Design

The later schema must support the following domains without treating this list as final tables or columns:

- users and roles;
- categories and products;
- suppliers and supplier-product relations;
- current inventory state;
- immutable, auditable stock transactions;
- daily sales history;
- forecasting runs, forecast values, model metadata, and evaluation metrics where appropriate;
- reorder recommendations and lifecycle status;
- purchase orders, line items, lifecycle status, incoming quantities, and receipt processing.

The business workflow design also freezes these invariants for P13+:

- Normal transaction handling must not make on-hand inventory negative.
- Every stock change requires an auditable transaction record.
- A received purchase-order quantity affects inventory; open purchase-order quantities contribute to incoming/on-order state.
- Recommendation acceptance does not itself increase on-hand inventory.
- Only a receipt increases on-hand inventory; sales or stock-out fulfillment decreases it.
- Cancelled purchase orders do not count as incoming stock.
- Reorder recommendations are decision support for a manager, not automatic supplier purchasing.

Conceptual state names to support are reorder recommendations `NEW`, `ACCEPTED`, `MODIFIED`, `REJECTED`, `EXPIRED`; purchase orders `DRAFT`, `APPROVED`, `ORDERED`, `IN_TRANSIT`, `RECEIVED`, `CANCELLED`; and stock transactions `RECEIPT`, `SALE`, `ADJUSTMENT_IN`, `ADJUSTMENT_OUT`. P13 will decide representation, constraints, and transition enforcement.
