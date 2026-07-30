"""
Recommendation Agent Prompts.
"""
from ai.prompts.base_prompt import BasePrompt

RECOMMENDATION_SYSTEM_PROMPT = """
You are the Recommendation Agent for Covenexa. Based on covenant headroom breaches or health risk level changes,
draft actionable recommendations for the credit analysis team.
"""

class RecommendationPrompt(BasePrompt):
    def __init__(self) -> None:
        super().__init__(
            "Suggest credit actions based on borrower: {borrower_name} containing risks: {detected_risks}"
        )
