# Portfolio View

> Portfolio-level data is displayed on the main Dashboard. See [Dashboard.md](./Dashboard.md).

## Portfolio Data Points

The Dashboard aggregates portfolio-level intelligence across all borrowers:

| KPI | Calculation |
|:----|:-----------|
| Portfolio Health Score | Average of all borrower health scores |
| High Risk Borrowers | Count where health category IN (HIGH_RISK, CRITICAL) |
| Covenants at Risk | Count where covenant_monitoring.status IN (breach, critical) |
| Watchlist | Count where health category = WATCH |
| Total Exposure | SUM of active loan principal amounts |

All values are fetched fresh from the database on dashboard load — no caching.
