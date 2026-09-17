# Dataset Memory

## Dataset Selection Status

**OFFICIAL DATASET: M5 Forecasting - Accuracy**

**OFFICIAL STRATEGY: Real M5 sales + simulated inventory**

M5 is the official source of historical retail sales for thesis forecasting development and evaluation. M5 does **not** provide real Walmart on-hand inventory, replenishment, supplier lead time, incoming stock, or purchase-order history. Those variables will be simulated later with explicit, documented assumptions. Inventory-policy findings must be described as simulation results, not observed Walmart inventory performance.

M5 was acquired locally and formally audited on 2026-09-17. No preprocessing, model training, feature engineering, or final experimental-protocol selection was performed.

## Formal Local M5 Audit

Status: **DONE — VERIFIED LOCALLY**

### Acquisition and Reproducible Outputs

- **Acquisition date/source:** 2026-09-17; official Kaggle competition `m5-forecasting-accuracy`.
- **Local location:** Git-ignored `data/raw/m5/`; raw archive and CSVs are not committed.
- **Tooling:** Kaggle CLI 2.2.4 in `.venv`; `requirements-dev.txt` records it as a development/data-acquisition dependency, not FastAPI runtime.
- **Script:** `scripts/data/audit_m5.py`, which uses 500-row sales chunks, 100,000-row price chunks, a temporary disk-backed price-key check, and writes aggregate metadata only.
- **Generated tracked outputs:** `data/manifests/m5_file_manifest.json`, `data/manifests/m5_audit.json`, and `reports/tables/m5_audit_summary.md`.

### Verified Local File Inventory

| File | Bytes | MiB | Rows | Columns | Purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| `calendar.csv` | 103,469 | 0.099 | 1,969 | 14 | Date, event, SNAP, and retail-week mapping |
| `sales_train_validation.csv` | 120,007,726 | 114.448 | 30,490 | 1,919 | Product-store sales through `d_1913` |
| `sales_train_evaluation.csv` | 121,736,518 | 116.097 | 30,490 | 1,947 | Product-store sales through `d_1941` |
| `sample_submission.csv` | 5,228,786 | 4.987 | 60,980 | 29 | Two submission panels with `F1`–`F28` |
| `sell_prices.csv` | 203,395,785 | 193.973 | 6,841,121 | 4 | Weekly item-store selling prices |

The downloaded archive is 48,009,163 bytes (45.785 MiB). Extracted CSVs total 450,472,284 bytes (429.604 MiB); `sell_prices.csv` is the largest file. SHA-256 hashes are recorded in the file manifest.

### Sales Schema, Scope, and Quality — Verified Locally

- Both sales files use `id`, `item_id`, `dept_id`, `cat_id`, `store_id`, and `state_id`, followed by daily `d_*` columns.
- Validation contains 1,913 day columns (`d_1`–`d_1913`); evaluation has the same identifiers and 28 additional observed columns, ending at `d_1941`.
- Evaluation contains 30,490 unique item-store series with no duplicate `item_id`/`store_id` key. It represents 3,049 items, 10 stores, 3 states, 3 categories, and 7 departments. Every store has 3,049 series.
- Categories: `FOODS` (1,437 items), `HOBBIES` (565), and `HOUSEHOLD` (1,047). Departments: `FOODS_1` (216), `FOODS_2` (398), `FOODS_3` (823), `HOBBIES_1` (416), `HOBBIES_2` (149), `HOUSEHOLD_1` (532), `HOUSEHOLD_2` (515).
- Evaluation has 59,181,090 sales cells: 0 missing, 0 negative, and 40,241,819 zero cells (67.9978%). Distribution: min 0, median 0, mean 1.130888, p95 5, p99 15, max 763.
- Observed sales equal to zero does **not** prove demand was zero and does **not** imply inventory was zero.

### Calendar — Verified Locally

- Columns: `date`, `wm_yr_wk`, `weekday`, `wday`, `month`, `year`, `d`, two event name/type pairs, and `snap_CA`, `snap_TX`, `snap_WI`.
- 1,969 rows map `d_1` to `d_1969`, from 2011-01-29 through 2016-06-19, with no duplicate `d` keys or dates and 282 distinct retail weeks.
- `d_1` maps to 2011-01-29. The last locally observed evaluation-sales key, `d_1941`, maps to 2016-05-22; the calendar extends 28 days further than observed evaluation sales.
- Event missingness is expected outside events: 1,807 missing values in each primary event field and 1,964 in each secondary event field.

### Selling Prices — Verified Locally

- Columns: `store_id`, `item_id`, `wm_yr_wk`, `sell_price`.
- 6,841,121 rows cover 10 stores, 3,049 items, and 282 retail weeks. Prices join via sales `item_id`/`store_id` and calendar `wm_yr_wk`.
- Important price fields have 0 missing values; price range is 0.01–107.32; there are 0 zero prices, 0 negative prices, and 0 duplicate store/item/week keys.

