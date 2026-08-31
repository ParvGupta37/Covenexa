# Agent Tests

> Full testing documentation is in [Unit Tests.md](./Unit%20Tests.md).

## Agent-Specific Test Coverage

### CovenantAgent
- `test_covenant_agent_has_no_hardcoded_formula_fallbacks` ✅
- `test_covenant_agent_has_no_hardcoded_threshold_fallbacks` ✅

### FinancialAgent
- `test_none_fields_preserved_not_coerced_to_zero` ✅
- Financial extraction mock returns null for missing fields ✅

### CopilotAgent
- `test_copilot_agent_handles_missing_session_state` ✅
- Returns structured response when no API key (mock mode) ✅

### DocumentAgent
- Pipeline state transitions tested: pending → processing → completed ✅
- Chunk embedding mock: produces deterministic chunk count ✅

### All Agents
- No real API key required — all external calls mock-patched ✅
- No real DB required — mock sessions used ✅
