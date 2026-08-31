# Agentic AI Research Notes

## Key Papers & Concepts

### ReAct (Reasoning + Acting)
- Paper: "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)
- Relevance: Covenexa's agents use a reason-then-act pattern for covenant extraction
- LangGraph implements this via node-level state management

### Multi-Agent Systems
- Paper: "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"
- Covenexa uses LangGraph (not AutoGen) but follows the same specialization principle
- Each agent has a single responsibility → better than one monolithic agent

### Retrieval-Augmented Generation
- Paper: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
- Covenexa extends basic RAG to Hybrid GraphRAG: SQL + Vector + Graph

### GraphRAG
- Microsoft GraphRAG paper (2024) — using knowledge graphs to improve RAG accuracy
- Covenexa's graph retriever (Neo4j planned) follows this pattern
- Neo4j enables multi-hop traversal that flat vector search cannot do

## LangGraph-Specific Notes

- LangGraph = stateful directed graph for multi-step agent workflows
- Each node = an agent or computation step
- State = dict shared across all nodes in the graph
- Edges = conditional or unconditional transitions
- Used in: DocumentWorkflow, ComplianceWorkflow

## Key Design Insight

**Agents should extract and reason. Engines should compute.**

Mixing LLM-based reasoning with financial math leads to hallucinated ratios. Covenexa separates:
- **Agents (LLM):** extract text → structured data
- **Engines (Python):** compute ratios, scores, predictions deterministically
