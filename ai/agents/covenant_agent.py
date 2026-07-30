"""
Covenant Extraction Agent.
Uses Cohere Command A to parse text chunks, extract covenants,
and save them to PostgreSQL (relational) and Neo4j (graph).
"""
import json
import uuid
from typing import Any, Dict

import structlog
from ai.agents.base_agent import BaseAgent
from ai.prompts.covenant_prompt import COVENANT_SYSTEM_PROMPT, CovenantPrompt

logger = structlog.get_logger(__name__)

COVENANT_KEYWORDS = ["covenant", "ratio", "threshold", "minimum", "maximum", "debt", "leverage", "coverage", "net worth"]


class CovenantAgent(BaseAgent):
    """
    Scans document chunks, uses LLM to identify financial and legal covenants,
    and maps them into the relational DB and Knowledge Graph.
    """

    @property
    def name(self) -> str:
        return "CovenantAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agreement_id = state.get("agreement_id")
        borrower_id = state.get("borrower_id")
        parsed_text = state.get("parsed_text", "")

        if not agreement_id or not borrower_id:
            state["status"] = "failed"
            state["error"] = "CovenantAgent: Missing agreement_id or borrower_id in state."
            return state

        logger.info("covenant_agent.run_start", agreement_id=agreement_id)

        # 1. Update status
        await self._update_agreement_status(agreement_id, "extracting")

        # 2. Filter chunks or text to extract covenants
        # For simplicity, if the text is small we process it, or we filter relevant paragraphs.
        paragraphs = parsed_text.split("\n\n")
        relevant_paragraphs = [
            p for p in paragraphs 
            if any(kw in p.lower() for kw in COVENANT_KEYWORDS)
        ]
        
        # Join into a context window up to 12000 chars to avoid token blowout
        context_text = "\n\n".join(relevant_paragraphs)[:12000]

        if not context_text.strip():
            logger.warning("covenant_agent.no_relevant_covenant_text_found")
            await self._update_agreement_status(agreement_id, "covenants_extracted")
            state["extracted_covenants"] = []
            return state

        # 3. Call LLM for structured extraction
        try:
            prompt = CovenantPrompt().format(parsed_text=context_text)
            response_json = await self._llm.generate_response(
                prompt=prompt,
                system_prompt=COVENANT_SYSTEM_PROMPT,
                temperature=0.0
            )

            # Parse JSON safely
            extracted = self._parse_json_response(response_json)
            covenants_list = extracted.get("covenants", [])
            logger.info("covenant_agent.extracted_covenants", count=len(covenants_list))

            # 4. Save to PostgreSQL and Neo4j via MCP
            for cov in covenants_list:
                cov_id = str(uuid.uuid4())
                
                # Relational insert
                await self._mcp.execute_tool(
                    tool_name="postgres",
                    operation="execute_write",
                    params={
                        "query": """
                            INSERT INTO covenants (
                                id, agreement_id, borrower_id, name, covenant_type, formula,
                                threshold, threshold_direction, frequency, cure_period_days,
                                is_event_of_default, amendment_references, raw_text, extracted_at
                            ) VALUES (
                                :id, :agreement_id, :borrower_id, :name, :covenant_type, :formula,
                                :threshold, :threshold_direction, :frequency, :cure_period_days,
                                :is_event_of_default, :amendment_references, :raw_text, NOW()
                            )
                        """,
                        "params": {
                            "id": cov_id,
                            "agreement_id": agreement_id,
                            "borrower_id": borrower_id,
                            "name": cov.get("name", "Unknown Covenant"),
                            "covenant_type": cov.get("covenant_type", "maintenance"),
                            "formula": cov.get("formula"),
                            "threshold": cov.get("threshold"),
                            "threshold_direction": cov.get("threshold_direction"),
                            "frequency": cov.get("frequency", "quarterly"),
                            "cure_period_days": cov.get("cure_period_days"),
                            "is_event_of_default": cov.get("is_event_of_default", False),
                            "amendment_references": cov.get("amendment_references"),
                            "raw_text": cov.get("raw_text"),
                        }
                    }
                )

                # Neo4j Graph insertion via MCP Neo4j Tool
                try:
                    # Upsert Covenant node
                    await self._mcp.execute_tool(
                        tool_name="neo4j",
                        operation="upsert_node",
                        params={
                            "label": "Covenant",
                            "properties": {
                                "id": cov_id,
                                "name": cov.get("name"),
                                "covenant_type": cov.get("covenant_type"),
                                "formula": cov.get("formula", ""),
                                "threshold": cov.get("threshold", 0.0),
                            },
                            "match_key": "id"
                        }
                    )
                    # Relate Agreement -> HAS_COVENANT -> Covenant
                    await self._mcp.execute_tool(
                        tool_name="neo4j",
                        operation="upsert_relation",
                        params={
                            "from_id": agreement_id,
                            "to_id": cov_id,
                            "relation_type": "HAS_COVENANT",
                            "from_label": "Agreement",
                            "to_label": "Covenant",
                            "properties": {}
                        }
                    )
                    # Relate Borrower -> HAS_COVENANT -> Covenant
                    await self._mcp.execute_tool(
                        tool_name="neo4j",
                        operation="upsert_relation",
                        params={
                            "from_id": borrower_id,
                            "to_id": cov_id,
                            "relation_type": "HAS_COVENANT",
                            "from_label": "Borrower",
                            "to_label": "Covenant",
                            "properties": {}
                        }
                    )
                except Exception as g_err:
                    logger.warning("covenant_agent.graph_write_failed", error=str(g_err))

            # 5. Update agreement status to covenants_extracted
            await self._update_agreement_status(agreement_id, "covenants_extracted")
            state["extracted_covenants"] = covenants_list
            state["status"] = "covenants_extracted"

        except Exception as exc:
            logger.error("covenant_agent.extraction_failed", error=str(exc))
            await self._update_agreement_status(agreement_id, "failed", f"Covenant extraction error: {exc}")
            state["status"] = "failed"
            state["error"] = f"Covenant extraction failed: {exc}"

        return state

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Strip markdown delimiters if present and load JSON."""
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(clean)
        except Exception:
            # Fallback simple dictionary structure if LLM outputs dirty text
            return {"covenants": []}

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
