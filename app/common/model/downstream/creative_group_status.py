# models_minimal.py
from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MinimalCreativeDesignDocument(BaseModel):
    """
    Minimal document that matches:
    {
        "clonedFromDesignGroupId": "<uuid>",
        "creativeDesigns": [],
        "fields": [],
        "bulkUploadFields": [],
        "status": "DRAFT"
    }
    """
    model_config = ConfigDict(extra="forbid")

    clonedFromDesignGroupId: UUID
    creativeDesigns: List[Any] = []
    fields: List[Any] = []
    bulkUploadFields: List[Any] = []
    status: str  # e.g., "DRAFT"


# ---------- Convenience API (mirrors previous file style) ----------

def load_minimal_document(data: Dict[str, Any]) -> MinimalCreativeDesignDocument:
    """
    Parse and validate a dict into a MinimalCreativeDesignDocument.
    Raises pydantic.ValidationError on invalid payload.
    """
    return MinimalCreativeDesignDocument.model_validate(data)


def validate_minimal_document_json_str(json_str: str) -> MinimalCreativeDesignDocument:
    """
    Parse and validate a JSON string into a MinimalCreativeDesignDocument.
    """
    import json
    parsed = json.loads(json_str)
    return load_minimal_document(parsed)
