# test_models.py
import json
from copy import deepcopy
from pathlib import Path
from unittest import TestCase

import pytest

from pydantic import ValidationError

from app.common.model.downstream.creative_group import (
    CreativeDesignDocument,
    load_document,
    validate_document_json_str,
    CreativeField,
    FileSizeRule,
    VerticalSpacingRule,
    HorizontalSpacingRule,
    ExportImageSeparateFileRule,
    FileTypeRule,
    OptionalFieldRule,
    MaintainedSpacingParams,
    CreativeAdGroupRequest, CreativeAdGroupCreateResponse,
)

class TestCreativeGroup(TestCase):

    SAMPLE_JSON = r"""
    {
      "version": 1,
      "contentVersion": 1,
      "designGroupId": "d96c2daa-5778-45a5-9c4a-585715d728c6",
      "templateGroupId": "CAROUSEL_VIDEO",
      "templateGroupDisplayName": "Carousel Video (Test)",
      "creativeDesigns": [
        {
          "id": "b1f0d8ff-6809-4fd1-83b1-2de6452e431f",
          "templateId": "efe1ac36-9e49-471d-be75-566f04074903",
          "foreignTemplateId": "56",
          "templateType": "VIDEO",
          "templateVersion": 4,
          "name": "Carousel Video",
          "width": 1920.0,
          "height": 1080.0,
          "fields": [
            {
              "fieldElementName": "8bc4c392-5bb7-4954-a0b6-20b6b1949ea2",
              "fieldDataType": "ZONE",
              "zoneType": "VIDEO",
              "displayName": "Video",
              "height": 1080.0,
              "left": 0.0,
              "top": 0.0,
              "width": 1920.0,
              "rules": {
                "fileSize": {
                  "ruleType": "fileSize",
                  "fileSize": 500,
                  "fileSizeUnit": "MB"
                },
                "verticalSpacing": {
                  "ruleType": "verticalSpacing",
                  "maintainedSpacingParams": {
                    "distanceInPixels": 0,
                    "distanceFrom": "BELOW",
                    "referencedElementType": "CANVAS",
                    "relativeToType": "CONTENT"
                  }
                },
                "horizontalSpacing": {
                  "ruleType": "horizontalSpacing",
                  "maintainedSpacingParams": {
                    "distanceInPixels": 0,
                    "distanceFrom": "RIGHT_OF",
                    "referencedElementType": "CANVAS",
                    "relativeToType": "CONTENT"
                  }
                }
              },
              "libraryValidations": {},
              "sourceSystem": "DESIGN_HUDDLE"
            },
            {
              "fieldElementName": "220f9727-c7bd-4a94-9b7f-efeccc312c65",
              "fieldDataType": "ZONE",
              "zoneType": "IMAGE",
              "displayName": "Thumbnail Image",
              "height": 1080.0,
              "left": 0.0,
              "top": 0.0,
              "width": 1920.0,
              "rules": {
                "exportImageSeparateFile": {
                  "ruleType": "exportImageSeparateFile",
                  "exportImage": true
                },
                "verticalSpacing": {
                  "ruleType": "verticalSpacing",
                  "maintainedSpacingParams": {
                    "distanceInPixels": 0,
                    "distanceFrom": "BELOW",
                    "referencedElementType": "CANVAS",
                    "relativeToType": "CONTENT"
                  }
                },
                "horizontalSpacing": {
                  "ruleType": "horizontalSpacing",
                  "maintainedSpacingParams": {
                    "distanceInPixels": 0,
                    "distanceFrom": "RIGHT_OF",
                    "referencedElementType": "CANVAS",
                    "relativeToType": "CONTENT"
                  }
                },
                "fileType": {
                  "ruleType": "fileType",
                  "supportedFileTypes": ["JPG","PNG","TIF"]
                }
              },
              "libraryValidations": {},
              "sourceSystem": "DESIGN_HUDDLE"
            },
            {
              "fieldElementName": "3bbc3fd2-fbc1-484d-b593-b89a3e3d3277",
              "fieldDataType": "ZONE",
              "zoneType": "IMAGE",
              "displayName": "Video Captions",
              "height": 540.0,
              "left": 480.0,
              "top": 270.0,
              "width": 960.0,
              "rules": {
                "optionalField": {
                  "ruleType": "optionalField"
                },
                "fileType": {
                  "ruleType": "fileType",
                  "supportedFileTypes": ["VTT","SRT"]
                }
              },
              "libraryValidations": {},
              "sourceSystem": "KAP"
            },
            {
              "fieldElementName": "133010b0-890c-42bd-a5c0-c377b528acee",
              "fieldDataType": "ZONE",
              "zoneType": "IMAGE",
              "displayName": "Video Description Track",
              "height": 540.0,
              "left": 480.0,
              "top": 270.0,
              "width": 960.0,
              "rules": {
                "fileType": {
                  "ruleType": "fileType",
                  "supportedFileTypes": ["MP3","AAC","M4A","WAV"]
                }
              },
              "libraryValidations": {},
              "sourceSystem": "KAP"
            }
          ],
          "additionalSizes": [],
          "thumbnailAsset": {
            "id": "68ef924fd8fae071f3a06a96",
            "fileName": "efe1ac36-9e49-471d-be75-566f04074903_v3_thumbnail.jpg",
            "blobFileName": "c030b425-03e1-4cae-9f82-b324374b8703.jpg",
            "fileType": "image/jpeg",
            "imageDimensions": { "width": 320.0, "height": 180.0 },
            "publicUrl": "https://sa8451mapcmctst.blob.core.windows.net/creative-assets-container/c030b425-03e1-4cae-9f82-b324374b8703.jpg?sv=2025-01-05&amp;se=2025-11-15T09%3A35%3A45Z&amp;sr=b&amp;sp=r&amp;sig=gNiBWs7skPQDmmQt6T28zgo86ZmfUqyseFsnybbclNU%3D",
            "md5Checksum": null
          },
          "hasAltText": false,
          "hasRenderWarningMessage": false,
          "outputFileType": "JPG",
          "maxOutputFileSizeUnits": "KB",
          "thumbnailSource": { "source": "DESIGN_HUDDLE", "field": null }
        }
      ],
      "fields": [],
      "bulkUploadFields": [],
      "status": "DRAFT",
      "warningMessages": [],
      "requiresGeneratedAssets": false,
      "primaryThumbnailDesignId": "b1f0d8ff-6809-4fd1-83b1-2de6452e431f"
    }
    """
    with open(f"{Path(__file__).parent.parent.parent}/utils/json_files/creative_group_request.json", 'r') as f:
        SAMPLE_JSON_CREATION_REQUEST = json.loads(f.read())

    with open(f"{Path(__file__).parent.parent.parent}/utils/json_files/creative_group_creation_response.json", 'r') as f:
        SAMPLE_JSON_CREATION_RESPONSE = json.loads(f.read())

    def test_parse_full_payload_success(self):
        doc = CreativeDesignDocument.model_validate(json.loads(self.SAMPLE_JSON))

        assert doc.version == 1
        assert doc.contentVersion == 1
        assert isinstance(doc.designGroupId, str)
        assert doc.templateGroupId == "CAROUSEL_VIDEO"
        assert doc.templateGroupDisplayName == "Carousel Video (Test)"
        assert len(doc.creativeDesigns) == 1

        design = doc.creativeDesigns[0]
        assert design.name == "Carousel Video"
        assert design.width == 1920.0
        assert design.height == 1080.0
        assert design.maxOutputFileSizeUnits == "KB"
        assert design.outputFileType == "JPG"
        assert design.thumbnailSource.source == "DESIGN_HUDDLE"
        assert design.thumbnailSource.field is None

        # fields parsed
        assert len(design.fields) == 4

        video_field = design.fields[0]
        assert video_field.zoneType == "VIDEO"
        assert "fileSize" in video_field.rules
        # discriminated union typing
        assert video_field.rules["fileSize"].ruleType == "fileSize"


    def test_rules_discriminated_union_coverage(self):
        # Build each rule type directly to exercise branches
        fs = FileSizeRule(fileSize=123, fileSizeUnit="MB")
        vs = VerticalSpacingRule(
            maintainedSpacingParams=MaintainedSpacingParams(
                distanceInPixels=0,
                distanceFrom="BELOW",
                referencedElementType="CANVAS",
                relativeToType="CONTENT",
            )
        )
        hs = HorizontalSpacingRule(
            maintainedSpacingParams=MaintainedSpacingParams(
                distanceInPixels=5,
                distanceFrom="RIGHT_OF",
                referencedElementType="CANVAS",
                relativeToType="CONTENT",
            )
        )
        ex = ExportImageSeparateFileRule(exportImage=True)
        ft = FileTypeRule(supportedFileTypes=["PNG", "JPG"])
        op = OptionalFieldRule()

        # assert types and content
        assert fs.fileSizeUnit == "MB"
        assert vs.maintainedSpacingParams.distanceFrom == "BELOW"
        assert hs.maintainedSpacingParams.distanceFrom == "RIGHT_OF"
        assert ex.exportImage is True
        assert ft.supportedFileTypes == ["PNG", "JPG"]
        assert op.ruleType == "optionalField"


    def test_field_validation_width_positive(self):
        # width must be positive -> zero invalid
        with pytest.raises(ValidationError):
            CreativeField.model_validate({
                "fieldElementName": "8bc4c392-5bb7-4954-a0b6-20b6b1949ea2",
                "fieldDataType": "ZONE",
                "zoneType": "IMAGE",
                "displayName": "Invalid",
                "height": 10.0,
                "left": 0.0,
                "top": 0.0,
                "width": 0.0,
                "rules": {},
                "libraryValidations": {},
                "sourceSystem": "TEST"
            })


    def test_roundtrip_json_and_helpers(self):
        # validate via helper from JSON string, then dump and re-validate
        doc1 = validate_document_json_str(self.SAMPLE_JSON)
        dumped = doc1.model_dump()
        doc2 = load_document(dumped)
        assert doc1.model_dump() == doc2.model_dump()


    def test_field_parse_full_request_payload(self):
        request = deepcopy(self.SAMPLE_JSON_CREATION_REQUEST)
        creative_ad_group_request = CreativeAdGroupRequest.model_validate(request)
        assert creative_ad_group_request.model_dump(exclude_none=True) == self.SAMPLE_JSON_CREATION_REQUEST


    def test_field_parse_full_request_missing_apiClientInfo(self):
        request = deepcopy(self.SAMPLE_JSON_CREATION_REQUEST)
        request["apiClientInfo"] = None
        with self.assertRaises(ValidationError):
            CreativeAdGroupRequest.model_validate(request)


    def test_field_parse_full_response_payload(self):
        response = deepcopy(self.SAMPLE_JSON_CREATION_RESPONSE)
        creative_ad_group_response = CreativeAdGroupCreateResponse.model_validate(response)
        assert creative_ad_group_response.model_dump(exclude_none=True) == response


    def test_field_parse_full_response_missing_fields(self):
        response = deepcopy(self.SAMPLE_JSON_CREATION_RESPONSE)
        response["version"] = None
        with self.assertRaises(ValidationError):
            CreativeAdGroupCreateResponse.model_validate(response)
