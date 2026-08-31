# Risk Analytics Page

> Full frontend documentation in [Dashboard.md](./Dashboard.md).

## Page: `/app/risk`

The Risk Monitor page provides a deep-dive into a single borrower's risk profile.

### Sections

#### 1. Borrower Health Score
- Circular gauge (0–100)
- Category badge: EXCELLENT / GOOD / WATCH / HIGH_RISK / CRITICAL
- Color-coded: green → amber → red

#### 2. Default Probability
- Percentage display
- Risk level badge: LOW / MEDIUM / HIGH / CRITICAL
- Based on Altman Z-Score computation

#### 3. Financial Ratios
| Metric | Source | Threshold |
|:-------|:-------|:---------|
| Debt/EBITDA | financial_metrics | Covenant-dependent |
| Interest Coverage | financial_metrics | ≥ 1.5x warning |
| Current Ratio | financial_metrics | ≥ 1.0x warning |
| Gross Margin | financial_metrics | Sector-dependent |

#### 4. Covenant Compliance
- Table of all covenants with status, actual value, threshold, headroom
- Color-coded rows: green (compliant), amber (watch), red (breach/critical)

#### 5. AI Recommendations
- Prioritized list (CRITICAL → HIGH → MEDIUM → LOW)
- Category icon: covenant / financial / operational / credit
- Expandable rationale + evidence

### Data Fetching
All sections fetched independently — page shows partial data as each API call resolves.
