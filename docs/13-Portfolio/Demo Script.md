# Demo Script — Covenexa

> Use this script for live demos, investor presentations, or technical walkthroughs.

---

## Setup Checklist (Before Demo)

- [ ] Backend running: `http://localhost:8000`
- [ ] Frontend running: `http://localhost:3000`
- [ ] PostgreSQL running: `docker-compose up -d`
- [ ] Redis running: `docker-compose up -d`
- [ ] At least one Organization registered
- [ ] At least one Borrower registered under that Org
- [ ] At least one Loan facility created
- [ ] At least one document uploaded and analyzed (pipeline: `completed`)
- [ ] Risk pipeline run at least once for the demo borrower

**Demo login:** `admin@covenexa.in` / `Admin@123`

---

## Demo Flow (~10 minutes)

### Step 1 — Login (30s)
1. Open `http://localhost:3000`
2. Enter credentials → click Login
3. Land on the Dashboard

**Say:** *"The dashboard gives a real-time portfolio view — health score, high-risk borrowers, covenant watch count, and the alert feed. Everything here is live database data — no hardcoded mocks."*

---

### Step 2 — Dashboard Overview (1 min)
1. Point to KPI cards: Health Score, High Risk count, Covenants at Risk
2. Point to the Risk Distribution donut chart
3. Point to the Portfolio Exposure chart
4. Point to the Recent Alerts feed

**Say:** *"The dashboard aggregates across all borrowers in your portfolio. The risk distribution shows how your book is segmented — green, amber, red."*

---

### Step 3 — Borrower Selection (30s)
1. Click the borrower dropdown in the Topbar
2. Select the demo borrower

**Say:** *"Covenexa supports multi-borrower portfolios. Switching context here changes the data across every page."*

---

### Step 4 — Risk Monitor (2 min)
1. Click `Risk Monitor` in the sidebar
2. Show the Borrower Health Score gauge (e.g. 62/100 — WATCH)
3. Show Default Probability (e.g. 28%)
4. Scroll to the Financial Ratios table

**Say:** *"The Borrower Health Score is a 5-dimension composite — financial performance, covenant compliance, liquidity, leverage, and trend. It's not just a number — it's explainable."*

5. Scroll to Covenant Compliance table

**Say:** *"Every covenant from the loan agreement is extracted by our AI and monitored in real-time. The headroom column shows how far from breach we are."*

6. Scroll to AI Recommendations

**Say:** *"The system generates prioritized action items — CRITICAL, HIGH, MEDIUM. These are evidence-backed from actual financial data, not generic advice."*

---

### Step 5 — Document Upload (1.5 min)
1. Click `Documents` in the sidebar
2. Click `Upload Document`
3. Select a PDF loan agreement + choose the loan
4. Click Upload

**Say:** *"When I upload this PDF, a Redis event fires and a LangGraph multi-agent pipeline runs asynchronously. DocumentAgent parses and embeds the content into Pinecone. CovenantAgent extracts covenant clauses using an LLM. FinancialAgent extracts financial metrics."*

5. Show the document in the list with status `processing` → refresh to `completed`

---

### Step 6 — Document Detail (1 min)
1. Click the document to open `DocumentDetailPage`
2. Show Extracted Covenants tab — name, threshold, operator
3. Show Extracted Financial Metrics tab

**Say:** *"No manual data entry. The AI reads the legal document and produces structured, queryable data."*

---

### Step 7 — Stress Testing (1 min)
1. Click `Stress Testing` in the sidebar
2. Set Revenue Change to -20%, EBITDA Change to -30%
3. Click `Run Scenario`

**Say:** *"What happens to this borrower if a recession hits? I'm simulating a 20% revenue drop and 30% EBITDA decline. The system evaluates which covenants would breach under stress and projects the adjusted health and default probability."*

4. Show projected health, projected default, and breached covenants

---

### Step 8 — AI Copilot (1.5 min)
1. Click `AI Copilot` in the sidebar
2. Type: *"What is the leverage covenant for this borrower and are they currently compliant?"*
3. Show the response + citations

**Say:** *"The Copilot uses Hybrid GraphRAG — it simultaneously queries the SQL database for current financial state, Pinecone for relevant document chunks, and Neo4j for entity relationships. Every answer comes with citations."*

4. Try: *"What would happen to their covenants if revenue dropped 25%?"*

---

### Step 9 — Credit Memorandum (30s)
1. Navigate to any page with the `Generate Report` button
2. Click it — show the 6-section Credit Memo

**Say:** *"One click generates a complete Executive Credit Memorandum — Executive Summary, Financial Analysis, Covenant Status, Stress Scenarios, Recommendations, and Risk Rating. Ready to send to an LP."*

---

## Q&A Talking Points

**"How accurate is the covenant extraction?"**
> The AI extracts covenant type, metric name, threshold, and operator from legal text. Accuracy depends on document quality. We validate extractions against the compliance monitoring results — if covenants produce unrealistic ratios, analysts can flag and re-run.

**"How is this different from ChatGPT?"**
> ChatGPT doesn't have access to your portfolio data. Covenexa's Copilot retrieves real-time data from three sources — your database, your documents, and your knowledge graph — before every answer. It's not an LLM chatting about private credit in general; it's an analyst with access to all your portfolio data.

**"What's the data security model?"**
> JWT authentication, RBAC (Admin/Analyst roles), tenant-isolated vector search, audit logging on every action, bcrypt password hashing. No API keys in the codebase.

**"Can it handle real loan agreements?"**
> Yes — it handles PDFs, DOCX, and SEC EDGAR HTML filings. LlamaIndex handles parsing; Cohere handles embeddings and extraction.
