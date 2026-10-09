# Architecture

## High-level Architecture

```text
React + Vite Frontend
      ↓
FastAPI Backend
      ↓
SQLAlchemy
      ↓
MySQL
      ↑
MySQL Workbench (ERD design and database administration)
```

## Business Pipeline

```text
Sales History
      ↓
Preprocessing
      ↓
Time-Series Feature Engineering
      ↓
Forecast Model
      ↓
Predicted Demand
      ↓
Current Inventory + Supplier Lead Time + Safety Stock + Incoming Stock
      ↓
Stockout / Overstock Analysis
      ↓
Reorder Recommendation
```

## Scope Boundaries

This is a single-store MVP for a small/medium supermarket, not a full ERP. Planned forecasting must influence actual inventory recommendations; it is not an isolated analytics feature. Full POS, payment, accounting, loyalty, delivery logistics, native mobile, full multi-branch support, barcode scanning, and advanced deep learning remain out of scope unless explicitly approved.

## Database Technology Decision

**MySQL 8.x** is the implemented relational database engine. FastAPI accesses the local MySQL Server through SQLAlchemy 2.x and the PyMySQL driver; Alembic revision `f86d36b27719` owns the initial schema. **MySQL Workbench is not the database**: it is the GUI/tool for ERD design, schema inspection, SQL execution, and database administration. It is not an application runtime dependency.

## Sales Data Ingestion Architecture

### Initial Historical Import

```text
Existing supermarket POS historical export
      ↓
CSV import process
      ↓
Smart Inventory Market
      ↓
sales_daily
```

An initial CSV import gives a newly adopting supermarket enough history for forecasting.

### Ongoing Sales Sync

```text
POS / external sales system
      ↓
API or database integration
      ↓
Smart Inventory Market
      ↓
sales_daily
```

The thesis MVP needs CSV sales import and a clearly defined future POS/API integration boundary; it does not need to implement a complete POS. In model development/evaluation, M5 supplies historical sales. In a real deployment, the system must eventually use that supermarket's own POS sales, not Walmart M5 data.

## Layered Backend Design — CHECKPOINT-011

```mermaid
flowchart TD
    UI[React Frontend] --> API[FastAPI API Layer]
    API --> APP[Application / Service Layer]
    APP --> DOMAIN[Domain / Business Rules]
    DOMAIN --> REPO[Repository / SQLAlchemy Layer]
    REPO --> DB[(MySQL)]
    WB[MySQL Workbench] -. ERD design and administration .-> DB

    APP --> FS[Forecast Service]
    FS --> FB[Past-only Feature Builder]
    FS --> MODEL[Loaded XGBOOST_V1 artifact]
    APP --> IDS[Inventory Decision Service]
    IDS --> RP[Reorder point and safety stock]
    IDS --> RISK[Stockout / overstock risk]
    IDS --> REC[Human-reviewed reorder recommendation]
```

P13+ must preserve these boundaries: FastAPI routes coordinate requests and responses but must not contain all business rules. Forecasting and inventory decision logic are separate services, while repositories isolate persistence concerns. The system is decision support: recommendation generation ends in human manager review and must not automatically purchase from suppliers.

## Current Implementation Status

P15 adds separate `SalesService` and `ForecastService` layers. `/api/sales/import` is a historical CSV UPSERT that changes `sales_daily` only. `/api/sales/record` locks inventory, updates the daily aggregate, and writes an immutable `SALE` transaction atomically. `/api/forecasts` obtains persisted history through the repository, rebuilds the frozen `FEATURE_SET_V1` with the shared builder/recursive utilities, uses a cached SHA-validated XGBOOST_V1 artifact, and atomically saves `forecast_runs`/`forecast_values`. Forecast inference is deliberately restricted to frozen M5 CA_1/FOODS SKU identities and the 2016 M5 calendar origin; it does not claim arbitrary supermarket-SKU support. Recommendation logic, authentication, and frontend workflows remain later-phase work.
