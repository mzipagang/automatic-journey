# test_models_minimal.py
import json
from unittest import TestCase

import pytest
from uuid import UUID
from pydantic import ValidationError

from app.common.model.downstream.creative_group_status import (
    MinimalCreativeDesignDocument,
    load_minimal_document,
    validate_minimal_document_json_str,
)

class TestCreativeGroupStatus(TestCase):

    SAMPLE_JSON = r"""
    {
      "clonedFromDesignGroupId": "d96c2daa-5778-45a5-9c4a-585715d728c6",
      "creativeDesigns": [],
      "fields": [],
      "bulkUploadFields": [],
      "status": "DRAFT"
    }
    """


    def test_parse_minimal_success(self):
        doc = MinimalCreativeDesignDocument.model_validate(json.loads(self.SAMPLE_JSON))
        assert isinstance(doc.clonedFromDesignGroupId, UUID)
        assert doc.status == "DRAFT"
        assert doc.creativeDesigns == []
        assert doc.fields == []
        assert doc.bulkUploadFields == []


    def test_helper_functions_and_roundtrip(self):
        doc1 = validate_minimal_document_json_str(self.SAMPLE_JSON)
        dumped = doc1.model_dump()
        doc2 = load_minimal_document(dumped)
        assert doc1.model_dump() == doc2.model_dump()


    def test_invalid_uuid_rejected(self):
        data = json.loads(self.SAMPLE_JSON)
        data["clonedFromDesignGroupId"] = "not-a-uuid"
        with pytest.raises(ValidationError):
            MinimalCreativeDesignDocument.model_validate(data)


    def test_forbid_extra_keys(self):
        data = json.loads(self.SAMPLE_JSON)
        data["unexpected"] = True
        with pytest.raises(ValidationError):
            MinimalCreativeDesignDocument.model_validate(data)


    def test_missing_required_field(self):
        data = json.loads(self.SAMPLE_JSON)
        del data["status"]
        with pytest.raises(ValidationError):
            MinimalCreativeDesignDocument.model_validate(data)