### Resource Findings — Verified Locally

- Audit environment: Python 3.12.10, pandas 3.0.5; full audit completed in 48.964 seconds.
- A 500-row representative evaluation read projected about 461.933 MiB with default pandas dtypes or 236.175 MiB with `int32` day columns.
- Loading one optimized sales CSV can be practical, but loading both sales files and `sell_prices.csv` together is not recommended. Use chunking/subsetting for audit and future feature work.

### Candidate Single-Store FOODS Subsets — Not Selected

These candidates are illustrative and intentionally cover one representative store from each state plus a narrower department option. They are not ranked or frozen.

| Store | Category | Department | Items / series | History days | Zero-sales prevalence | Long-form rows | Estimated int32 sales payload |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `CA_1` | FOODS | all | 1,437 | 1,941 | 56.9186% | 2,789,217 | 10.640 MiB |
| `TX_1` | FOODS | all | 1,437 | 1,941 | 64.8026% | 2,789,217 | 10.640 MiB |
| `WI_1` | FOODS | all | 1,437 | 1,941 | 62.6583% | 2,789,217 | 10.640 MiB |
| `WI_1` | FOODS | FOODS_3 | 823 | 1,941 | 60.0453% | 1,597,443 | 6.094 MiB |

### Forecast Horizon and Chronological-Split Feasibility — Not Frozen

All 7-, 14-, and 28-day horizons are technically feasible using observed evaluation sales through `d_1941`. Shorter horizons focus on nearer-term replenishment; 28 days is more challenging but supports longer planning and matches the M5 competition framing.

| Candidate horizon | Train (start–end) | Validation | Test | Status |
| ---: | --- | --- | --- | --- |
| 7 days | `d_1`–`d_1927` (to 2016-05-08) | `d_1928`–`d_1934` (2016-05-09 to 2016-05-15) | `d_1935`–`d_1941` (2016-05-16 to 2016-05-22) | Candidate only |
| 14 days | `d_1`–`d_1913` (to 2016-04-24) | `d_1914`–`d_1927` (2016-04-25 to 2016-05-08) | `d_1928`–`d_1941` (2016-05-09 to 2016-05-22) | Candidate only |
| 28 days | `d_1`–`d_1885` (to 2016-03-27) | `d_1886`–`d_1913` (2016-03-28 to 2016-04-24) | `d_1914`–`d_1941` (2016-04-25 to 2016-05-22) | Candidate only |

All candidates are chronological; random splitting is prohibited. NEXT-005, not this audit, will select a subset, horizon, and split.

## Critical Interpretation Rule

These observations are different and must never be conflated:

- **Actual demand/sales** — observed units sold; zero sales does not prove zero demand.
- **Actual inventory position** — on-hand or inventory-pipeline quantities.
- **Stockout state** — an availability/out-of-stock signal, not an on-hand quantity.
- **Replenishment action** — quantities ordered, received, in transit, or replenished.

In particular, `sales = 0` is not evidence that `inventory = 0`.

## Comparison Matrix

`YES`, `NO`, `PARTIAL`, and `UNCLEAR` describe the evidence available in this audit, not a final data-quality verdict.

| Criterion | M5 Forecasting - Accuracy | OSA-Data | Inventory Optimization for Retail | FreshRetailNet-50K |
| --- | --- | --- | --- | --- |
| Real retail sales | YES — Walmart | NO — simulated | UNCLEAR | YES — fresh retail |
| SKU level | YES | YES | UNCLEAR | YES |
| Store level | YES | YES | UNCLEAR | YES |
| Historical sales | YES, daily | YES, dated rows | PARTIAL — claimed, not downloaded | YES, 90 days/series |
| Actual inventory quantity | NO | YES — on-hand | PARTIAL — claimed, not verified | NO |
| Replenishment history | NO | YES | PARTIAL — claimed, not verified | NO |
| Lead time | NO | YES | PARTIAL — claimed, not verified | NO |
| Stockout information | NO | PARTIAL — no explicit label verified | UNCLEAR | YES — explicit hourly status |
| Price | YES | NO | PARTIAL — claimed, not verified | NO — discount only |
| Promotion/event | YES — calendar/events | PARTIAL — promotion units | PARTIAL — claimed, not verified | YES — discount, holiday, activity |
| Clear provenance | YES | NO — published simulation | NO — no reliable origin verified | YES — developer + report |
| Clear license | PARTIAL — competition rules | NO — no license file found | YES — MIT reported by Kaggle | YES — CC BY 4.0 |
| Suitable for forecasting | YES — strong | PARTIAL — small/simulated | UNCLEAR | YES — strong, but short history |
| Suitable for inventory evaluation | PARTIAL — documented simulation | PARTIAL — rich fields but simulated/unlicensed | UNCLEAR | PARTIAL — stockout, not quantity/replenishment |
| Inventory simulation still required | YES | NO for field coverage; synthetic assumptions remain | UNCLEAR | YES |
| Dataset complexity | Medium–high | Low | UNCLEAR | High |

