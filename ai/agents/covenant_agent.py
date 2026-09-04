"""
Covenant Extraction Agent.
Uses Cohere Command A to parse text chunks and extract covenants,
complemented by legal pattern-matching for robust covenant clause extraction.
"""
import re
import json
import uuid
from typing import Any, Dict, List

import structlog
from ai.agents.base_agent import BaseAgent
from ai.prompts.covenant_prompt import COVENANT_SYSTEM_PROMPT, CovenantPrompt

logger = structlog.get_logger(__name__)

COVENANT_KEYWORDS = [
    "covenant", "ratio", "threshold", "minimum", "maximum",
    "debt", "leverage", "coverage", "net worth", "ebitda", "indebtedness",
    "capitalization", "tangible net worth", "fixed charge", "liquidity",
    "negative covenant", "affirmative covenant", "financial covenant",
    "reporting requirement"
]


class CovenantAgent(BaseAgent):
    """
    Scans document chunks, uses LLM or pattern-matching to identify financial and legal covenants,
    and maps them into PostgreSQL and Knowledge Graph.
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

        # 2. Filter paragraphs & covenant sections (handles both \n\n and \n text formats)
        raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", parsed_text) if p.strip()]
        if len(raw_paragraphs) <= 3 and parsed_text:
            lines = [l.strip() for l in parsed_text.splitlines() if l.strip()]
            raw_paragraphs = ["\n".join(lines[i:i+8]) for i in range(0, len(lines), 5)]

        relevant_paragraphs = [
            p for p in raw_paragraphs 
            if any(kw in p.lower() for kw in COVENANT_KEYWORDS)
        ]
        context_text = "\n\n".join(relevant_paragraphs if relevant_paragraphs else raw_paragraphs)[:25000]

        covenants_list: List[Dict[str, Any]] = []

        # 3. Call LLM for structured extraction
        try:
            prompt = CovenantPrompt().format(parsed_text=context_text)
            response_json = await self._llm.generate_response(
                prompt=prompt,
                system_prompt=COVENANT_SYSTEM_PROMPT,
                temperature=0.0
            )

            extracted = self._parse_json_response(response_json)
            covenants_list = extracted.get("covenants", [])
        except Exception as exc:
            logger.warning("covenant_agent.llm_failed_using_pattern_parser", error=str(exc))

        # 4. Fallback pattern-matching if LLM returned no covenants
        if not covenants_list:
            covenants_list = self._pattern_extract_covenants(parsed_text)

        logger.info("covenant_agent.extracted_covenants", count=len(covenants_list))

        # 5. Save to PostgreSQL and Neo4j via MCP
        # Clean up any existing covenants extracted for this agreement (Idempotency)
        if agreement_id:
            try:
                await self._mcp.execute_tool(
                    tool_name="postgres",
                    operation="execute_write",
                    params={
                        "query": "DELETE FROM covenants WHERE agreement_id = :aid",
                        "params": {"aid": agreement_id}
                    }
                )
            except Exception as exc:
                logger.warning("covenant_agent.cleanup_failed", error=str(exc))

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
                            is_event_of_default, raw_text, extracted_at
                        ) VALUES (
                            :id, :agreement_id, :borrower_id, :name, :covenant_type, :formula,
                            :threshold, :threshold_direction, :frequency, :cure_period_days,
                            :is_event_of_default, :raw_text, NOW()
                        )
                    """,
                    "params": {
                        "id": cov_id,
                        "agreement_id": agreement_id,
                        "borrower_id": borrower_id,
                        "name": cov.get("name", "Financial Covenant"),
                        "covenant_type": cov.get("covenant_type", "maintenance"),
                        "formula": cov.get("formula"),
                        "threshold": cov.get("threshold"),
                        "threshold_direction": cov.get("threshold_direction"),
                        "frequency": cov.get("frequency", "quarterly"),
                        "cure_period_days": cov.get("cure_period_days", 30),
                        "is_event_of_default": cov.get("is_event_of_default", False),
                        "raw_text": cov.get("raw_text", ""),
                    }
                }
            )

            # Knowledge Graph node & relations
            try:
                await self._mcp.execute_tool(
                    tool_name="neo4j",
                    operation="upsert_node",
                    params={
                        "node_id": cov_id,
                        "label": "Covenant",
                        "properties": {
                            "name": cov.get("name"),
                            "covenant_type": cov.get("covenant_type"),
                            "threshold": cov.get("threshold"),
                            "threshold_direction": cov.get("threshold_direction"),
                            "frequency": cov.get("frequency"),
                        }
                    }
                )
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

        # 6. Update agreement status to covenants_extracted
        await self._update_agreement_status(agreement_id, "covenants_extracted")
        state["extracted_covenants"] = covenants_list
        state["status"] = "covenants_extracted"
        return state

    def _pattern_extract_covenants(self, text: str) -> List[Dict[str, Any]]:
        """
        Legal covenant pattern extraction.
        Extracts genuine covenants with disclosed numerical thresholds or explicitly defined
        covenant clauses without disclosed numerical thresholds (setting threshold=None).
        Never fabricates covenants or thresholds for generic loan/note mentions.
        """
        found: List[Dict[str, Any]] = []
        covenant_names_seen = set()

        def _add_covenant(cov: Dict[str, Any]):
            name = cov.get("name")
            if name and name not in covenant_names_seen:
                covenant_names_seen.add(name)
                found.append(cov)

        # 1. Maximum Consolidated Senior Secured Leverage Ratio
        # 1a. Numeric match (must be followed by ratio notation :1, x, times)
        sr_sec_lev_num = re.search(
            r"(?:consolidated\s+senior\s+secured\s+leverage|senior\s+secured\s+leverage)[^\d]{1,150}?(\d+(?:\.\d+)?)\s*(?::\s*1(?:\.0+)?|\s*to\s*1(?:\.0+)?|\s*x\b|\s*times\b)",
            text,
            re.IGNORECASE
        )
        if sr_sec_lev_num:
            thresh = float(sr_sec_lev_num.group(1))
            _add_covenant({
                "name": "Maximum Consolidated Senior Secured Leverage Ratio",
                "covenant_type": "maintenance",
                "formula": "Consolidated Senior Secured Debt / EBITDA",
                "threshold": thresh,
                "threshold_direction": "max",
                "frequency": "quarterly",
                "raw_text": sr_sec_lev_num.group(0).strip()
            })
        else:
            # 1b. Clause without disclosed numeric threshold (requires explicit covenant/requirement/maintenance language)
            sr_sec_lev_clause = re.search(
                r"(?:covenant[s]?[^;\.\n]*?(?:require[s]?|maintain[ing]?|including|subject to)[^;\.\n]*?|maintain[ing]?(?:\s+(?:a|the))?\s+|shall not permit[^;\.\n]*?)(?:a\s+)?(maximum\s+(?:consolidated\s+)?senior\s+secured\s+leverage\s+ratio|consolidated\s+senior\s+secured\s+leverage\s+ratio|maximum\s+senior\s+secured\s+leverage\s+ratio)",
                text,
                re.IGNORECASE
            )
            if sr_sec_lev_clause:
                _add_covenant({
                    "name": "Maximum Consolidated Senior Secured Leverage Ratio",
                    "covenant_type": "maintenance",
                    "formula": "Consolidated Senior Secured Debt / EBITDA",
                    "threshold": None,
                    "threshold_direction": "max",
                    "frequency": "quarterly",
                    "raw_text": sr_sec_lev_clause.group(0).strip()
                })

        # 2. Maximum Consolidated Leverage Ratio (general)
        # 2a. Numeric match (must be followed by ratio notation :1, x, times)
        lev_match = re.search(
            r"(?:consolidated\s+leverage\s+ratio|consolidated\s+leverage|leverage\s+ratio|debt\s+to\s+ebitda)[^\d]{1,150}?(\d+(?:\.\d+)?)\s*(?::\s*1(?:\.0+)?|\s*to\s*1(?:\.0+)?|\s*x\b|\s*times\b)",
            text,
            re.IGNORECASE
        )
        if lev_match and "Maximum Consolidated Senior Secured Leverage Ratio" not in covenant_names_seen:
            thresh = float(lev_match.group(1))
            _add_covenant({
                "name": "Maximum Consolidated Leverage Ratio",
                "covenant_type": "maintenance",
                "formula": "Total Net Debt / EBITDA",
                "threshold": thresh,
                "threshold_direction": "max",
                "frequency": "quarterly",
                "raw_text": lev_match.group(0).strip()
            })
        elif "Maximum Consolidated Senior Secured Leverage Ratio" not in covenant_names_seen:
            # 2b. Clause without numeric threshold
            lev_clause = re.search(
                r"(?:covenant[s]?[^;\.\n]*?(?:require[s]?|maintain[ing]?|including|subject to)[^;\.\n]*?|maintain[ing]?(?:\s+(?:a|the))?\s+|shall not permit[^;\.\n]*?)(?:a\s+)?(maximum\s+(?:consolidated\s+)?leverage\s+ratio|consolidated\s+leverage\s+ratio)",
                text,
                re.IGNORECASE
            )
            if lev_clause:
                _add_covenant({
                    "name": "Maximum Consolidated Leverage Ratio",
                    "covenant_type": "maintenance",
                    "formula": "Total Net Debt / EBITDA",
                    "threshold": None,
                    "threshold_direction": "max",
                    "frequency": "quarterly",
                    "raw_text": lev_clause.group(0).strip()
                })

        # 3. Minimum Interest Coverage Ratio
        # 3a. Numeric match
        cov_match = re.search(
            r"(?:interest\s+coverage\s+ratio|interest\s+coverage|fixed\s+charge\s+coverage\s+ratio|fixed\s+charge\s+coverage|dscr)[^\d]{1,150}?(\d+(?:\.\d+)?)\s*(?::\s*1(?:\.0+)?|\s*to\s*1(?:\.0+)?|\s*x\b|\s*times\b)",
            text,
            re.IGNORECASE
        )
        if cov_match:
            thresh = float(cov_match.group(1))
            _add_covenant({
                "name": "Minimum Interest Coverage Ratio",
                "covenant_type": "maintenance",
                "formula": "EBITDA / Interest Expense",
                "threshold": thresh,
                "threshold_direction": "min",
                "frequency": "quarterly",
                "raw_text": cov_match.group(0).strip()
            })
        else:
            # 3b. Clause without numeric threshold
            cov_clause = re.search(
                r"(?:covenant[s]?[^;\.\n]*?(?:require[s]?|maintain[ing]?|including|subject to)[^;\.\n]*?|maintain[ing]?(?:\s+(?:a|the))?\s+|shall maintain[^;\.\n]*?)(?:a\s+)?(minimum\s+interest\s+coverage(?:\s+ratio)?|interest\s+coverage\s+ratio|minimum\s+fixed\s+charge\s+coverage(?:\s+ratio)?)",
                text,
                re.IGNORECASE
            )
            if cov_clause:
                _add_covenant({
                    "name": "Minimum Interest Coverage Ratio",
                    "covenant_type": "maintenance",
                    "formula": "EBITDA / Interest Expense",
                    "threshold": None,
                    "threshold_direction": "min",
                    "frequency": "quarterly",
                    "raw_text": cov_clause.group(0).strip()
                })

        # 4. Minimum Liquidity
        # 4a. Numeric match
        liq_num = re.search(
            r"(?:minimum\s+liquidity|maintain\s+liquidity|liquidity\s+covenant)[^\d$]{1,150}?\$?\s*([0-9,]+(?:\.[0-9]+)?)\s*(million|billion|k\b|thousand)",
            text,
            re.IGNORECASE
        )
        if liq_num and liq_num.group(1):
            raw_num_str = liq_num.group(1).replace(",", "")
            raw_num = float(raw_num_str) if raw_num_str else 0.0
            unit = (liq_num.group(2) or "").lower()
            if unit == "billion":
                raw_num *= 1e9
            elif unit == "million":
                raw_num *= 1e6
            elif unit in ("k", "thousand"):
                raw_num *= 1e3
            _add_covenant({
                "name": "Minimum Liquidity",
                "covenant_type": "maintenance",
                "formula": "Cash and Cash Equivalents + Available Revolver Capacity",
                "threshold": raw_num,
                "threshold_direction": "min",
                "frequency": "quarterly",
                "raw_text": liq_num.group(0).strip()
            })
        else:
            # 4b. Clause without numeric threshold
            liq_clause = re.search(
                r"(?:covenant[s]?[^;\.\n]*?(?:require[s]?|maintain[ing]?|including|subject to)[^;\.\n]*?|maintain[ing]?(?:\s+(?:a|the))?\s+|shall maintain[^;\.\n]*?)(?:a\s+)?(minimum\s+liquidity(?:\s+amount)?|liquidity\s+covenant|minimum\s+consolidated\s+liquidity)",
                text,
                re.IGNORECASE
            )
            if liq_clause:
                _add_covenant({
                    "name": "Minimum Liquidity",
                    "covenant_type": "maintenance",
                    "formula": "Cash and Cash Equivalents + Available Facility Commitments",
                    "threshold": None,
                    "threshold_direction": "min",
                    "frequency": "quarterly",
                    "raw_text": liq_clause.group(0).strip()
                })

        # 5. Financial Reporting Requirements
        rep_clause = re.search(
            r"(?:covenant[s]?[^;\.\n]*?(?:require[s]?|including|subject to|deliver|furnish)[^;\.\n]*?|affirmative\s+covenants?[^;\.\n]*?)(financial\s+reporting(?:\s+requirements)?|delivery\s+of\s+financial\s+statements|furnish\s+annual\s+and\s+quarterly\s+financial\s+statements)",
            text,
            re.IGNORECASE
        )
        if rep_clause:
            _add_covenant({
                "name": "Financial Reporting Requirements",
                "covenant_type": "reporting",
                "formula": "Delivery of periodic financial statements and compliance certificates",
                "threshold": None,
                "threshold_direction": None,
                "frequency": "quarterly",
                "raw_text": rep_clause.group(0).strip()
            })

        # 6. Debt to Capitalization covenant pattern
        cap_match = re.search(
            r"(?:debt\s+to\s+(?:total\s+)?capitalization(?:\s+ratio)?|capitalization\s+ratio)[^\d]{1,150}?(\d+(?:\.\d+)?)\s*(?::\s*1(?:\.0+)?|\s*to\s*1(?:\.0+)?|%|\s*percent)",
            text,
            re.IGNORECASE
        )
        if cap_match:
            thresh = float(cap_match.group(1))
            _add_covenant({
                "name": "Debt to Capitalization Ratio",
                "covenant_type": "maintenance",
                "formula": "Total Debt / Total Capitalization",
                "threshold": thresh,
                "threshold_direction": "max",
                "frequency": "quarterly",
                "raw_text": cap_match.group(0).strip()
            })
        else:
            cap_clause = re.search(
                r"(?:covenant[s]?[^;\.\n]*?(?:require[s]?|maintain[ing]?|including|subject to)[^;\.\n]*?|maintain[ing]?(?:\s+(?:a|the))?\s+)(?:a\s+)?(maximum\s+debt\s+to\s+capitalization\s+ratio|debt\s+to\s+capitalization\s+ratio)",
                text,
                re.IGNORECASE
            )
            if cap_clause:
                _add_covenant({
                    "name": "Debt to Capitalization Ratio",
                    "covenant_type": "maintenance",
                    "formula": "Total Debt / Total Capitalization",
                    "threshold": None,
                    "threshold_direction": "max",
                    "frequency": "quarterly",
                    "raw_text": cap_clause.group(0).strip()
                })

        # 7. Tangible Net Worth covenant pattern
        tnw_match = re.search(
            r"(?:tangible\s+net\s+worth|minimum\s+net\s+worth|consolidated\s+net\s+worth)[^\d$]{1,150}?\$?\s*([0-9,]+(?:\.[0-9]+)?)\s*(million|billion|k\b|thousand)",
            text,
            re.IGNORECASE
        )
        if tnw_match and tnw_match.group(1):
            raw_num_str = tnw_match.group(1).replace(",", "")
            raw_num = float(raw_num_str) if raw_num_str else 0.0
            unit = (tnw_match.group(2) or "").lower()
            if unit == "billion":
                raw_num *= 1e9
            elif unit == "million":
                raw_num *= 1e6
            elif unit in ("k", "thousand"):
                raw_num *= 1e3
            _add_covenant({
                "name": "Tangible Net Worth",
                "covenant_type": "maintenance",
                "formula": "Total Assets - Intangibles - Total Liabilities",
                "threshold": raw_num,
                "threshold_direction": "min",
                "frequency": "quarterly",
                "raw_text": tnw_match.group(0).strip()
            })
        else:
            tnw_clause = re.search(
                r"(?:covenant[s]?[^;\.\n]*?(?:require[s]?|maintain[ing]?|including|subject to)[^;\.\n]*?|maintain[ing]?(?:\s+(?:a|the))?\s+)(?:a\s+)?(minimum\s+tangible\s+net\s+worth|tangible\s+net\s+worth\s+covenant)",
                text,
                re.IGNORECASE
            )
            if tnw_clause:
                _add_covenant({
                    "name": "Tangible Net Worth",
                    "covenant_type": "maintenance",
                    "formula": "Total Assets - Intangibles - Total Liabilities",
                    "threshold": None,
                    "threshold_direction": "min",
                    "frequency": "quarterly",
                    "raw_text": tnw_clause.group(0).strip()
                })

        return found

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(clean)
        except Exception:
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
