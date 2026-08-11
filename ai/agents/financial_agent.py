"""
Financial Metrics Extraction Agent — Sprint 3.
Uses Cohere Command A to parse financial statements and SEC filings,
complemented by regex financial statement parsing for robust metric extraction.
"""
import re
import json
import uuid
from typing import Any, Dict

import structlog
from ai.agents.base_agent import BaseAgent
from ai.prompts.financial_prompt import FINANCIAL_SYSTEM_PROMPT, FinancialPrompt

logger = structlog.get_logger(__name__)

FINANCIAL_KEYWORDS = [
    "revenue", "sales", "ebitda", "operating income", "net income",
    "total debt", "long-term debt", "interest expense", "cash and cash equivalents",
    "balance sheet", "statement of operations"
]


class FinancialAgent(BaseAgent):
    """
    Parses document text, extracts core accounting values using LLM or regex pattern matching,
    calculates derived credit ratios (leverage, interest coverage), and persists them.
    """

    @property
    def name(self) -> str:
        return "FinancialAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agreement_id = state.get("agreement_id")
        borrower_id = state.get("borrower_id")
        parsed_text = state.get("parsed_text", "")
        file_type = state.get("file_type", "loan_agreement")

        if not agreement_id or not borrower_id:
            state["status"] = "failed"
            state["error"] = "FinancialAgent: Missing agreement_id or borrower_id in state."
            return state

        logger.info("financial_agent.run_start", agreement_id=agreement_id)

        # 1. Update status
        await self._update_agreement_status(agreement_id, "extracting_financials")

        # 2. Grab relevant context text
        paragraphs = parsed_text.split("\n\n")
        relevant_paragraphs = [
            p for p in paragraphs
            if any(kw in p.lower() for kw in FINANCIAL_KEYWORDS)
        ]
        context_text = "\n\n".join(relevant_paragraphs if relevant_paragraphs else paragraphs)[:15000]

        metrics: Dict[str, Any] = {}

        # 3. Try LLM Extraction
        try:
            prompt = FinancialPrompt().format(parsed_text=context_text)
            response_json = await self._llm.generate_response(
                prompt=prompt,
                system_prompt=FINANCIAL_SYSTEM_PROMPT,
                temperature=0.0
            )

            metrics = self._parse_json_response(response_json)
        except Exception as exc:
            logger.warning("financial_agent.llm_failed_using_pattern_parser", error=str(exc))

        # 4. If LLM returned empty or missing core metrics, run Pattern Parser
        if not metrics or not any(metrics.get(k) for k in ["revenue", "ebitda", "net_income", "total_debt", "cash"]):
            logger.info("financial_agent.running_fallback_pattern_extractor")
            metrics = self._pattern_extract_financials(parsed_text)

        logger.info("financial_agent.extracted_metrics", metrics=metrics)

        if metrics:
            rev = metrics.get("revenue") or 0.0
            # Do NOT invent EBITDA from revenue — that creates false confidence.
            # If EBITDA was not extracted, store NULL, not a fabricated estimate.
            ebitda_raw = metrics.get("ebitda")
            ebitda = float(ebitda_raw) if ebitda_raw is not None else None
            total_debt = metrics.get("total_debt") or 0.0
            cash = metrics.get("cash") or 0.0
            net_income = metrics.get("net_income") or 0.0
            interest_expense_raw = metrics.get("interest_expense")
            interest_expense = float(interest_expense_raw) if interest_expense_raw is not None else None

            net_debt = total_debt - cash
            # RULE: None denominator → None ratio (not 0.0).
            if ebitda is not None and ebitda != 0:
                leverage_ratio: float | None = round(net_debt / ebitda, 2)
            else:
                leverage_ratio = None
            if interest_expense is not None and interest_expense != 0 and ebitda is not None:
                raw_cov = ebitda / interest_expense
                # Cap at 50x to prevent near-zero interest artefacts from propagating.
                interest_coverage: float | None = round(min(raw_cov, 50.0), 2)
            else:
                interest_coverage = None

            metrics_id = str(uuid.uuid4())
            await self._mcp.execute_tool(
                tool_name="postgres",
                operation="execute_write",
                params={
                    "query": """
                        INSERT INTO financial_metrics (
                            id, agreement_id, borrower_id, reporting_period, revenue, ebitda,
                            net_income, total_debt, cash, interest_expense, leverage_ratio,
                            interest_coverage, currency, extracted_at
                        ) VALUES (
                            :id, :agreement_id, :borrower_id, :reporting_period, :revenue, :ebitda,
                            :net_income, :total_debt, :cash, :interest_expense, :leverage_ratio,
                            :interest_coverage, :currency, NOW()
                        )
                    """,
                    "params": {
                        "id": metrics_id,
                        "agreement_id": agreement_id,
                        "borrower_id": borrower_id,
                        "reporting_period": metrics.get("reporting_period", "FY 10-K"),
                        "revenue": rev,
                        "ebitda": ebitda,
                        "net_income": net_income,
                        "total_debt": total_debt,
                        "cash": cash,
                        "interest_expense": interest_expense,
                        "leverage_ratio": leverage_ratio,
                        "interest_coverage": interest_coverage,
                        "currency": metrics.get("currency", "USD"),
                    }
                }
            )

            state["extracted_metrics"] = metrics

        # 5. Update agreement status to done
        await self._update_agreement_status(agreement_id, "done")
        state["status"] = "done"
        return state

    def _pattern_extract_financials(self, text: str) -> Dict[str, Any]:
        """Regex pattern extraction for SEC 10-K & financial statements."""
        extracted: Dict[str, Any] = {
            "reporting_period": "FY 10-K",
            "currency": "USD",
            "revenue": None,
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None
        }

        def parse_amount(val_str: str) -> float:
            clean = val_str.replace(",", "").replace("$", "").replace("(", "").replace(")", "").strip()
            try:
                num = float(clean)
                # SEC 10-Ks are reported in millions if numbers are 5-6 digits (e.g., $391,035 = $391.035B)
                if num > 1000 and num < 1000000:
                    return num * 1000000.0
                return num
            except ValueError:
                return 0.0

        # Revenue / Net Sales pattern
        rev_match = re.search(r"(?:total net sales|total sales|total revenue|net sales|revenue)[^\d]*\$?\s*([0-9,]{4,12})", text, re.IGNORECASE)
        if rev_match:
            extracted["revenue"] = parse_amount(rev_match.group(1))

        # Net Income pattern
        ni_match = re.search(r"(?:net income|net earnings)[^\d]*\$?\s*([0-9,]{4,12})", text, re.IGNORECASE)
        if ni_match:
            extracted["net_income"] = parse_amount(ni_match.group(1))

        # Operating Income / EBITDA proxy pattern
        ebitda_match = re.search(r"(?:operating income|ebitda|operating profit)[^\d]*\$?\s*([0-9,]{4,12})", text, re.IGNORECASE)
        if ebitda_match:
            extracted["ebitda"] = parse_amount(ebitda_match.group(1))

        # Cash pattern
        cash_match = re.search(r"(?:cash and cash equivalents|cash and marketable securities)[^\d]*\$?\s*([0-9,]{4,12})", text, re.IGNORECASE)
        if cash_match:
            extracted["cash"] = parse_amount(cash_match.group(1))

        # Debt pattern
        debt_match = re.search(r"(?:total debt|term debt|commercial paper|notes payable|term loan)[^\d]*\$?\s*([0-9,]{4,12})", text, re.IGNORECASE)
        if debt_match:
            extracted["total_debt"] = parse_amount(debt_match.group(1))

        # Interest Expense pattern
        int_match = re.search(r"(?:interest expense|interest paid)[^\d]*\$?\s*([0-9,]{3,10})", text, re.IGNORECASE)
        if int_match:
            extracted["interest_expense"] = parse_amount(int_match.group(1))

        return extracted

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```")[1].split("```")[0].strip()
        try:
            data = json.loads(clean)
            if isinstance(data, dict):
                return data.get("financial_metrics", data)
            return {}
        except Exception:
            return {}

    async def _update_agreement_status(self, agreement_id: str, status: str, error_msg: str | None = None) -> None:
        await self._mcp.execute_tool(
            tool_name="postgres",
            operation="execute_write",
            params={
                "query": """
                    UPDATE agreements
                    SET processing_status = :status,
                        processing_error = :error
                    WHERE id = :id
                """,
                "params": {
                    "id": agreement_id,
                    "status": status,
                    "error": error_msg,
                }
            }
        )
