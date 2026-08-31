# Document Detail Page

> Full frontend documentation in [Dashboard.md](./Dashboard.md).

## Page: `/app/documents/:agreementId`

Displays the full analysis results for a single ingested agreement.

### Tabs
1. **Covenants** — list of LLM-extracted covenant clauses
   - Name, metric, threshold, operator, description
   - Status badge: compliant/watch/breach based on covenant_monitoring
2. **Financial Metrics** — extracted financial figures by reporting period
   - Revenue, EBITDA, Total Debt, Cash, Interest Expense
   - Computed ratios: Debt/EBITDA, Interest Coverage, Current Ratio
3. **Document Chunks** — raw text chunks from document parsing
   - Chunk index, content preview, chunk type (covenant/financial/general)

### Data Sources
- Covenants: `GET /api/v1/documents/{agreement_id}/covenants`
- Financials: `GET /api/v1/documents/{agreement_id}/financials`
- Chunks: `GET /api/v1/documents/{agreement_id}/chunks`
