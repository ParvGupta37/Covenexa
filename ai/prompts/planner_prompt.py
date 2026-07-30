"""
Planner Agent Prompts.
"""
from ai.prompts.base_prompt import BasePrompt

PLANNER_SYSTEM_PROMPT = """
You are the Planner Agent for Covenexa. Your job is to orchestrate all other agents 
(Document, Covenant, Financial, Compliance, Portfolio, Recommendation, Reporting, Copilot)
to address a borrower review request. 

Determine what downstream agents are required and outline an execution sequence.
"""

class PlannerPrompt(BasePrompt):
    def __init__(self) -> None:
        super().__init__(
            "User Request: {user_query}\nAvailable Context: {retrieved_context}\nDetermine the next action step."
        )
