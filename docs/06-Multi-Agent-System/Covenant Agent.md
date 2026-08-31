# Covenant Agent

## Purpose

Extract structured covenant definitions from loan agreement document chunks using LLM comprehension. Produces the covenant data that drives the compliance monitoring system.

---

## File

`ai/agents/covenant_agent.py`

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
- `chunks` — list of document text chunks from DocumentAgent

---

## LLM Prompt Strategy

For each chunk, the agent sends a structured prompt to Cohere Command A:

```
Extract all financial covenants from the following legal text.
For each covenant found, return a JSON object:
{
  "name": "Human-readable covenant name",
  "covenant_type": "financial" | "information" | "affirmative",
  "metric": "machine-readable metric key (e.g. total_debt_to_ebitda)",
  "threshold": float or null,
  "operator": "<=" | ">=" | "<" | ">" or null,
  "description": "Full covenant description from the text"
}
Return a JSON array. If no covenants are found, return [].
```

---

## Output

- Inserts extracted covenants into the `covenants` table
- Each covenant is linked to `agreement_id` and `borrower_id`
- `source_chunk_id` preserves the origin chunk for citation

---

## No Hardcoded Rules

The CovenantAgent extracts covenants based entirely on document content — there are no hardcoded covenant types, metrics, or thresholds in the agent code. This is validated by a production test:
```
test_covenant_agent_has_no_hardcoded_formula_fallbacks ✅
test_covenant_agent_has_no_hardcoded_threshold_fallbacks ✅
```

---

## Downstream: CovenantMonitor

Once covenants are extracted, the `CovenantMonitor` engine evaluates each covenant against actual financial metrics:

```python
for covenant in covenants:
    actual_value = get_metric_value(financial_metrics, covenant.metric)
    is_breached = evaluate(actual_value, covenant.operator, covenant.threshold)
    headroom = compute_headroom(actual_value, covenant.threshold)
    status = classify(headroom, is_breached)
    # INSERT into covenant_monitoring
```