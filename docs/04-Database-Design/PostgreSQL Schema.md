# PostgreSQL Schema — 19 Tables Across 4 Migrations

## Migration Chain

```
0001_initial_schema.py
  → organizations, users, borrowers, loans, agreements,
    financial_statements, compliance_results, reports

0002_document_intelligence.py
  → document_chunks, covenants, financial_metrics
  + Added pipeline columns to agreements: is_analyzed, analyzed_at, parsing_status

0003_risk_intelligence.py
  → borrower_health_scores, risk_assessments, covenant_monitoring,
    alerts, stress_test_results, ai_recommendations

0004_audit_logs.py
  → audit_logs
```

---

## Entity Hierarchy

```
organizations
  └── borrowers
        ├── loans
        │     └── agreements
        │           ├── document_chunks
        │           ├── covenants
        │           └── financial_metrics
        ├── borrower_health_scores
        ├── risk_assessments
        ├── covenant_monitoring
        ├── alerts
        ├── stress_test_results
        ├── ai_recommendations
        └── reports

users (belong to organizations implicitly via registration)
audit_logs (system-wide, unscoped)
```

---

## Table Definitions

### `organizations`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| name | VARCHAR | Org / fund name |
| industry | VARCHAR | e.g. Technology, Finance |
| created_at | TIMESTAMPTZ | |

### `users`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| name | VARCHAR | Display name |
| email | VARCHAR UNIQUE | |
| password_hash | VARCHAR | bcrypt hash |
| role | VARCHAR | `ADMIN` or `ANALYST` |
| created_at | TIMESTAMPTZ | |

### `borrowers`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| organization_id | VARCHAR FK → organizations | |
| company_name | VARCHAR | |
| sector | VARCHAR | |
| country | VARCHAR | |
| risk_level | VARCHAR | `LOW`, `MEDIUM`, `HIGH` |
| risk_score | INTEGER | 1–10 |
| created_at | TIMESTAMPTZ | |

### `loans`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| agreement_id | VARCHAR FK → agreements NULLABLE | Set after upload |
| principal_amount | JSONB | `{ amount, currency }` |
| interest_rate | FLOAT | |
| start_date | DATE | |
| maturity_date | DATE | |
| status | VARCHAR | `ACTIVE`, `CLOSED`, `DEFAULTED` |
| created_at | TIMESTAMPTZ | |

### `agreements`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| loan_id | VARCHAR FK → loans | |
| version | INTEGER | |
| file_path | VARCHAR | Local or S3 path |
| file_name | VARCHAR | Original filename |
| file_type | VARCHAR | `pdf`, `docx`, `html` |
| upload_date | TIMESTAMPTZ | |
| is_analyzed | BOOLEAN | False until pipeline completes |
| analyzed_at | TIMESTAMPTZ NULLABLE | |
| parsing_status | VARCHAR | `pending`, `processing`, `completed`, `failed` |

### `document_chunks`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| agreement_id | VARCHAR FK → agreements | |
| borrower_id | VARCHAR FK → borrowers | |
| chunk_index | INTEGER | Position in document |
| content | TEXT | Raw chunk text |
| chunk_type | VARCHAR | `covenant`, `financial`, `general` |
| embedding_id | VARCHAR NULLABLE | Pinecone vector ID |
| metadata | JSONB | |
| created_at | TIMESTAMPTZ | |

### `covenants`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| agreement_id | VARCHAR FK → agreements | |
| borrower_id | VARCHAR FK → borrowers | |
| name | VARCHAR | e.g. "Leverage Ratio Covenant" |
| covenant_type | VARCHAR | `financial`, `information`, `affirmative` |
| metric | VARCHAR | e.g. `total_debt_to_ebitda` |
| threshold | FLOAT NULLABLE | e.g. 4.0 |
| operator | VARCHAR | `<=`, `>=`, `<`, `>` |
| description | TEXT | Full covenant text |
| source_chunk_id | VARCHAR NULLABLE FK → document_chunks | |
| created_at | TIMESTAMPTZ | |

