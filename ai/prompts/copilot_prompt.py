"""
Copilot Agent Prompts.
"""
from ai.prompts.base_prompt import BasePrompt

COPILOT_SYSTEM_PROMPT = """
You are the Covenexa Copilot. Help credit analysts answer questions about loan covenants,
definitions, and borrower performance using retrieved context only.
Never make up information. If context is missing, say so.
"""

class CopilotPrompt(BasePrompt):
    def __init__(self) -> None:
        super().__init__(
            "Retrieved Context:\n{retrieved_context}\n\nQuestion: {user_query}\n\nAnswer with sources and citations."
        )
