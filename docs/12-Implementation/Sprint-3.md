# Sprint 3 — AI Risk Intelligence & Decision Engine

---

# Sprint Goal

Transform Covenexa from an AI document processing system into a complete AI-powered Credit Risk Intelligence Platform.

By the end of Sprint 3, the platform should not only extract information from documents but also understand borrower risk, monitor covenant compliance, predict future issues, explain its reasoning, and provide an enterprise-grade AI experience.

---

# Sprint Deliverables

Sprint 3 introduces the intelligence layer of Covenexa.

Major deliverables include:

- Financial Risk Engine
- Borrower Health Score
- Portfolio Risk Analytics
- Covenant Monitoring Engine
- Default Prediction
- Portfolio Stress Testing
- Explainable AI
- AI Recommendation Engine
- AI Copilot
- Neo4j Knowledge Graph Visualization
- Real-time Monitoring
- Alerts & Notifications
- Interactive Analytics Dashboard

---

# 1. Financial Analysis Engine

## Objective

Convert extracted financial statements into actionable financial intelligence.

Automatically calculate:

- Revenue
- EBITDA
- Net Income
- Cash
- Total Debt
- Net Debt
- Current Ratio
- Quick Ratio
- Debt-to-Equity
- Interest Coverage
- Leverage Ratio
- DSCR
- Free Cash Flow

Store all calculated metrics inside PostgreSQL.

Maintain historical financial snapshots.

---

# 2. Borrower Health Score

## Objective

Generate an overall borrower health score ranging from 0–100.

The score should consider:

- Financial performance
- Historical trends
- Covenant compliance
- Industry risk
- Liquidity
- Debt profile
- Cash flow
- Payment history
- AI confidence score

Health Categories

90-100 → Excellent

75-89 → Good

60-74 → Moderate

40-59 → High Risk

0-39 → Critical

Dashboard should display

- Current Score
- Trend
- Historical graph
- Risk explanation

---

# 3. Portfolio Risk Analytics

Dashboard should display

- Portfolio Risk Score
- Average Borrower Score
- High Risk Borrowers
- Active Covenant Breaches
- Upcoming Reporting Obligations
- Industry Distribution
- Geographic Distribution
- Total Exposure

Replace the current "Risk Low" badge with a numerical portfolio risk indicator.

Example

Portfolio Risk

18 /100

LOW

---

# 4. Covenant Monitoring Engine

Automatically monitor

Maintenance Covenants

Reporting Covenants

Negative Covenants

Affirmative Covenants

Incurrence Covenants

For every covenant determine

Healthy

Warning

Breach

Critical

Each decision must include

Reason

Supporting financial values

Supporting covenant text

Source document

Confidence score

---

# 5. Default Prediction Engine

Develop an ML-based borrower default prediction module.

Inputs

Financial ratios

Borrower Health

Historical financials

Industry

Macroeconomic assumptions

Outputs

Default Probability

Risk Category

Confidence Score

Top contributing risk factors

---

# 6. Portfolio Stress Testing

Allow simulation of scenarios such as

Revenue decreases

EBITDA decreases

Interest rates increase

Debt increases

Operating expenses increase

Economic recession

Display

Predicted covenant breaches

Borrowers at risk

Portfolio losses

Expected default probability

Interactive scenario comparison charts.

---

# 7. Explainable AI

Every AI-generated prediction must explain

Why the model reached this conclusion

Important financial metrics

Relevant covenant clauses

Supporting document references

Confidence level

This makes the platform suitable for enterprise risk teams.

---

# 8. AI Recommendation Engine

Generate recommendations such as

Increase monitoring

Escalate to analyst

Request updated financials

Renegotiate covenant

Reduce exposure

Approve

Reject

Each recommendation must include detailed reasoning.

---

# 9. AI Copilot

Implement a conversational AI assistant.

Users should be able to ask

"Summarize this loan."

"List all maintenance covenants."

"Which covenant is closest to breach?"

"Why is borrower risk increasing?"

"What happens if EBITDA falls by 20%?"

"What are the reporting obligations?"

The assistant should use

Hybrid GraphRAG

Neo4j

Pinecone

LLM

Structured SQL retrieval

---

# 10. Neo4j Knowledge Graph Visualization

Create an interactive graph showing

Borrower

↓

Loan

↓

Agreement

↓

Financial Statements

↓

Extracted Covenants

↓

Financial Metrics

↓

Events

↓

Violations

Users should be able to click nodes to inspect relationships.

---

# 11. Dashboard Enhancements

Upgrade the dashboard with

Borrower Health Score

Portfolio Risk Score

AI Insights

Active Alerts

Upcoming Reporting Dates

Default Probability

Risk Trend

Financial Charts

Stress Test Results

Top Risk Borrowers

Remove empty placeholders and replace them with real analytics.

---

# 12. AI Insights Panel

Add a dedicated AI Insights section.

Example

⚠ EBITDA declined 18%

⚠ Debt increased 12%

⚠ Two reporting covenants due within 14 days

⚠ Borrower Health decreased from 82 → 69

✓ Portfolio risk remains LOW

