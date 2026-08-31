# Testing Strategy

## Overview

Covenexa maintains **92 backend tests** with a 100% pass rate. All tests run without real API keys (using deterministic mock fallbacks). The test suite covers unit logic, engine accuracy, security invariants, and production readiness.

---

## Test Suite Structure

```
backend/tests/
├── test_critical_fixes.py          # Critical bug regression tests
├── test_e2e_loan_workflow.py       # End-to-end loan registration workflow
├── test_high_issues.py             # High-priority correctness tests
├── test_low5_duplicate_cleanup.py  # Deduplication tests (isolated, slow)
├── test_medium1_graphrag.py        # GraphRAG retrieval tests
├── test_medium3_engine_accuracy.py # Engine computation + security tests
├── test_phase2a_fixes.py           # Phase 2 correctness tests
└── test_production_readiness_pass.py # Production readiness invariants
```

---

## Test Categories

### 1. Critical Regression Tests (`test_critical_fixes.py`)
- CopilotAgent handles missing session state without crashing
- None fields in financial data are preserved as None, not coerced to 0

### 2. Engine Accuracy Tests (`test_medium3_engine_accuracy.py`)
**HealthScoreEngine:**
- Verified weight breakdown: Financial(35%) + Compliance(25%) + Liquidity(20%) + Leverage(10%) + Trend(10%) = 100%
- Score bounds: 0–100 clamped
- Null metric handling: missing values default to 50 (neutral), not 0

**RecommendationEngine:**
- Idempotency: running twice on same data does not double-insert
- Priority ordering: CRITICAL > HIGH > MEDIUM > LOW

**CovenantAgent:**
- No hardcoded formula fallbacks
- No hardcoded threshold fallbacks
- Extracts from document context only

**Security (CompanyStore):**
- No hardcoded organization UUIDs in frontend store
- No hardcoded/fake agreement IDs

### 3. GraphRAG Tests (`test_medium1_graphrag.py`)
- Vector retriever does not retry without borrower_id filter (tenant isolation)
- Graph retriever returns proper entity relationship paths
- SQL retriever returns structured borrower context

### 4. High-Priority Tests (`test_phase2a_fixes.py`)
- GET endpoints are read-only (no state mutation)
- Loan-agreement FK behavior with null agreement_id
- Recommendation engine idempotency

### 5. Production Readiness Tests (`test_production_readiness_pass.py`)
- `None != 0`: unanalyzed borrowers return None for financial fields
- Analyzed borrowers preserve their actual calculated values
- Vector retriever zero-result handling (no unfiltered fallback)
- Production environment hides internal exception details
- Development environment surfaces exception details
- File upload sanitizes path traversal filenames (`../../etc/passwd`)
- SEC URL validator blocks SSRF attack URLs (`localhost`, `169.254.x.x`, etc.)
- SEC URL validator accepts legitimate `sec.gov` and `cloudfront.net` URLs
- Cohere embed model config is consistent between config and client
- Pydantic v2 loan response schema uses `model_config` (not deprecated `class Config`)

### 6. E2E Workflow Tests
- Full loan registration workflow (org → borrower → loan → upload ready)
- Organization creation and deletion cascade

---

## Running Tests

```bash
# Run all tests (except slow duplicate cleanup)
cd backend
PYTHONPATH=.:.. .venv/bin/pytest tests/ -v \
  --ignore=tests/test_low5_duplicate_cleanup.py

# Run specific test file
.venv/bin/pytest tests/test_production_readiness_pass.py -v

# Run with output capture disabled (see print statements)
.venv/bin/pytest tests/ -v -s
```

---

## Test Results (v1.0 Final)

```
92 passed, 1 warning in ~16s
```

The single warning is a Pydantic v2 deprecation in the Cohere SDK (not in Covenexa code).

---

## Key Testing Principles

| Principle | Implementation |
|:----------|:--------------|
| No real API keys required | All LLM/Pinecone calls mock-patched in tests |
| No real DB required | Tests use in-memory or mock sessions |
| Deterministic | No randomness in expected outputs |
| Isolated | Each test cleans up its own state |
| `None != 0` | Core data integrity invariant asserted explicitly |
