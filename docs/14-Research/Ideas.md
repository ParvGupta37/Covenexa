# Ideas & Future Exploration

> Loose ideas, experiments, and "what if" thinking. Not committed to the roadmap.

---

## Product Ideas

- **Portfolio-level AI narrative** — one AI paragraph summarizing the entire fund's risk posture weekly
- **Covenant breach prediction** — predict which covenants will breach in 2 quarters based on trend
- **Peer benchmarking** — compare borrower ratios against sector medians
- **LP reporting mode** — restricted read-only view for limited partners
- **Slack/Teams integration** — push critical alerts to Slack channels
- **Email digest** — daily/weekly portfolio summary email to portfolio managers

---

## Technical Ideas

- **GraphRAG with Neo4j multi-hop** — answer "which borrowers share the same legal counsel?" via graph traversal
- **Fine-tune Cohere on covenant clauses** — improve extraction accuracy with domain-specific training data
- **Streaming copilot** — stream LLM response tokens via SSE instead of waiting for full completion
- **Multi-modal documents** — handle scanned/image PDFs using OCR (Tesseract or AWS Textract)
- **Agent memory** — LangGraph checkpoints for persistent cross-session Copilot memory
- **Automated financial ratio forecasting** — linear regression on historical quarterly ratios

---

## Infrastructure Ideas

- **Multi-region** — US + EU deployments for data residency compliance
- **Event sourcing** — replace direct DB writes with event log as source of truth
- **CQRS** — separate command models from query models for large-scale read optimization
