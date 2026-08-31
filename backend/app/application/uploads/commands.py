"""
Document Upload application commands.
"""
from dataclasses import dataclass
from typing import BinaryIO


@dataclass
class UploadDocumentCommand:
    loan_id: str
    file_name: str
    file_type: str  # e.g., 'loan_agreement', 'amendment'
    content: BinaryIO
    size_bytes: int
