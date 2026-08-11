# Covenexa — System Audit & Prioritized Bug Report

> **Audit Date**: August 2026  
> **Auditor**: Full codebase inspection (all endpoints, ORM, migrations, frontend pages, AI engines)  
> **Scope**: All bugs, inconsistencies, and structural problems discovered through static code analysis and database inspection

---

## CRITICAL Issues

---

### CRITICAL-1 — Create Facility Button Has No Functionality

**Issue**: The "Create Facility" button on `/loans` (LoansPage) does nothing. Clicking it is a no-op.

**Root Cause**: The button in `LoansPage.tsx` has no `onClick` handler, no modal, no form. It is purely decorative.

```tsx
// LoansPage.tsx line 32-35 — button with no onClick
<button className="flex items-center gap-2 bg-primary ...">
  <Plus className="w-4 h-4" />
  Create Facility
</button>
```

**Affected Files**:
- `frontend/src/pages/loans/LoansPage.tsx`

**Affected Tables**: `loans`

**Affected APIs**: `POST /api/v1/loans/`

**Proposed Fix**: Add a modal/form that collects `borrower_id`, `principal_amount`, `interest_rate`, `start_date`, `maturity_date`. Note: the backend `LoanCreateSchema` also requires `agreement_id` (see CRITICAL-2) which must be addressed simultaneously.

**Risk**: Low — purely additive change to a non-functional button.

---

### CRITICAL-2 — LoanCreateSchema Requires `agreement_id` — Breaks Loan Creation from Frontend

**Issue**: `LoanCreateSchema` defines `agreement_id: str` as a required field. But a loan is created BEFORE any agreement/document is uploaded. This circular dependency makes it impossible to create a loan without first having an agreement, and vice versa.

**Root Cause**: Schema design error in Sprint 1. The `loans` table has `agreement_id` as a non-nullable column, and `LoanCreateSchema` enforces it. But `UploadsPage.tsx` tries to auto-create a loan without providing `agreement_id`, causing HTTP 422 which is silently caught:

```tsx
// UploadsPage.tsx line 85-92 — missing agreement_id → always fails
const newLoanRes = await api.post("/api/v1/loans/", {
  borrower_id: selectedCompanyId,
  principal_amount: { amount: 100000000.0, currency: "USD" },
  interest_rate: 0.065,
  start_date: today,
  maturity_date: maturity,
  status: "ACTIVE",
  // agreement_id NOT PROVIDED → HTTP 422 → caught by .catch(() => null)
}).catch(() => null);
```

**Affected Files**:
- `frontend/src/pages/uploads/UploadsPage.tsx`
- `frontend/src/store/company.store.ts`
- `backend/app/core/schemas/loan.py`
- `backend/app/infrastructure/orm/loan_orm.py`
- `backend/alembic/versions/0001_initial_schema.py`

**Affected Tables**: `loans`

**Affected APIs**: `POST /api/v1/loans/`

**Proposed Fix**:
1. Make `agreement_id` optional in `LoanCreateSchema` and the `loans` table (nullable column via migration).
2. The `loans.agreement_id` field should store the ID of the **primary agreement** if one is attached later, not be required at creation time.

**Risk**: Medium — requires a migration to make `agreement_id` nullable. No data loss risk.

---

### CRITICAL-3 — AI Copilot Returns Error When Financial Metrics Contain None Values

**Issue**: `CopilotPage` shows "I encountered an error querying the intelligence engine" for borrowers with financial data.

**Root Cause**: `CopilotAgent.run()` formats financial metrics using Python f-string format specifiers (`:,.2f`). If any metric field is `None`, Python raises `TypeError: unsupported format character`. This propagates as HTTP 500.

```python
# ai/agents/copilot_agent.py line 99 — crashes if any value is None
f"**Latest Financials:** Revenue: ${fin['revenue']:,.2f} | EBITDA: ${fin['ebitda']:,.2f} ..."
```

**Additional Issue**: Even when Cohere API key is absent, the mock response is a raw JSON string like `{"_note": "Cohere API key not configured..."}`. This gets shown verbatim in the chat as an ugly JSON blob rather than a user-friendly message.

