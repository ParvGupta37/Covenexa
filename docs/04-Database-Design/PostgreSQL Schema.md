# PostgreSQL Schema

## Purpose

Stores structured business data for the platform.

## Core Tables

### Users
- id
- name
- email
- password_hash
- role
- created_at

### Organizations
- id
- name
- industry
- created_at

### Borrowers
- id
- organization_id
- company_name
- sector
- country
- risk_rating

### Loans
- id
- borrower_id
- agreement_id
- principal_amount
- interest_rate
- start_date
- maturity_date
- status

### Agreements
- id
- loan_id
- version
- file_path
- upload_date

### Financial Statements
- id
- borrower_id
- reporting_period
- revenue
- ebitda
- total_debt
- cash
- uploaded_at

### Compliance Results
- id
- borrower_id
- covenant_id
- status
- headroom
- checked_at

### Reports
- id
- borrower_id
- report_type
- generated_at
- report_path

## Relationships

Organization
→ Borrowers

Borrower
→ Loans

Loan
→ Agreement

Borrower
→ Financial Statements

Borrower
→ Compliance Results

Borrower
→ Reports