# RAG Pipeline

## Purpose

Provide accurate and explainable answers by combining retrieved company data with LLM reasoning.

## Workflow

User Query

↓

Planner Agent

↓

Retrieve Relevant Context

- Vector Database
- Knowledge Graph
- PostgreSQL

↓

Context Builder

↓

LLM

↓

Response with Citations

## Benefits

- Reduces hallucinations
- Uses latest portfolio data
- Provides explainable responses