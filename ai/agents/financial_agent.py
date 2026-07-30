"""
Financial Metrics Extraction Agent.
Uses Cohere Command A to parse financial statements, calculate derived ratios,
and save structured records to PostgreSQL.
"""
import json
import uuid
from typing import Any, Dict

import structlog
from ai.agents.base_agent import BaseAgent
from ai.prompts.financial_prompt import FINANCIAL_SYSTEM_PROMPT, FinancialPrompt

logger = structlog.get_logger(__name__)

FINANCIAL_KEYWORDS = ["revenue", "ebitda", "net income", "debt", "interest", "cash", "statement", "balance sheet"]


class FinancialAgent(BaseAgent):
    """
    Parses document text, extracts core accounting values using LLM,
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

        # We extract financial metrics if it's explicitly a financial statement,
        # OR if the file content contains financial keywords (to be thorough).
        is_financial_doc = (
            file_type == "financial_statement" or
            any(kw in parsed_text.lower() for kw in FINANCIAL_KEYWORDS)
        )

        if not is_financial_doc:
            logger.info("financial_agent.skip", reason="Not identified as a financial statement")
            await self._update_agreement_status(agreement_id, "done")
            state["status"] = "done"
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
        context_text = "\n\n".join(relevant_paragraphs)[:12000]

        if not context_text.strip():
            logger.warning("financial_agent.no_relevant_financial_text_found")
            await self._update_agreement_status(agreement_id, "done")
            state["status"] = "done"
            return state

        # 3. Call LLM
        try:
            prompt = FinancialPrompt().format(parsed_text=context_text)
            response_json = await self._llm.generate_response(
                prompt=prompt,
                system_prompt=FINANCIAL_SYSTEM_PROMPT,
                temperature=0.0
            )

            # Parse JSON safely
            metrics = self._parse_json_response(response_json)
            logger.info("financial_agent.extracted_metrics", metrics=metrics)

            if metrics:
                # Calculate derived ratios
                ebitda = metrics.get("ebitda")
                total_debt = metrics.get("total_debt")
                interest_expense = metrics.get("interest_expense")

                leverage_ratio = None
                if total_debt is not None and ebitda:
                    leverage_ratio = float(total_debt) / float(ebitda)

                interest_coverage = None
                if ebitda is not None and interest_expense:
                    interest_coverage = float(ebitda) / float(interest_expense)

                # Persist to financial_metrics table
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
                            "reporting_period": metrics.get("reporting_period", "LTM"),
                            "revenue": metrics.get("revenue"),
                            "ebitda": ebitda,
                            "net_income": metrics.get("net_income"),
                            "total_debt": total_debt,
                            "cash": metrics.get("cash"),
                            "interest_expense": interest_expense,
                            "leverage_ratio": leverage_ratio,
                            "interest_coverage": interest_coverage,
                            "currency": metrics.get("currency", "USD"),
                        }
                    }
                )

                state["extracted_metrics"] = metrics

            # 4. Update agreement status to done
            await self._update_agreement_status(agreement_id, "done")
            state["status"] = "done"

        except Exception as exc:
            logger.error("financial_agent.extraction_failed", error=str(exc))
            await self._update_agreement_status(agreement_id, "failed", f"Financial extraction error: {exc}")
            state["status"] = "failed"
            state["error"] = f"Financial extraction failed: {exc}"

        return state

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(clean)
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
