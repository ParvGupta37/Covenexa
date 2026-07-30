"""
Document Events.
Events related to uploading and parsing agreement/amendment files.
"""
from dataclasses import dataclass
from event_bus.events.base_event import BaseEvent


@dataclass(kw_only=True)
class DocumentUploadedEvent(BaseEvent):
    """
    Fired when a document is successfully saved to disk.
    Triggers parsing or OCR pipelines.
    """
    borrower_id: str
    agreement_id: str
    file_path: str
    file_type: str  # e.g., 'loan_agreement', 'amendment', 'financial_statement'

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "borrower_id": self.borrower_id,
            "agreement_id": self.agreement_id,
            "file_path": self.file_path,
            "file_type": self.file_type,
        })
        return data


@dataclass(kw_only=True)
class DocumentProcessedEvent(BaseEvent):
    """
    Fired when OCR/parsing completes, indexing is done,
    and metadata has been updated in databases.
    """
    borrower_id: str
    agreement_id: str
    status: str  # e.g., 'success', 'failed'
    error_message: str | None = None

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "borrower_id": self.borrower_id,
            "agreement_id": self.agreement_id,
            "status": self.status,
            "error_message": self.error_message,
        })
        return data
