# Neo4j Schema

## Purpose

Represents relationships between legal documents, covenants, borrowers, and financial definitions.

## Nodes

- Borrower
- Loan
- Agreement
- Covenant
- Definition
- Financial Metric
- Amendment

## Relationships

Borrower
OWNS
Loan

Loan
HAS
Agreement

Agreement
CONTAINS
Covenant

Agreement
DEFINES
Definition

Covenant
USES
Definition

Borrower
REPORTS
Financial Metric

Agreement
UPDATED_BY
Amendment

## Why Neo4j?

Graph databases make relationship traversal much faster than relational databases for connected legal and financial data.