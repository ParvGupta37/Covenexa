# Evaluation Benchmarks

## Current Status (v1.0)

Formal evaluation benchmarks for LLM extraction quality are **not implemented** in v1.0.

## What is Measured

| Metric | Method | Status |
|:-------|:-------|:-------|
| Backend test pass rate | pytest | 92/92 (100%) |
| Engine accuracy | Unit tests with known inputs/outputs | ✅ |
| Covenant extraction accuracy | Manual spot-check | Not automated |
| Financial extraction accuracy | Manual spot-check | Not automated |
| Copilot response quality | Manual evaluation | Not automated |

## Planned Evaluation (v1.1)

### Covenant Extraction Benchmark
- Dataset: 20 real loan agreements with ground-truth covenant annotations
- Metrics: Precision, Recall, F1 for covenant detection
- Metric field accuracy: exact match on `metric`, `threshold`, `operator`

### Financial Extraction Benchmark
- Dataset: 20 financial statements with ground-truth financial figures
- Metrics: MAE (Mean Absolute Error) on numeric fields
- Field coverage: % of fields correctly extracted vs. null

### Copilot Response Quality
- Human evaluation rubric: Accuracy, Relevance, Citation correctness
- Scale: 1–5 per dimension
- Target: ≥4.0 on all dimensions for common analyst queries
