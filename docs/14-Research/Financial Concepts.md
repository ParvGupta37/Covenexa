# Financial Concepts Reference

Key financial metrics and formulas used by Covenexa's engines.

## Financial Ratios

### Debt/EBITDA (Leverage Ratio)
```
Total Debt ÷ EBITDA
```
- Measures how leveraged a company is relative to its operating earnings
- Industry norm: ≤ 4.0x for investment-grade private credit
- Covenexa warning: > 4.5x | Critical: > 6.0x

### Interest Coverage Ratio
```
EBITDA ÷ Interest Expense
```
- Measures ability to pay interest from operating earnings
- Healthy: ≥ 3.0x | Warning: < 2.0x | Critical: < 1.5x

### Current Ratio (Liquidity)
```
Current Assets ÷ Current Liabilities
```
- Measures short-term liquidity
- Healthy: ≥ 2.0x | Warning: < 1.2x | Critical: < 1.0x

### Gross Margin
```
(Revenue - Cost of Goods Sold) ÷ Revenue × 100%
```
- Measures pricing power and operational efficiency

## Altman Z-Score (Default Prediction)

```
Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5

Where:
X1 = Working Capital / Total Assets
X2 = Retained Earnings / Total Assets
X3 = EBITDA / Total Assets  (proxy for EBIT/Total Assets)
X4 = Market Cap / Total Liabilities  (or Book Equity if no market cap)
X5 = Revenue / Total Assets
```

### Altman Z-Score Interpretation
| Z-Score | Zone |
|:--------|:-----|
| > 2.99 | Safe zone |
| 1.81 – 2.99 | Grey zone |
| < 1.81 | Distress zone |

Covenexa maps Z-Score to 0–100% default probability:
- Z > 3.0 → ~10% default probability
- Z 1.5–3.0 → 30–60% default probability
- Z < 1.5 → 70–90% default probability

## Borrower Health Score — Weight Breakdown

| Dimension | Weight | Source Metrics |
|:----------|:-------|:--------------|
| Financial Performance | 35% | EBITDA margin, revenue trend |
| Covenant Compliance | 25% | Covenant monitoring status |
| Liquidity | 20% | Current ratio, cash balance |
| Leverage | 10% | Debt/EBITDA |
| Trend | 10% | Change in health score over time |

Total: 100%. Score range: 0–100 (higher is healthier).

## Covenant Types

| Type | Description | Example |
|:-----|:-----------|:--------|
| Financial | Tied to measurable ratio | "Debt/EBITDA ≤ 4.0x" |
| Information | Reporting obligations | "Deliver financial statements within 90 days" |
| Affirmative | Things borrower must do | "Maintain adequate insurance coverage" |
| Negative | Things borrower must not do | "Do not incur additional indebtedness > $5M" |

Covenexa's CovenantAgent focuses on **financial covenants** — the ones with testable thresholds.
