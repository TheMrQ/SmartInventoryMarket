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

## P17 Animated UX and Authentication

Protected application routes now restore a real session through `GET /api/auth/me`; unauthenticated users are redirected to `/login` and return to their intended route after sign-in. Login and registration use a responsive CSS 3D circular panel with a static reduced-motion fallback and a restrained animated conic-gradient ring. The sidebar profile reflects the authenticated name and role and includes a real logout action. The demand chart reserves legend space and allows responsive legend wrapping; the page-content layer uses a short reduced-motion-aware fade/vertical entrance without remounting providers or triggering forecasts.

## P18 Authentication UX Hotfix

The auth surface is deliberately outside the operational dashboard shell. It uses a very light canvas and a small dark-navy brand container, while the centered desktop coin remains dark navy with an attached blue/cyan/indigo conic-gradient ring. The coin has one stable React component for both `/login` and `/register`; its pending face rotates as one 780 ms 3D object before the history URL changes. Direct URLs and browser back/forward synchronize the face, active controls are focused after the transition, and hidden controls are disabled/removed from tab order. Short desktops and mobile use a single un-clipped rounded-card fallback rather than nested scrolling.

Authentication fields use a thin `#60A5FA` border plus soft blue glow on focus, with a separate visible keyboard focus treatment that does not stack a harsh global outline. Buttons, face switches, and password visibility controls have small hover/press feedback; all movement and ring rotation stop under `prefers-reduced-motion`. Registration exposes only the client-side confirmation field to the browser; the API receives its documented `full_name`, `email`, and `password` fields. FastAPI validation lists are normalized to concise inline messages rather than raw JSON.

## P18 Coin Rendering Repair

The moving gradient is no longer a filled plane in the 3D scene. Two decorative ring elements represent the front and reverse coin perimeters. Each is backface-hidden, positioned with its matching face, and uses a radial CSS mask so only the conic-gradient circumference paints; the center remains transparent at every angle. This avoids using fragile z-index escalation and prevents either Login or Register from being covered after `rotateY(180deg)`. The auth canvas returned to dark navy `#0F172A`; the brand container is now a lighter integrated navy with a subtle border, while the coin remains a distinct slightly lighter navy surface.

## P18 Premium Workspace Refinement

The fixed sidebar keeps its navigation region horizontally bounded. Full-width route rows no longer translate on hover, and horizontal overflow is constrained only for navigation; wide operational tables retain their intentional independent horizontal scrolling. Expanded navigation does not render route tooltips. In desktop collapsed navigation, the shared tooltip component portals the visible label to `document.body` and positions it beside the source icon, closing on pointer leave, blur, or Escape. It is consequently outside the scrollable sidebar layout and cannot create a horizontal scrollbar.

The footer uses actual session data rather than a demo persona: a 50px white, thin-blue-outlined `UserRound` avatar overlaps the left edge of a `#1E304D` profile tail. The tail presents the authenticated full name and formatted role plus the real logout control. No enclosing rectangle or fabricated status/account action is introduced. At desktop collapse, the tail transitions out over 200ms and the centered avatar remains. The mobile drawer restores the capsule and logout control for usable account exit.

`premium.css` centralizes blue, surface, shadow, easing, and radius tokens for the existing workspace. Buttons gain restrained lift/press/shadow feedback, inputs gain calm hover/focus treatment, rows gain blue-gray hover feedback, and modals/cards retain light surfaces with refined shadows. This is visual-only: no route, data loading, API contract, auth behavior, forecast generation, inventory calculation, or model boundary changes.

## P18 Targeted UI Repair

Collapsed navigation explicitly keeps each `.tooltip` wrapper and its route link visible, correcting the earlier broad `.collapsed nav span` rule that hid those wrapper spans together with their icons. Only explicit `.nav-label` and group-label text remains hidden on desktop collapse; all eight route icons, active styling, keyboard/click links, fixed portal tooltips, avatar-only footer, and chevron behavior are retained. Mobile restores labels in the drawer as before.

Within the Inventory Insight dialog only, the compact demand chart panel now uses a 20px inset and a local header layout with no negative margins. The heading/subtitle, divider, responsive chart, axes, and legend remain inside the rounded panel. The main Forecasts chart is intentionally unchanged. Register omits the disabled social-option component; Login remains the sole location for the disabled Google/Facebook/GitHub coming-soon controls. No authentication API/session/role behavior changed.

## P18 Collapsed-Sidebar Final Alignment

At desktop widths, collapsed brand, navigation, and profile layout now share one parent-derived center axis: the brand has no residual expanded padding/gap and centers its mark, the symmetric navigation rail centers each route/icon, and the 50px avatar remains centered by automatic side margins. This preserves the distinct logo/avatar sizes while aligning their centers across the actual sidebar width. Labels/group labels remain hidden, while all eight links, active state, and portalled tooltips remain usable.

The collapsed active ribbon is rendered as a non-interactive sidebar overlay. The shell measures the active route row after route, resize, and nav-scroll changes, then places a 23px primary-blue continuation from the row's ordinary right edge to 11px beyond the sidebar. Because it is a sibling of the clipped navigation scroller, it does not expand or reintroduce horizontal sidebar scrolling; the active icon itself remains centered in its ordinary 42px row. The ribbon is desktop-collapsed-only and respects existing reduced-motion timing.

## P18 Sidebar Active-Hover Fix

The generic dark-slate route hover is now explicitly limited to inactive links. A higher-specificity active rule preserves the `#2563EB` active surface on pointer hover, focus, and keyboard focus-visible interaction in expanded and collapsed navigation. Active feedback is limited to a 6% brightness change and soft blue shadow, with no transform, so the centered icon and measured ribbon remain visually coherent. Inactive routes retain the existing slate hover behavior.

## P18 Actual Collapsed-Icon Alignment

The desktop collapsed navigation now establishes its icon rail from the sidebar width rather than from each group's local content width. It uses no horizontal outer padding on the nav itself; every `nav-group` is a full-width border-box grid with centered items, and every direct tooltip wrapper receives the same `calc(100% - 24px)` width. The full-width route link centers its icon in that common rail. This corrects the screenshot-reported Management/Intelligence right shift without translations or per-icon offsets. The 12px inset still connects the active row to the measured 11px sidebar-level ribbon, and the expanded sidebar/mobile drawer remain unchanged.

## P18 Sliding-Card Authentication Redesign

The authentication presentation now replaces the circular 3D UI with one stable, horizontally split card (`min(960px, viewport - 48px)` by `min(590px, viewport - 132px)`). Login uses a left blue-gradient welcome panel and right white form; Register mirrors it. A single gradient overlay transitions from its source half to the full rounded card and then to the destination half. Form identity swaps only once the overlay covers the card, so no form content is horizontally stretched or exposed early. The transition state is advanced by the overlay width’s `transitionend` event; repeated switches are disabled while it is active, and reduced-motion or compact single-column layouts change sides directly.

Both Login and Register forms remain in the DOM. The inactive form is hidden, disabled, and non-interactive; the revealed form receives focus after the transition. Existing API/React Query behavior is unchanged. The card preserves thin blue input focus, button hover/press feedback, real password/confirmation validation, inline errors, and dark navy page branding. Google, Facebook, and GitHub marks come from `react-icons` but are disabled placeholders with “coming soon” labels—there is no OAuth, redirect, or fake login path. At tablet/mobile widths or constrained heights, the card becomes a single-column rounded layout without the desktop horizontal expansion.
