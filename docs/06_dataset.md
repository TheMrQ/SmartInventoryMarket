# Dataset Memory

## Primary Candidate

**M5 Forecasting - Accuracy**, sourced from the Kaggle competition.

Known conceptually: retail/Walmart daily item/store sales with calendar/events and selling prices.

## Audit State

Actual downloaded schema is **not yet audited**. Do not fabricate exact dimensions, store/category/SKU selection, or final chronological dates.

| Item | Current value |
| --- | --- |
| Dataset version | NOT AUDITED |
| Selected store | NOT SELECTED |
| Selected category | NOT SELECTED |
| Selected SKU subset | NOT SELECTED |
| Forecast horizon | Candidate 7 / 14 / 28 days — NOT FROZEN |
| Train window | NOT FROZEN |
| Validation window | NOT FROZEN |
| Test window | NOT FROZEN |

## Known Limitation

M5 does not contain the complete real inventory operational history needed by the application. Sales data will use real M5 data. Initial inventory, lead time, safety stock, and replenishment parameters will later be simulated under explicitly documented assumptions.