This panel should become the first thing users notice after logging in.

---

# 13. Real-Time Monitoring

Continuously monitor

New uploaded agreements

Financial statement updates

Covenant compliance

Borrower health

Portfolio exposure

Automatically trigger AI re-analysis.

---

# 14. Alerts & Notifications

Generate alerts for

Covenant Breach

Upcoming Reporting Deadlines

Financial Deterioration

High Default Probability

Material Portfolio Changes

Severity Levels

Info

Warning

High

Critical

---

# 15. Charts & Visual Analytics

Replace static numbers with charts.

Examples

Revenue Trend

EBITDA Trend

Debt Trend

Borrower Health Trend

Risk Distribution

Industry Exposure

Portfolio Allocation

Covenant Status Distribution

---

# 16. Testing

Unit tests

Integration tests

Agent tests

Graph retrieval tests

Recommendation tests

Health score validation

Risk score validation

---

# Documentation

Update

Architecture diagrams

AI workflow

Knowledge Graph documentation

Borrower Health formula

Risk engine documentation

Copilot workflow

---

# Definition of Done

Sprint 3 is complete only if

✓ Borrower Health Score is operational

✓ Portfolio Risk Score is visible

✓ AI Insights panel works

✓ AI Copilot answers questions

✓ Graph visualization works

✓ Stress testing is operational

✓ Default prediction works

✓ Recommendation engine works

✓ Charts display real analytics

✓ Alerts trigger automatically

✓ Explainable AI provides reasoning

✓ Dashboard displays enterprise-level intelligence

✓ Platform behaves like a commercial Credit Risk Intelligence solution.

# 17. SEC EDGAR Filing URL Support

## Objective

Enable analysts to analyze SEC filings directly from their EDGAR URL without manually downloading documents.

This feature should support

- SEC 10-K
- SEC 10-Q
- 8-K
- Credit Agreements
- Exhibits
- Indentures
- Loan Agreements
- Other EDGAR HTML filings

---

## User Workflow

Dashboard

↓

Paste SEC Filing URL

↓

Click "Analyze"

↓

System validates URL

↓

Download filing

↓

Parse HTML

↓

Extract document text

↓

Run AI pipeline

↓

Generate Knowledge Graph

↓

Extract Financial Metrics

↓

Extract Covenants

↓

Store Results

↓

Display Dashboard

---

## Supported Sources

SEC EDGAR

Examples

https://www.sec.gov/Archives/...

https://www.sec.gov/ixviewer/...

https://www.sec.gov/Archives/edgar/data/...

---

## Backend Components

Create

SECDownloader

Responsible for

- URL validation
- HTTP download
- Retry mechanism
- User-Agent handling
- Rate limiting

---

Create

HTMLParser

Responsible for

- BeautifulSoup parsing
- Removing navigation
- Removing scripts
- Removing styles
- Extracting clean text
- Preserving headings
- Preserving tables where possible

---

Create

SECDocumentPipeline

The pipeline should automatically decide

if PDF

↓

OCR Pipeline

if DOCX

↓

DOCX Parser

if HTML

↓

SEC HTML Parser

if TXT

↓

Text Parser

All formats should converge into the same semantic chunking pipeline.

---

## Frontend Changes

Replace

Upload Document

with

Upload Document

OR

Analyze SEC Filing URL

Input

--------------------------------------
Paste SEC Filing URL
--------------------------------------

[ Analyze Filing ]

---

## AI Pipeline

Downloaded filing

↓

HTML Cleaning

↓

Semantic Chunking

↓

Embedding

↓

Vector Storage

↓

Knowledge Graph

↓

Financial Extraction

↓

Covenant Extraction

↓

Borrower Health

↓

Risk Engine

↓

Dashboard

---

## Metadata

Store

Original URL

Filing Type

Company

CIK

Accession Number

Filing Date

Document Type

Company Name

Source = SEC

This metadata should be searchable.

---

## Future Compatibility

The ingestion architecture should allow future support for

- Moody's
- Fitch
- S&P Global
- Bloomberg
- Refinitiv
- Internal Bank Document Portals
- SharePoint
- AWS S3
- Google Drive

without changing the downstream AI pipeline.

---

## Definition of Done

✓ User pastes an EDGAR URL.

✓ Filing downloads automatically.

✓ HTML is parsed correctly.

✓ AI pipeline runs exactly like uploaded PDFs.

✓ Financial metrics extracted.

✓ Covenants extracted.

✓ Neo4j graph created.

✓ Pinecone indexed.

✓ Dashboard updated automatically.

✓ Original SEC URL stored in database.

┌───────────────────────────────────────────────┐
│               Document Ingestion              │
├───────────────────────────────────────────────┤

① Upload PDF / DOCX / XLSX / CSV

[ Drag & Drop ]

───────────────────────────────────────────────

② Analyze SEC Filing

[ Paste EDGAR URL......................... ]

[ Analyze Filing ]

───────────────────────────────────────────────

③ Connect Data Source (Sprint 4)

○ SharePoint

○ S3

○ Google Drive

○ Internal Repository
