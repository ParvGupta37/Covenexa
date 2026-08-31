# Covenant Examples

Real-world style covenant clauses used for testing and development.

## Financial Covenant Examples

### Leverage Covenant
```
The Borrower shall not permit the Total Leverage Ratio (as defined herein as
Total Indebtedness divided by EBITDA for the trailing twelve month period) to
exceed 4.00 to 1.00, tested quarterly as of the last day of each fiscal quarter.
```
Extracted as: `metric=total_debt_to_ebitda, threshold=4.0, operator=<=`

### Interest Coverage Covenant
```
The Borrower shall maintain an Interest Coverage Ratio (EBITDA divided by
Interest Expense) of not less than 2.00 to 1.00, measured as of the last day
of each fiscal quarter on a trailing twelve-month basis.
```
Extracted as: `metric=interest_coverage_ratio, threshold=2.0, operator=>=`

### Minimum Liquidity Covenant
```
The Borrower shall at all times maintain unrestricted Cash and Cash Equivalents
of not less than $5,000,000.
```
Extracted as: `metric=cash, threshold=5000000, operator=>=`

### Current Ratio Covenant
```
The Borrower shall maintain a Current Ratio (current assets to current liabilities)
of at least 1.20 to 1.00 as of the end of each fiscal quarter.
```
Extracted as: `metric=current_ratio, threshold=1.2, operator=>=`

## Information Covenants (Not Monitored Numerically)

```
The Borrower shall deliver to the Lender:
(a) within 90 days after the end of each fiscal year, audited annual financial statements
(b) within 45 days after the end of each fiscal quarter, unaudited quarterly financial statements
(c) within 30 days, notice of any material adverse change
```

These are extracted by CovenantAgent as `covenant_type=information` and stored without thresholds.

## Common Negative Covenants (Not Monitored Numerically)

- "Shall not incur additional Indebtedness exceeding $10,000,000 in aggregate"
- "Shall not make any Acquisitions without Lender consent"
- "Shall not make any Restricted Payments (dividends) if leverage exceeds 3.5x"