## Candidate A — M5 Forecasting - Accuracy

### Sources

- [Official Kaggle competition data page](https://www.kaggle.com/c/m5-forecasting-accuracy/data)
- [M5 results paper, International Journal of Forecasting](https://doi.org/10.1016/j.ijforecast.2021.11.013)

### Audit

- **Provenance / real vs synthetic:** Real Walmart unit-sales data released for the M5 competition. The published competition record reports 3,049 products across 10 US stores and 42,840 hierarchical series.
- **License:** Kaggle labels it “Subject to Competition Rules”; treat use/redistribution as restricted by those rules, not as an open-data license. Confirm terms at acquisition.
- **Known files:** `sales_train_validation.csv`, `sales_train_evaluation.csv`, `calendar.csv`, `sell_prices.csv`, and a sample submission. The official page describes daily product-store sales, calendar information, and store/date prices.
- **Scale and coverage:** 30,490 lowest-level item-store series; training covers `d_1`–`d_1913`, and evaluation extends to `d_1941`. Published coverage is 2011-01-29 to 2016-06-19. Exact local file sizes/schema are `DOWNLOAD_NOT_VERIFIED`.
- **Forecasting coverage:** Product, store, category/department hierarchy, daily sales, prices, and calendar/event variables make it highly suitable for chronological SKU-level forecasting.
- **Inventory coverage:** No actual on-hand/DC quantity, stockout state, replenishment/purchase-order history, supplier, incoming stock, or lead time.
- **Implementation:** A single-store/category/SKU subset can be constructed after formal audit. Inventory simulation remains required and must state all assumptions explicitly.

## Candidate B — OSA-Data

### Sources

- [Official Tredence GitHub repository](https://github.com/tredenceofficial/OSA-Data)
- [Published inventory CSV header and records](https://raw.githubusercontent.com/tredenceofficial/OSA-Data/main/osa_raw_data.csv)
- [Published vendor lead-time CSV](https://raw.githubusercontent.com/tredenceofficial/OSA-Data/main/vendor_leadtime_info.csv)
- [Tredence/Databricks OSA material](https://www.databricks.com/notebooks/osa-tredence/01_data-preparation.html)

### Audit

- **Provenance / real vs synthetic:** **SIMULATED.** Tredence/Databricks describes the accelerator data as a simulated inventory and vendor dataset. Do not represent it as real retailer operations.
- **License:** **UNCLEAR / NO LICENSE FILE FOUND.** The public repository lists CSVs and README but no `LICENSE` file. Public visibility is not a reuse grant; obtain clarification before thesis use or redistribution.
- **Scale and coverage:** README says about 100 Store-SKU combinations at Store-SKU-Day level. The inventory CSV is 1.98 MB with 40,590 data rows; exact range and distinct counts were not formally computed.
- **Verified schema:** `date`, `store_id`, `sku`, `product_category`, `total_sales_units`, `on_hand_inventory_units`, `replenishment_units`, `inventory_pipeline`, `units_in_transit`, `units_in_dc`, `units_on_order`, `units_under_promotion`, and `shelf_capacity`. The lead-time file provides vendor/store/item identifiers and DC, transit, and on-order lead-time fields.
- **Forecasting coverage:** Dated sales, store, SKU, category, and promotion-unit fields exist; price/calendar/weather/events were not verified.
- **Inventory coverage:** On-hand/DC quantities, replenishment, pipeline, transit, on-order, shelf capacity, and lead time are present. No separately documented stockout flag was verified; zero on-hand must not automatically mean lost demand.
- **Implementation:** Lightweight, but small, simulated, and apparently irregular in dated observations. It can illustrate decision logic but is weak evidence for a thesis claim about real inventory performance.

## Candidate C — Inventory Optimization for Retail (Kaggle / `suvroo`)

### Source

- [Official Kaggle dataset page](https://www.kaggle.com/datasets/suvroo/inventory-optimization-for-retail)

### Audit

- **Provenance / real vs synthetic:** **UNCLEAR.** Accessible Kaggle metadata identifies an uploader and says the data was designed for a multi-agent retail system, but did not provide a verifiable retailer, collection method, publication/DOI, or statement that it is real. Do not call it real or synthetic yet.
- **License:** Kaggle reports **MIT**. Confirm current license and provenance at acquisition; an open license does not prove underlying observations are real.
- **Claimed composition:** Historical sales, store/warehouse inventory, restocking frequency, supplier/logistics delivery schedules and lead times, price changes, and promotions.
- **Schema / scale / coverage:** `DOWNLOAD_NOT_VERIFIED`. Kaggle file metadata/API access was unavailable and the data was intentionally not downloaded. Fields, record count, range, granularity, stockout labels, supplier IDs, and actual inventory/replenishment semantics remain unverified.
- **Suitability:** Potentially attractive only if claims are independently substantiated. It must not become a thesis dataset because its schema looks convenient.

## Candidate D — FreshRetailNet-50K

### Sources

- [Official Hugging Face dataset card](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K)
- [Technical report](https://arxiv.org/abs/2505.16319)
- [Official baseline repository](https://github.com/Dingdong-Inc/frn-50k-baseline)

### Audit

- **Provenance / real vs synthetic:** Real fresh-retail data released by Dingdong-Inc with a 2025 technical report; a public benchmark for censored-demand/stockout-aware forecasting.
- **License:** CC BY 4.0, version 1.0, released 2025-05-08. Attribution is required; retain the citation and review terms at use.
- **Scale:** Dataset card reports 50,000 store-product 90-day series, 898 stores in 18 cities, 865 perishable SKUs, 4,500,000 train rows, and 350,000 evaluation rows. Its abstract says 863 SKUs; resolve this 863/865 discrepancy during formal audit.
- **Verified fields:** Store/product/category hierarchy, date, normalized daily and hourly sales, out-of-stock hour count/status, discount, holiday/activity flags, precipitation, and weather.
- **Forecasting coverage:** Strong SKU/store sales, hierarchy, discount, holiday/activity, and weather context. The 90-day history is much shorter than M5; hourly-to-daily aggregation and censored-demand treatment raise complexity.
- **Inventory coverage:** Explicit stockout state is valuable, but there is **no verified on-hand/DC quantity, replenishment, incoming stock, purchase order, supplier, lead time, safety stock, or reorder point**. A stockout flag is not an inventory quantity.
- **Implementation:** A single-store fresh-retail subset is plausible, but full data needs memory-conscious Parquet processing. Simulation remains needed for quantity/replenishment outcomes.

## Optional Backup — Store Sales - Time Series Forecasting (Corporación Favorita)

- [Official Kaggle page](https://www.kaggle.com/c/store-sales-time-series-forecasting/data)
- Real grocery-chain daily store/product-family sales with promotion counts; a forecasting-only backup, not an inventory/replenishment candidate.

## Candidate Ranking — Recommendation Only

This ranking is an evidence-based recommendation, **not** an official selection.

1. **M5 Forecasting - Accuracy** — strongest long daily SKU-store history, price/calendar context, academic provenance, and direct fit for planned baseline/LightGBM/XGBoost comparison. Inventory requires transparent simulation.
2. **FreshRetailNet-50K** — strongest real alternative for stockout-aware fresh retail, with clear CC BY 4.0 terms and rich context. It lacks quantities/replenishment, has 90-day series, and adds hourly/censoring complexity.
3. **OSA-Data** — best operational schema but simulated, small, and lacking a clear reuse license.
4. **Inventory Optimization for Retail** — fields are claimed, but provenance and actual schema are unverified.

## Dataset Strategy Assessment

### Strategy A — M5 only: real sales + simulated inventory

**Recommended provisionally, pending user decision.** It provides one coherent, real retail source and a defensible forecasting benchmark. Inventory results must be reported as a **simulation study**, with explicit initial inventory, lead-time, safety-stock, incoming-stock, and policy assumptions; never as observed Walmart replenishment outcomes.

### Strategy B — One dataset containing sales and inventory

No primary candidate is currently verified as both real and complete enough. OSA has the fields but is simulated/unlicensed; FreshRetailNet is real and stockout-annotated but lacks quantities and replenishment. Strategy B is not currently supported.

### Strategy C — Real forecasting data + separate inventory data

**Not recommended as the main evaluation.** Unrelated stores would make forecast errors and inventory positions come from different systems, weakening causal interpretation. OSA may later be a clearly labelled demo fixture after license clarification, not evidence that an M5 forecast improves a real OSA inventory system.

## Formal-Audit State and Boundaries

| Item | Current value |
| --- | --- |
| Dataset version | M5 acquisition/version NOT YET AUDITED LOCALLY |
| Selected store | NOT YET FROZEN |
| Selected category | NOT YET FROZEN |
| Selected SKU subset | NOT YET FROZEN |
| Forecast horizon | 7 / 14 / 28 days are candidates — NOT YET FROZEN |
| Train window | NOT YET FROZEN |
| Validation window | NOT YET FROZEN |
| Test window | NOT YET FROZEN |

No candidate has been acquired locally. The next user-directed action is M5 acquisition and formal local schema/resource audit, not model training or feature engineering.
