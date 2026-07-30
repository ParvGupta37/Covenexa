"""
Covenexa prompt templates library.
Provides standardized formatting and decouples prompt writing from agent workflows.
"""
from ai.prompts.base_prompt import BasePrompt
from ai.prompts.planner_prompt import PLANNER_SYSTEM_PROMPT, PlannerPrompt
from ai.prompts.document_prompt import DOCUMENT_SYSTEM_PROMPT, DocumentPrompt
from ai.prompts.covenant_prompt import COVENANT_SYSTEM_PROMPT, CovenantPrompt
from ai.prompts.financial_prompt import FINANCIAL_SYSTEM_PROMPT, FinancialPrompt
from ai.prompts.compliance_prompt import COMPLIANCE_SYSTEM_PROMPT, CompliancePrompt
from ai.prompts.recommendation_prompt import RECOMMENDATION_SYSTEM_PROMPT, RecommendationPrompt
from ai.prompts.report_prompt import REPORT_SYSTEM_PROMPT, ReportPrompt
from ai.prompts.copilot_prompt import COPILOT_SYSTEM_PROMPT, CopilotPrompt

__all__ = [
    "BasePrompt",
    "PLANNER_SYSTEM_PROMPT",
    "PlannerPrompt",
    "DOCUMENT_SYSTEM_PROMPT",
    "DocumentPrompt",
    "COVENANT_SYSTEM_PROMPT",
    "CovenantPrompt",
    "FINANCIAL_SYSTEM_PROMPT",
    "FinancialPrompt",
    "COMPLIANCE_SYSTEM_PROMPT",
    "CompliancePrompt",
    "RECOMMENDATION_SYSTEM_PROMPT",
    "RecommendationPrompt",
    "REPORT_SYSTEM_PROMPT",
    "ReportPrompt",
    "COPILOT_SYSTEM_PROMPT",
    "CopilotPrompt",
]
