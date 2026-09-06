# Architecture

## High-level Architecture

```text
React Frontend
      ↓
FastAPI Backend
      ↓
Database
      ↓
Forecasting Service
      ↓
Inventory Decision Engine
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

## Current Implementation Status

Only a FastAPI smoke application and React/Vite environment scaffold exist. Database, forecasting service, decision engine, and business integrations are planned only.
