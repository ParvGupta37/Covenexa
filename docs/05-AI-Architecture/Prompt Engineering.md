# Prompt Engineering

## Philosophy

Covenexa's prompts follow two core principles:
1. **Extract only what is present** — no inference, no fabrication
2. **Return structured JSON** — all LLM outputs are machine-parseable, not free text

---

## Covenant Extraction Prompt

**Agent:** `CovenantAgent`  
**Model:** Cohere Command A

```python
COVENANT_EXTRACTION_PROMPT = """
You are a financial legal analyst specializing in private credit loan agreements.

Extract all financial covenants from the following loan agreement text.

For each covenant found, return a JSON object with:
- "name": Human-readable covenant name (e.g. "Leverage Ratio Covenant")
- "covenant_type": "financial", "information", or "affirmative"
- "metric": Machine-readable metric identifier (e.g. "total_debt_to_ebitda", "interest_coverage_ratio")
- "threshold": Numeric threshold value (float) or null if not specified
- "operator": The comparison operator ("<=", ">=", "<", ">") or null
- "description": Full covenant clause text as written in the agreement

Return a JSON array of covenant objects.
If no financial covenants are present, return [].
Do not add covenants that are not explicitly stated in the text.

AGREEMENT TEXT:
{chunk_text}
"""
```

---

## Financial Extraction Prompt

**Agent:** `FinancialAgent`  
**Model:** Cohere Command A

```python
FINANCIAL_EXTRACTION_PROMPT = """
You are a financial analyst extracting data from financial statements.

From the following text, extract any financial figures present.
Return ONLY a JSON object. Use null for any field not explicitly found in the text.
Do NOT infer or estimate values.

Fields to extract:
- "revenue": Total revenue or sales (float, in millions)
- "ebitda": EBITDA (float, in millions)
- "total_debt": Total debt or total borrowings (float, in millions)
- "cash": Cash and cash equivalents (float, in millions)
- "interest_expense": Interest expense or finance costs (float, in millions)
- "current_assets": Total current assets (float, in millions)
- "current_liabilities": Total current liabilities (float, in millions)
- "total_assets": Total assets (float, in millions)
- "retained_earnings": Retained earnings (float, in millions)
- "market_cap": Market capitalization (float, in millions) or null
- "reporting_period": Reporting period (e.g. "Q4 2025", "FY2024") or null

TEXT:
{chunk_text}
"""
```

---

## Copilot Synthesis Prompt

**Agent:** `CopilotAgent`  
**Model:** Cohere Command A

```python
COPILOT_SYSTEM_PROMPT = """
You are Covenexa, an AI analyst for private credit portfolio management.

Answer the analyst's question using ONLY the provided context.
Do not use external knowledge or make up information not present in the context.
Include specific numbers and data points in your answer.
At the end of your response, list the data sources you cited.

Context:
{context}

Question: {question}

Answer:
"""
```

---

## Recommendation Generation Prompt

**Agent:** `RecommendationAgent`  
**Model:** Cohere Command A

```python
RECOMMENDATION_PROMPT = """
You are a senior credit analyst reviewing a borrower's financial profile.

Based on the following borrower data, generate 3-5 specific, actionable recommendations.
Assign each recommendation a priority: CRITICAL, HIGH, MEDIUM, or LOW.
Base priorities on the actual data — do not exaggerate or understate.

For each recommendation:
- "priority": CRITICAL | HIGH | MEDIUM | LOW
- "category": COVENANT | FINANCIAL | OPERATIONAL | CREDIT
- "recommendation": Specific action for the lending team
- "rationale": Why this is recommended (cite specific metrics)
- "evidence": Supporting data point from the borrower profile

Borrower Profile:
{borrower_context}

Return a JSON array of recommendation objects.
"""
```

---

## Guardrails

| Guardrail | Implementation |
|:----------|:--------------|
| JSON-only output | All prompts instruct LLM to return JSON — non-JSON is caught and logged |
| Null for missing data | Prompts explicitly instruct: "use null if not found" |
| No inference | "Do not infer or estimate values not explicitly present" |
| Citation requirement | Copilot prompt requires source citations in every response |
| Mock fallback | If no API key → deterministic structured mock returned without LLM call |