**Affected Files**:
- `ai/agents/copilot_agent.py`
- `integrations/cohere/client.py`

**Affected Tables**: `financial_metrics`

**Affected APIs**: `POST /api/v1/copilot/query`

**Proposed Fix**:
1. Wrap all f-string financial formatting with `or 0` fallbacks: `${float(fin['revenue'] or 0):,.2f}`.
2. Improve the mock response in `CohereClient` to return a proper natural language string instead of raw JSON.

**Risk**: Very low — defensive null coalescing, no schema changes needed.

---

### CRITICAL-4 — Facility Selection Empty/Wrong During Document Upload (Facility Selection Bug)

**Issue**: When a borrower has no existing loan facility, the auto-creation in `UploadsPage.tsx` silently fails (see CRITICAL-2). The fallback then sets `selectedLoanId` to the first loan in `allLoans` (fetched from `GET /api/v1/loans/` without filtering). This means the upload gets attached to a **different company's loan facility**.

**Root Cause**: Chain of failures:
1. Auto-loan creation fails due to missing `agreement_id` → caught silently
2. Fallback: `setLoans(allLoans)` — uses ALL loans across ALL borrowers
3. `setSelectedLoanId(allLoans[0].id)` — picks first loan in system (likely Acme Tech)
4. Upload attaches to wrong borrower's facility

```tsx
// UploadsPage.tsx lines 97-100 — wrong fallback
} else {
  setLoans(allLoans);  // ← all borrowers' loans!
  if (allLoans.length > 0) setSelectedLoanId(allLoans[0].id);
}
```

**Affected Files**:
- `frontend/src/pages/uploads/UploadsPage.tsx`

**Affected Tables**: `agreements`, `financial_metrics`, `covenants`

**Affected APIs**: `POST /api/v1/uploads/`, `POST /api/v1/uploads/sec-url`, `POST /api/v1/loans/`

**Proposed Fix**: Fix CRITICAL-2 first (make `agreement_id` optional). Then the auto-creation will succeed. Remove the `allLoans` fallback — if no loan exists and creation failed, show an error instead.

**Risk**: Medium — directly causes data corruption (documents linked to wrong borrower).

---

## HIGH Issues

---

### HIGH-1 — AI Recommendations Accumulate Indefinitely (Duplicate Records)

**Issue**: Every pipeline run inserts new recommendations. `GET /risk/recommendations/:id` returns ALL records for a borrower. After 5 pipeline runs, the Risk page shows 5 identical recommendation sets.

**Root Cause**: `RecommendationEngine.generate_recommendations()` does not delete existing recommendations before inserting new ones. Unlike `CovenantMonitor` (which does DELETE + INSERT), recommendations just INSERT.

```python
# ai/engines/recommendation_engine.py line 90-106
# No DELETE before INSERT — accumulates forever
await session.execute(
    text("INSERT INTO ai_recommendations ..."),
    ...
)
```

**Affected Files**:
- `ai/engines/recommendation_engine.py`
- `backend/app/api/v1/endpoints/risk.py`

**Affected Tables**: `ai_recommendations`

**Affected APIs**: `GET /api/v1/risk/recommendations/:borrower_id`

**Proposed Fix**: Add `DELETE FROM ai_recommendations WHERE borrower_id = :b` before inserting new recommendations. Or add a `DISTINCT ON` query to return only the latest generation per type.

**Risk**: Low — simple DELETE before INSERT. Existing UI is unaffected.

---

### HIGH-2 — Health Scores and Risk Assessments Accumulate Without Limit

**Issue**: Every pipeline run inserts a new row into `borrower_health_scores` and `risk_assessments`. After 20+ pipeline runs per borrower, these tables grow unbounded.

**Root Cause**: Both engines use `INSERT` without checking for existing rows.

**Affected Files**:
- `ai/engines/health_score_engine.py`
- `ai/engines/default_predictor.py`

**Affected Tables**: `borrower_health_scores`, `risk_assessments`

