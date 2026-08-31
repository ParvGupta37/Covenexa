# Integration Tests

> Full testing documentation is in [Unit Tests.md](./Unit%20Tests.md).

## Integration Test Coverage

### E2E Loan Workflow (`test_e2e_loan_workflow.py`)
Tests the full organization → borrower → loan registration flow:
- Create organization
- Register borrower under organization
- Create loan facility with principal + interest
- Verify relationships and data integrity

### Risk Pipeline Integration (`test_phase2a_fixes.py`)
- GET `/risk/health` is read-only (does not create side effects)
- Lazy pipeline trigger: health endpoint auto-runs pipeline if metrics exist but no score
- Covenant monitoring DELETE + INSERT per pipeline run

### Document Pipeline Flow
- Upload → Redis event → DocumentWorkflow → agents complete → risk pipeline
- SEC URL ingestion → synchronous DocumentWorkflow → same result as file upload

### Authentication Flow
- Register → Login → GET /auth/me returns correct user
- Invalid credentials → 401
- Missing token → 401
- Insufficient role → 403
