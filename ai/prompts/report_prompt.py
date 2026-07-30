"""
Reporting Agent Prompts.
"""
from ai.prompts.base_prompt import BasePrompt

REPORT_SYSTEM_PROMPT = """
You are the Reporting Agent for Covenexa. Synthesize structured findings from all agents
into formatted markdown reports for direct lenders.
"""

class ReportPrompt(BasePrompt):
    def __init__(self) -> None:
        super().__init__(
            "Create a credit analysis report using financial summaries: {financial_summaries} and compliance results: {compliance_results}"
        )
