"""
Document Upload API schemas.
"""
from datetime import datetime
from pydantic import BaseModel


class UploadResponseSchema(BaseModel):
    agreement_id: str
    loan_id: str
    file_name: str
    file_path: str
    file_type: str
    upload_date: datetime
    status: str = "uploaded"