### `financial_metrics`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| agreement_id | VARCHAR FK NULLABLE | Source document |
| reporting_period | VARCHAR | e.g. "Q4 2025" |
| revenue | FLOAT NULLABLE | |
| ebitda | FLOAT NULLABLE | |
| total_debt | FLOAT NULLABLE | |
| cash | FLOAT NULLABLE | |
| interest_expense | FLOAT NULLABLE | |
| current_assets | FLOAT NULLABLE | |
| current_liabilities | FLOAT NULLABLE | |
| total_assets | FLOAT NULLABLE | |
| retained_earnings | FLOAT NULLABLE | |
| working_capital | FLOAT NULLABLE | |
| market_cap | FLOAT NULLABLE | |
| debt_to_ebitda | FLOAT NULLABLE | Computed |
| interest_coverage | FLOAT NULLABLE | Computed |
| current_ratio | FLOAT NULLABLE | Computed |
| gross_margin | FLOAT NULLABLE | Computed |
| created_at | TIMESTAMPTZ | |

### `borrower_health_scores`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| score | FLOAT | 0–100 composite |
| category | VARCHAR | `EXCELLENT`, `GOOD`, `WATCH`, `HIGH_RISK`, `CRITICAL` |
| financial_score | FLOAT NULLABLE | 35% weight |
| compliance_score | FLOAT NULLABLE | 25% weight |
| liquidity_score | FLOAT NULLABLE | 20% weight |
| leverage_score | FLOAT NULLABLE | 10% weight |
| trend_score | FLOAT NULLABLE | 10% weight |
| computed_at | TIMESTAMPTZ | |

### `risk_assessments`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| default_probability | FLOAT | 0–100% |
| altman_z_score | FLOAT NULLABLE | Classical Z-Score value |
| risk_level | VARCHAR | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| confidence | FLOAT | Model confidence 0–1 |
| rationale | TEXT NULLABLE | Explanation |
| assessed_at | TIMESTAMPTZ | |

### `covenant_monitoring`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| covenant_id | VARCHAR FK → covenants | |
| actual_value | FLOAT NULLABLE | Current metric value |
| threshold | FLOAT NULLABLE | Covenant limit |
| headroom | FLOAT NULLABLE | (threshold - actual) / threshold |
| status | VARCHAR | `compliant`, `watch`, `breach`, `critical` |
| checked_at | TIMESTAMPTZ | Replaced each pipeline run |

### `alerts`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| alert_type | VARCHAR | `covenant_breach`, `health_decline`, etc. |
| title | VARCHAR | Short alert title |
| message | TEXT | Detailed description |
| severity | VARCHAR | `critical`, `high`, `medium`, `low` |
| is_read | BOOLEAN | Default false |
| metadata | TEXT NULLABLE | JSON extra context |
| created_at | TIMESTAMPTZ | |

### `stress_test_results`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| scenario | JSONB | Input shock parameters |
| results | JSONB | Full output with breached covenants |
| projected_health | FLOAT NULLABLE | |
| projected_default | FLOAT NULLABLE | |
| created_at | TIMESTAMPTZ | |

### `ai_recommendations`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| priority | VARCHAR | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| category | VARCHAR | `COVENANT`, `FINANCIAL`, `OPERATIONAL`, `CREDIT` |
| recommendation | TEXT | Action description |
| rationale | TEXT | Why this is recommended |
| evidence | TEXT NULLABLE | Supporting data points |
| created_at | TIMESTAMPTZ | Accumulates — not replaced |

### `reports`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| borrower_id | VARCHAR FK → borrowers | |
| report_type | VARCHAR | `credit_memo` |
| generated_at | TIMESTAMPTZ | |
| report_path | VARCHAR NULLABLE | File path if saved |
| content | TEXT NULLABLE | Markdown content |

### `audit_logs`
| Column | Type | Notes |
|:-------|:-----|:------|
| id | VARCHAR PK | UUID |
| action | VARCHAR | e.g. `user_login`, `document_upload` |
| resource_type | VARCHAR | `auth`, `document`, `borrower`, etc. |
| user_id | VARCHAR NULLABLE | |
| user_email | VARCHAR NULLABLE | |
| details | JSONB | Extra context |
| created_at | TIMESTAMPTZ | |

---

## Key Design Decisions

| Decision | Rationale |
|:---------|:----------|
| `financial_statements` table (Sprint 1) deprecated by `financial_metrics` | `financial_metrics` has computed ratios and is document-linked; `financial_statements` was a simpler precursor |
| `borrower_health_scores` accumulates (no DELETE) | Enables trend tracking over time; latest row = current score |
| `covenant_monitoring` is replaced each run (DELETE + INSERT) | Always reflects current state; prevents stale compliance records |
| `ai_recommendations` accumulates | History of recommendations preserved; frontend shows latest batch |
| `None ≠ 0` policy | Unanalyzed fields remain NULL and shown as `N/A` in UI — never fabricated |