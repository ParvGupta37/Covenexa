# Loan Agreement Samples

> Reference notes on loan agreement structure. Used to train the CovenantAgent prompt.

## Typical Structure of a Leveraged Loan Agreement

1. **Definitions** — all capitalized terms defined here (EBITDA, Indebtedness, Interest Coverage Ratio, etc.)
2. **Facility** — amount, type (revolving/term), draw conditions
3. **Representations and Warranties** — what the borrower represents as true
4. **Affirmative Covenants** — obligations the borrower must maintain
5. **Negative Covenants** — prohibited actions
6. **Financial Covenants** — testable ratio obligations (most important for Covenexa)
7. **Events of Default** — what constitutes a breach + cure periods
8. **Remedies** — lender's rights on default

## Where Financial Covenants Live

Section 6 or 7 (varies by deal) under **Financial Covenants** or **Financial Maintenance Covenants**. Look for:
- "shall not exceed" (leverage, debt)
- "shall not fall below" / "shall maintain" (coverage, liquidity)
- "tested quarterly" / "measured as of the last day of each fiscal quarter"

## SEC EDGAR Sources for Practice

- Form 8-K (Material Definitive Agreement) — often attaches credit agreements
- EDGAR full-text search: https://efts.sec.gov/LATEST/search-index?q=%22credit+agreement%22&dateRange=custom&startdt=2024-01-01

## Notes on Parsing Challenges

- EBITDA definitions vary by deal — often custom-defined with addbacks (e.g., "Consolidated EBITDA" includes non-cash items)
- Covenant thresholds may step down over time ("4.0x through Q2 2025; 3.5x thereafter")
- Some covenants are springing — only tested when revolver utilization exceeds 35%

Covenexa v1.0 uses the simple threshold at time of extraction — step-downs and springing conditions are not modeled.
