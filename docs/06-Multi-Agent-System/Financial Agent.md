# Financial Agent

## Purpose

Extract structured financial metrics from raw document chunks using LLM comprehension. Produces the financial data that feeds the FinancialEngine, HealthScoreEngine, and DefaultPredictor.

---

## File

`ai/agents/financial_agent.py`

---

## Position in Pipeline

```
DocumentAgent → CovenantAgent → FinancialAgent → RiskPipeline
                                     ↑
                              [This Agent]
```

---

## Inputs

- `agreement_id` — the document being analyzed
- `borrower_id` — the borrower this document belongs to
- `chunks` — list of document text chunks (from DocumentAgent)

---

## LLM Prompt Strategy

For each chunk, the agent sends a structured prompt to Cohere Command A asking it to extract:

```
From the following text, extract any financial data present.
Return ONLY a JSON object with these fields (use null if not found):
{
  "revenue": float or null,
  "ebitda": float or null,
  "total_debt": float or null,
  "cash": float or null,
  "interest_expense": float or null,
  "current_assets": float or null,
  "current_liabilities": float or null,
  "total_assets": float or null,
  "retained_earnings": float or null,
  "market_cap": float or null,
  "reporting_period": string or null
}
```

---

## Output

- Merges extracted fields across chunks (latest non-null wins)
- INSERTs a `financial_metrics` row for the borrower
- Downstream: FinancialEngine computes derived ratios (debt_to_ebitda, interest_coverage, current_ratio, gross_margin)

---

## None ≠ 0 Policy

If a field is not found in the document, it remains `null` in the database. It is **never** coerced to `0`. This prevents false financial health signals.

---

## Mock Fallback

If no `COHERE_API_KEY` is configured, the agent returns a deterministic mock extraction. Marked clearly in logs as `[MOCK]`.