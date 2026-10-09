# Dashboard

Status: `DONE` — P17 responsive React operational dashboard integrated with the FastAPI API.

The planned dashboard will present:

- Total products and current inventory
- Low-stock, out-of-stock, and excess-stock signals
- Sales trends
- Demand forecast and forecast-versus-actual view
- Stockout risks and reorder recommendations
- Model performance

## P17 Implementation

The React/Vite UI now supplies a responsive sidebar/top-bar shell, database-health indicator, local Thesis Demo label, loading/empty/error feedback, semantic status badges, mobile navigation drawer, and a common API error layer. It uses React Router, TanStack React Query, Lucide React, Recharts, and Sonner.

Implemented pages are Dashboard, Products, Inventory, Suppliers, Purchase Orders, Sales, Forecasts, and Inventory Decisions. API mutations wait for backend success and invalidate relevant React Query caches; they do not make unsafe optimistic stock updates. The forecast page draws persisted daily predictions using Recharts and states the M5-compatible SKU limitation. The decision page presents risk calculations and supports recommendation generation plus explicit ACCEPT/MODIFY/REJECT review; it explicitly states that review does not change inventory or automatically create an order.

The Dashboard derives real KPIs, risk distribution, inventory attention, recommendations, and recent orders from API responses. It renders intentional empty states where compatible forecast/supplier context does not yet exist. Local startup instructions are maintained in `frontend/README.md`.
