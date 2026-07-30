"""
Compliance Agent Prompts.
"""
from ai.prompts.base_prompt import BasePrompt

COMPLIANCE_SYSTEM_PROMPT = """
You are the Compliance Agent for Covenexa. Your task is to evaluate calculations results,
flag breaches, and check headroom thresholds. Use deterministic inputs only.
"""

class CompliancePrompt(BasePrompt):
    def __init__(self) -> None:
        super().__init__(
            "Evaluate compliance given covenant thresholds: {covenants} and calculated ratios: {ratios}"
        )
