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

## P17 Polish

The visual system now uses the blue Smart Inventory Market palette: `#2563EB` primary actions, blue slate navigation, blue focus states, and blue forecast-chart treatment. Green is reserved for successful/healthy semantic states. KPI cards now have differentiated icon containers, supporting context, subtle elevation, and responsive hover/focus-safe transitions. Tables, controls, drawers, modals, badges, and empty states use the same restrained feedback language, with `prefers-reduced-motion` support.

The optional local-only `scripts/db/setup_ui_demo.py` prepares genuine presentation state through the existing services. It uses the frozen XGBoost artifact and the real inventory decision engine; the operational quantities exist solely to demonstrate the workflow and are not presented as observed Walmart inventory.

## P17 UX Refinement

The desktop shell now keeps the current page title in page content only; the top bar communicates global database/demo state and supplies the mobile orientation title. `frontend/src/utils/presentation.js` maps technical status enums to stable human labels and transforms only the display of anonymized M5 demo SKUs (for example `FOODS_1_001` becomes `Food Item 1-001` while the original SKU remains visible and unchanged).

Forecasts combines the real 28-day observed sales history ending at the persisted forecast origin with real future forecast values from the selected run. The chart clearly distinguishes historical sales, forecast demand, and the forecast-start boundary. No future TEST demand is fetched or visualized. Friendly summary formatting rounds only displayed values to two decimals; stored API values retain their original precision.
