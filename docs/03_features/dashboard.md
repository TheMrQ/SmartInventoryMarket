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

## P17 Decision-Support Refinement

Forecasts is the analysis surface: it resolves `GET /api/forecasts/latest?product_id=...` per selected product through React Query, restores `product` and `horizon` from URL search parameters, and only calls `POST /api/forecasts` after an explicit Generate/Refresh action. The reusable `DemandForecastChart` renders the 28 observed sales days ending at the saved forecast origin and persisted future expected-demand values with linear daily lines; navigation never triggers model inference.

Inventory Insights is the operational surface. Selecting a decision opens a product detail panel that brings together current/incoming stock, inventory position, lead-time demand, supplier lead time, safety stock, reorder point, target stock, recommended order, a responsive target-versus-position coverage bar, and an optional calculation explanation. The detail embeds the same `DemandForecastChart`; it does not duplicate chart/data logic. If a saved forecast is unavailable, it gives a clear link to Forecasts instead of fabricating demand context.

## P17 Final Visual Refinement

The shared tooltip component now has explicit hover, focus, blur, and Escape lifecycle handling, avoiding sticky help overlays in tables and the decision dialog. On desktop, modal overlays begin at the main workspace boundary and center dialogs within that workspace, leaving the fixed navigation visually separate. Rounded dialog scroll containers clip their content and use restrained integrated scrollbar styling. Major dashboard, table, forecast, and model-detail panels use a reusable structural card-header treatment.

## P17 Visual Design Polish

The visual system now favors white/light cards with 16px rounded corners, restrained borders, soft elevation, and editorial section headers over large saturated surfaces. `@fontsource-variable/inter` provides the `Inter Variable` UI font. The sidebar organizes routes into Overview, Management, and Intelligence and uses a floating chevron control for collapse. Blue is intentionally limited to primary controls, active navigation, focused elements, forecast/chart emphasis, and selected states; healthy, warning, and risk colors remain semantic.

## P17 Sidebar Layout Fix

Every route row fills the usable sidebar width and preserves the active-row background across that width. Group rows use 5px internal and 19px between-group spacing, so the eight destinations fit a typical 768px desktop viewport. The collapse state now targets `.brand-name` and `.nav-label` rather than every `nav span`; this preserves each `Tooltip` wrapper and Lucide icon as a usable link. The chevron-only control has an aria label but is deliberately not wrapped in a visual tooltip. At mobile widths, the off-canvas drawer restores group and route labels and keeps the desktop collapse control hidden.

## P17 Premium UX Pass

The desktop collapse control is now anchored below the 80px brand row at 92px from the sidebar top, while navigation reserves 58px before the first group. This makes the half-protruding 36px circular control independent of route count and prevents it from covering navigation. The sidebar uses a flex layout: its navigation region can scroll at constrained heights, and a compact, non-clickable Demo Manager / Demo workspace persona remains pinned at the bottom. The profile deliberately has no email, online status, account action, or logout control because authentication is not implemented.

`frontend/src/premium.css` provides shared spacing, radius, surface, text, border, shadow, and transition tokens plus restrained common treatment for cards, controls, fields, tables, badges, callouts, and modals. It preserves light structural card headers, semantic colors, unit/forecast presentation, existing responsive table behavior, and current user workflows.
