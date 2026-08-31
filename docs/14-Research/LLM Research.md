# LLM Research Notes

## Model Selection: Cohere Command A

### Why Cohere over OpenAI GPT-4?
- Competitive performance on structured extraction tasks
- Cohere's `embed-english-v3.0` is best-in-class for legal/financial semantic search
- Integrated ecosystem: same provider for LLM + embeddings = simpler billing and integration
- Good JSON output reliability

### Cohere Command A Capabilities Used
- **Structured extraction:** covenant and financial metric extraction from legal text
- **Synthesis:** Copilot response generation with citation awareness
- **Recommendations:** generating prioritized credit action items

### Temperature Settings
- Extraction tasks: `temperature=0.1` — near-deterministic for structured data
- Copilot synthesis: `temperature=0.3` — some creativity allowed in phrasing
- Recommendations: `temperature=0.2` — structured but varied phrasing

## Mock Mode

When `COHERE_API_KEY` is not set:
- All LLM calls return deterministic mock responses
- Embeddings return a 1024-dim vector (small perturbation from zero)
- Allows full development and testing without API costs

## Prompt Reliability Notes

- Cohere Command A reliably returns JSON when explicitly instructed
- Extraction prompts must specify: "Return ONLY a JSON object. No explanations."
- Multi-covenant extraction: tested up to 15 covenants per chunk reliably

## Alternative Models Considered

| Model | Pro | Con |
|:------|:----|:----|
| OpenAI GPT-4o | Best overall quality | Higher cost, no integrated embedding |
| Anthropic Claude 3.5 | Strong reasoning | No integrated embedding model |
| Mistral | Open-source option | Lower structured extraction quality |
| Llama 3 (local) | No API cost | Requires GPU infrastructure |
