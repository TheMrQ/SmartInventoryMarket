# M5 Local Audit Summary

This generated report contains aggregate metadata only; it has no raw M5 records.

## Verified Local Findings

- Extracted raw CSV size: 429.604 MiB; archive: 45.785 MiB.
- Evaluation sales: 30,490 item-store series × 1,941 daily columns (d_1 to d_1941).
- Calendar: 2011-01-29 to 2016-06-19; evaluation sales ends 2016-05-22.
- Stores/items/categories/departments: 10/3049/3/7.
- Zero sales prevalence: 68.00%; negative sales cells: 0.
- Prices: 6,841,121 rows, range 0.01 to 107.32, duplicate keys 0.

## Candidate Subsets (Not Selected)

| Store | Category | Department | Items | Series | Days | Zero sales | Estimated int32 payload MiB |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| CA_1 | FOODS | All | 1,437 | 1,437 | 1,941 | 56.92% | 10.64 |
| TX_1 | FOODS | All | 1,437 | 1,437 | 1,941 | 64.80% | 10.64 |
| WI_1 | FOODS | All | 1,437 | 1,437 | 1,941 | 62.66% | 10.64 |
| WI_1 | FOODS | FOODS_3 | 823 | 823 | 1,941 | 60.05% | 6.094 |

Final subset, horizon, and split selection belongs to NEXT-005.