**Proposed Fix**: Either UPSERT (update if exists for today's date) or add a cleanup step that deletes all but the last N records per borrower. Historical trend data can be kept by keeping one record per day.

**Risk**: Low — additive query change only.

---

### HIGH-3 — Stress Test Formula Produces 0% Default Probability for Companies With Huge Coverage Ratios

**Issue**: When a borrower has a very large interest coverage ratio (e.g., Alphabet Inc at 419,365,671x due to tiny interest expense extracted from SEC), the stress test formula:

```python
proj_health = round(max(0.0, 75.0 - (breaches*20) - (stressed_leverage*5) + (stressed_coverage*3)), 1)
```

becomes `75 + (3 × 419,365,671) = 1,258,097,088`. Capped to 100. Then:
```python
proj_default = round(min(100.0, max(0.0, (100.0 - 100.0) * 0.8)), 1) = 0.0
```

Regardless of scenario severity — even -50% revenue, -50% EBITDA — the result is always 0% default probability.

**Root Cause**: The stress tester formula is unbounded on the coverage ratio term. Any company with interest expense near zero will break the formula.

**Affected Files**:
- `ai/engines/stress_tester.py`

**Affected Tables**: `stress_test_results`, `financial_metrics`

**Affected APIs**: `POST /api/v1/risk/stress`

**Proposed Fix**: Cap coverage ratio to a reasonable maximum (e.g., 50x) before applying the formula. Also cap `stressed_coverage` to 50x. Apply scenario deltas to health score more directly.

**Risk**: Low — math formula change, no schema changes.

---

### HIGH-4 — Multiple Pipeline Auto-Triggers Cause Race Conditions and Redundant Writes

**Issue**: The risk pipeline is triggered from 3 implicit locations besides the explicit POST endpoint:
1. `GET /risk/health/:id` — if no health score but has metrics
2. `GET /risk/recommendations/:id` — if no recommendations
3. Document workflow completion (auto-trigger)

If a user opens Dashboard + Risk page simultaneously after document ingestion, 2–3 pipeline runs fire concurrently, each writing duplicate rows to `borrower_health_scores`, `risk_assessments`, and `ai_recommendations`.

**Root Cause**: Each GET endpoint silently triggers a pipeline run as a side effect.

**Affected Files**:
- `backend/app/api/v1/endpoints/risk.py`
- `ai/workflows/document_workflow.py`

**Proposed Fix**: Remove implicit pipeline triggers from GET endpoints. Pipeline should only run via explicit POST or document workflow completion. Add a `pipeline_running` flag or timestamp check to prevent concurrent runs.

**Risk**: Medium — removes implicit behavior that some workflows depend on.

---

### HIGH-5 — `loans.agreement_id` Is Not a Real Foreign Key

**Issue**: `loans.agreement_id` is stored as a plain string with a comment "to avoid constraint loops." The auto-generated IDs used here (`"AGREEMENT-PRIMARY"` from the SQL INSERT in `CreateBorrowerHandler`, or `"agreement_{id[:8]}"` from `company.store`) are not valid UUIDs referencing real `agreements` rows.

**Root Cause**: The schema was designed with an anticipated but unimplemented many-to-one relationship. In practice, an agreement belongs to a loan — not the other way around.

**Affected Files**:
- `backend/app/infrastructure/orm/loan_orm.py`
- `backend/app/application/borrowers/handlers.py`
- `frontend/src/store/company.store.ts`

**Affected Tables**: `loans`

**Proposed Fix**: Remove `agreement_id` from the `loans` table entirely (it's already derivable via `agreements.loan_id`). The relationship is `agreements.loan_id → loans.id`, which already exists as a proper FK.

**Risk**: Medium — requires migration and schema change. The `LoanResponseSchema` and frontend also reference `agreement_id` (displayed in LoansPage).

---

## MEDIUM Issues

---

### MEDIUM-1 — Covenant-to-Ratio Mapping Uses Fragile Keyword Matching

**Issue**: `CovenantMonitor` determines which financial ratio to compare against a covenant threshold using keyword matching on the covenant name:

```python
if "leverage" in name_lower or "debt/ebitda" in name_lower:
    current_val = fin["leverage_ratio"]
elif "coverage" in name_lower or "interest" in name_lower:
    current_val = fin["interest_coverage"]
else:
    current_val = float(fin.get("leverage_ratio") or 3.0)  # ← hardcoded fallback
```

If a covenant is named "Maximum Senior Secured Net Indebtedness Ratio", this maps to the else-branch and uses the hardcoded 3.0 fallback.

**Affected Files**: `ai/engines/covenant_monitor.py`

**Proposed Fix**: Store `formula` field in `covenants` table (it already exists) with a standardized identifier (e.g., `"leverage_ratio"`, `"interest_coverage"`). Use that field for mapping instead of name-based heuristics.

**Risk**: Low — improved mapping only; no schema changes needed.

---

### MEDIUM-2 — `trend_score` is Always Hardcoded to 80.0

**Issue**: The health score engine hardcodes `trend_score = 80.0` regardless of actual historical score trends.

```python
# ai/engines/health_score_engine.py line 95
trend_score = 80.0  # ← hardcoded
```

This accounts for 10% of the health score (8 points always awarded for "trend").

**Affected Files**: `ai/engines/health_score_engine.py`

**Proposed Fix**: Calculate actual trend by comparing current score to previous score from `borrower_health_scores`. Positive trend → higher score, negative trend → lower score.

**Risk**: Low — engine internal change only.

---

### MEDIUM-3 — Default Predictor Base Probability is Always 5%

**Issue**: `DefaultPredictor` starts from a hardcoded `base_prob = 5.0`. For companies with no financial data (no `fin`), no further adjustments are made, returning exactly 5.0% default probability. This is presented as if it's an AI-calculated value.

```python
# ai/engines/default_predictor.py line 37
base_prob = 5.0
```

**Affected Files**: `ai/engines/default_predictor.py`

**Proposed Fix**: When no financial data exists, return `default_probability = null` and `risk_category = "NO DATA"` rather than a misleading 5.0%.

**Risk**: Low — improves accuracy of displayed data.

---

### MEDIUM-4 — Risk Page Silently Triggers Pipeline on Every Load (GET Side-Effect)

**Issue**: `GET /risk/recommendations/:id` triggers `RiskIntelligencePipeline.run_full_pipeline()` if no recommendations exist. This is a side-effect in a GET handler, which is semantically wrong (GET should be idempotent) and causes unexpected write operations.

**Affected Files**: `backend/app/api/v1/endpoints/risk.py` (lines 303-310)

**Proposed Fix**: Remove the implicit pipeline trigger from the GET endpoint. Return empty array if no recommendations exist. Prompt user to click "Recalculate Risk" instead.

**Risk**: Low — removes an implicit behavior. Users must use the explicit Recalculate button.

---

### MEDIUM-5 — `financial_statements` and `compliance_results` Tables Are Dead Code

**Issue**: Two Sprint 1 tables are in the database but are never read or written by any active code path:
- `financial_statements` — superseded by `financial_metrics`
- `compliance_results` — superseded by `covenant_monitoring`

Both ORM models still exist and are registered in `__init__.py`.

**Affected Files**:
- `backend/app/infrastructure/orm/financial_statement_orm.py`
- `backend/app/infrastructure/orm/compliance_result_orm.py`

**Affected Tables**: `financial_statements`, `compliance_results`

**Proposed Fix**: Leave tables in place (low risk to keep), but remove from ORM `__all__` exports and add a comment flagging them as deprecated. They can be formally dropped in a cleanup migration later.

**Risk**: Very Low — no active code paths use them.

---

### MEDIUM-6 — Neo4j Connected But Never Queried

**Issue**: Neo4j driver is initialized on every backend startup and kept open, consuming a connection. The Knowledge Graph endpoint builds its graph entirely from PostgreSQL at query time. Neo4j is not used.

**Affected Files**:
- `integrations/neo4j/client.py`
- `backend/app/api/v1/endpoints/risk.py` (graph endpoint)

**Proposed Fix**: Either (a) integrate Neo4j into the graph endpoint for real graph traversal, or (b) remove the Neo4j connection until it's actually implemented.

**Risk**: Low — if removed, connection resources freed; no functional impact.

---

### MEDIUM-7 — AI Copilot Does Not Use Pinecone Vector Search

**Issue**: `CopilotAgent` is described as a "Hybrid GraphRAG" engine but only performs SQL context retrieval. The Pinecone vector index (`covenexa-docs`) stores all document chunks but is never queried by the copilot. Document text evidence cannot be retrieved by the copilot.

**Affected Files**: `ai/agents/copilot_agent.py`

**Proposed Fix**: Add a Pinecone similarity search call using the user query embedding to retrieve relevant document chunks, and include them as context blocks alongside the SQL context.

**Risk**: Low — additive feature; no existing functionality broken.

---

## LOW Issues

---

### LOW-1 — `interest_rate` Stored as Decimal (0.065) but Displayed as Percentage

**Issue**: `LoanCreateSchema` validates `interest_rate` with `ge=0.0, le=1.0` (decimal, e.g., 0.065 = 6.5%). But `LoansPage.tsx` renders it as `(loan.interest_rate * 100).toFixed(2)%` — correct. However, auto-created loans in `UploadsPage` use `interest_rate: 0.065`, while the `handlers.py` auto-create SQL uses `interest_rate: 5.5` (a plain number, interpreted as 550%). This inconsistency is confusing.

**Affected Files**: `frontend/src/pages/uploads/UploadsPage.tsx`, `backend/app/application/borrowers/handlers.py`

**Proposed Fix**: Standardize on decimal representation (0.055 = 5.5%) everywhere. Fix the SQL INSERT in handlers.py to use `0.055`.

**Risk**: Very Low — cosmetic data issue in auto-created loans.

---

### LOW-2 — Dashboard "Active Facilities" Count Is Hardcoded

**Issue**: DashboardPage displays "Active Facilities" as either 0 or 1 based only on whether `recentDocs.length > 0`:

```tsx
// DashboardPage.tsx line 182
<span className="text-4xl font-extrabold">{recentDocs.length > 0 ? 1 : 0}</span>
```

A borrower with 3 loan facilities always shows "1" or "0".

**Affected Files**: `frontend/src/pages/dashboard/DashboardPage.tsx`

**Proposed Fix**: Fetch actual facility count from `GET /api/v1/loans/?borrower_id=:id` and display the real count.

**Risk**: Very Low — display only.

---

### LOW-3 — `get_loan` Endpoint Has Dead Code Bug

**Issue**: The `get_loan` endpoint in `loans.py` calls an undefined function:

```python
# backend/app/api/v1/endpoints/loans.py line 62
return await loan_query_details(session, loan_id)  # ← calls local function
```

The `LoanQueryHandler` is never called in this endpoint. It's functionally correct (the local `loan_query_details` function does call the handler) but the code structure is confusing.

**Affected Files**: `backend/app/api/v1/endpoints/loans.py`

**Proposed Fix**: Call `handler.get_by_id(query)` directly in the endpoint, removing the redundant `loan_query_details` wrapper.

**Risk**: Very Low — cosmetic refactor.

---

### LOW-4 — `company.store.ts` Has a Hardcoded Fallback Organization ID

**Issue**: When registering a new borrower, if fetching organizations fails, the store falls back to a hardcoded UUID:

```ts
// company.store.ts line 79
let orgId = "58b9ebce-3dc7-4168-af47-04a2354343f7";
```

This UUID may not exist in the database, causing borrower creation to fail with a foreign key error.

**Affected Files**: `frontend/src/store/company.store.ts`

**Proposed Fix**: If no organizations are found, show a user-facing error: "Please create an organization first." Do not silently use a hardcoded UUID.

**Risk**: Very Low — edge case only.

---

### LOW-5 — Duplicate Records in `borrower_health_scores` From Acme Tech

**Issue**: Database inspection revealed 6 health score rows for Acme Tech (all identical at 71.2). This is because the pipeline was triggered multiple times (manually, from GET endpoints, from document workflow). No deduplication or cleanup.

**Affected Tables**: `borrower_health_scores`, `risk_assessments`, `ai_recommendations`

**Proposed Fix**: See HIGH-1 and HIGH-2 for the fix.

---

## Architecture Cleanup Recommendations

### Current Structure Problems
1. **Flat top-level directories** for stubs (`rag-engine/`, `compliance-engine/`, `financial-engine/`) that add confusion without adding functionality.
2. **Dual `agents/` directories** — one at root and one at `ai/agents/` — both exist. Root-level `agents/` appears to be a stub.
3. **Risk engine bypasses DDD** — `risk.py` endpoint imports AI engines directly (`from ai.engines.pipeline_runner import ...`) instead of going through application handlers. This couples the API layer directly to the AI layer.
4. **Raw SQL in endpoints** — multiple endpoints in `risk.py` use `text("SELECT ...")` directly rather than going through repositories.

### Proposed Incremental Cleanup (No Big Rewrite)

**Phase 1 — Fix the bugs above (CRITICAL + HIGH)**

**Phase 2 — Extract raw SQL from endpoints into service classes**
```
backend/app/
  services/
    risk_query_service.py    # moves raw SQL from risk.py
    document_query_service.py
```

**Phase 3 — Consolidate stub directories**
```
# Move or delete: agents/, rag-engine/, compliance-engine/, financial-engine/
# These are empty stubs adding noise to the root directory
```

**Phase 4 — Add repository layer for AI tables**
```
backend/app/infrastructure/repositories/
  health_score_repository.py    # replaces raw SQL in health_score_engine
  risk_assessment_repository.py
  recommendation_repository.py
```

**Phase 5 — Wire Neo4j and Pinecone into Copilot properly**

---

## Summary Matrix

| ID | Severity | Module | Status |
|----|----------|--------|--------|
| CRITICAL-1 | 🔴 CRITICAL | LoansPage — Create Facility button | No onClick handler |
| CRITICAL-2 | 🔴 CRITICAL | LoanCreateSchema — `agreement_id` required | Blocks all loan creation |
| CRITICAL-3 | 🔴 CRITICAL | CopilotAgent — None value formatting crash | HTTP 500 on every query |
| CRITICAL-4 | 🔴 CRITICAL | UploadsPage — wrong loan fallback | Documents attach to wrong borrower |
| HIGH-1 | 🟠 HIGH | RecommendationEngine — no cleanup | Duplicate recommendations |
| HIGH-2 | 🟠 HIGH | HealthScore/DefaultPredictor — no cleanup | Unbounded table growth |
| HIGH-3 | 🟠 HIGH | StressTester formula | Always 0% for high-coverage borrowers |
| HIGH-4 | 🟠 HIGH | GET endpoints trigger pipeline | Race conditions, duplicate writes |
| HIGH-5 | 🟠 HIGH | loans.agreement_id not real FK | Data integrity issue |
| MEDIUM-1 | 🟡 MEDIUM | CovenantMonitor — keyword mapping | Wrong ratios for some covenants |
| MEDIUM-2 | 🟡 MEDIUM | trend_score hardcoded 80 | Inaccurate health score |
| MEDIUM-3 | 🟡 MEDIUM | base_prob hardcoded 5% | Misleading default probability |
| MEDIUM-4 | 🟡 MEDIUM | GET /recommendations side-effect | Non-idempotent GET |
| MEDIUM-5 | 🟡 MEDIUM | Dead tables (financial_statements, compliance_results) | Dead code |
| MEDIUM-6 | 🟡 MEDIUM | Neo4j connected but unused | Wasted connection |
| MEDIUM-7 | 🟡 MEDIUM | Copilot missing Pinecone retrieval | Not truly RAG |
| LOW-1 | 🟢 LOW | interest_rate inconsistency | Cosmetic data issue |
| LOW-2 | 🟢 LOW | Dashboard facilities count hardcoded | Display only |
| LOW-3 | 🟢 LOW | get_loan dead code | Cosmetic |
| LOW-4 | 🟢 LOW | Hardcoded org UUID fallback | Edge case |
| LOW-5 | 🟢 LOW | Duplicate health score rows in DB | Symptom of HIGH-1/HIGH-2 |
