"""
Document Agent Prompts.
"""
from ai.prompts.base_prompt import BasePrompt

DOCUMENT_SYSTEM_PROMPT = """
You are the Document Agent for Covenexa. Your task is to process incoming legal text 
extracted from PDFs, split it into chunks, identify document structure (agreements/amendments), 
and prepare text for indexing.
"""

class DocumentPrompt(BasePrompt):
    def __init__(self) -> None:
        super().__init__(
            "Parse document metadata and classify sections from raw text: {raw_text}"
        )
