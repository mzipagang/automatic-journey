# models.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Annotated, Literal

from pydantic import BaseModel, Field, ConfigDict, PositiveFloat, NonNegativeFloat, NonNegativeInt

from app.common.model.downstream.campaign_activation_service import ContactReference


# ---------- Rule Models (Discriminated Union) ----------

class FileSizeRule(BaseModel):
    ruleType: Literal["fileSize"] = "fileSize"
    fileSize: NonNegativeInt
    fileSizeUnit: Literal["KB", "MB", "GB"]


class MaintainedSpacingParams(BaseModel):
    distanceInPixels: NonNegativeInt
    # The sample uses BELOW and RIGHT_OF; adding common complements for flexibility.
    distanceFrom: Literal["BELOW", "ABOVE", "LEFT_OF", "RIGHT_OF", "CENTER"]
    referencedElementType: Literal["CANVAS", "CONTENT", "FIELD", "GROUP"]
    relativeToType: Literal["CONTENT", "CANVAS", "FIELD", "GROUP"]


class VerticalSpacingRule(BaseModel):
    ruleType: Literal["verticalSpacing"] = "verticalSpacing"
    maintainedSpacingParams: MaintainedSpacingParams


class HorizontalSpacingRule(BaseModel):
    ruleType: Literal["horizontalSpacing"] = "horizontalSpacing"
    maintainedSpacingParams: MaintainedSpacingParams


class ExportImageSeparateFileRule(BaseModel):
    ruleType: Literal["exportImageSeparateFile"] = "exportImageSeparateFile"
    exportImage: bool


class FileTypeRule(BaseModel):
    ruleType: Literal["fileType"] = "fileType"
    supportedFileTypes: List[str]


class OptionalFieldRule(BaseModel):
    ruleType: Literal["optionalField"] = "optionalField"


class AspectRatio(BaseModel):
    width: PositiveFloat
    height: PositiveFloat


class ImageAspectRatioRule(BaseModel):
    ruleType: Literal["imageAspectRatio"] = "imageAspectRatio"
    requiredAspectRatio: AspectRatio


class ImageDimensionsRule(BaseModel):
    ruleType: Literal["imageDimensions"] = "imageDimensions"
    minImageDimensions: ImageDimensions


class MediaLengthRule(BaseModel):
    ruleType: Literal["mediaLength"] = "mediaLength"
    minLengthInSeconds: NonNegativeInt
    maxLengthInSeconds: NonNegativeInt

Rule = Annotated[
    Union[
        FileSizeRule,
        VerticalSpacingRule,
        HorizontalSpacingRule,
        ExportImageSeparateFileRule,
        FileTypeRule,
        OptionalFieldRule,
        ImageAspectRatioRule,
        ImageDimensionsRule,
        MediaLengthRule,
    ],
    Field(discriminator="ruleType"),
]


# ---------- Field / Asset Models ----------

class ImageDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    unit: Optional[str] = None
    width: PositiveFloat
    height: PositiveFloat


class ThumbnailAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    fileName: str
    blobFileName: str
    fileType: str
    imageDimensions: ImageDimensions
    publicUrl: str
    md5Checksum: Optional[str] = None


class CreativeField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fieldElementName: str
    fieldDataType: Literal["ZONE"]
    zoneType: Literal["VIDEO", "IMAGE"]
    displayName: str

    height: PositiveFloat
    left: NonNegativeFloat
    top: NonNegativeFloat
    width: PositiveFloat

    # The rules object contains multiple named rules. We allow any key,
    # but values must match one of the discriminated Rule subtypes.
    rules: Dict[str, Rule] = Field(default_factory=dict)

    # free-form container (sample shows {})
    libraryValidations: Dict[str, Any] = Field(default_factory=dict)

    sourceSystem: str


class ThumbnailSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    # In sample this is null; it likely references a field ID, so we accept UUID or None
    field: Optional[str] = None


class AltTextCopyGuidelines(BaseModel):
    questionAndExclamationMarkNotRecommended: bool
    shouldNotContainAllCaps: bool
    shouldNotContainAllCapsStrict: bool
    shouldNotEndWithPunctuation: bool


class CreativeDesign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    templateId: str
    foreignTemplateId: str
    templateType: str
    templateVersion: int
    name: str

    width: PositiveFloat
    height: PositiveFloat

    fields: List[CreativeField]
    additionalSizes: List[Any] = Field(default_factory=list)

    thumbnailAsset: ThumbnailAsset

    hasAltText: bool
    hasRenderWarningMessage: bool

    outputFileType: str  # sample uses "JPG"
    maxOutputFileSizeUnits: Literal["KB", "MB", "GB"]  # sample uses "KB"

    thumbnailSource: Optional[ThumbnailSource] = None

    altTextCopyGuidelines: Optional[AltTextCopyGuidelines] = None


# ---------- Root Document ----------

class CreativeDesignDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    contentVersion: int
    designGroupId: str

    templateGroupId: str
    templateGroupDisplayName: str

    creativeDesigns: List[CreativeDesign] = Field(default_factory=list)

    # present at root but empty in sample; keep flexible
    fields: List[Any] = Field(default_factory=list)
    bulkUploadFields: List[Any] = Field(default_factory=list)

    status: str  # sample uses "DRAFT"
    warningMessages: List[str] = Field(default_factory=list)

    requiresGeneratedAssets: bool
    primaryThumbnailDesignId: Optional[str] = None


# ---------- Convenience API ----------

def load_document(data: Dict[str, Any]) -> CreativeDesignDocument:
    """
    Parse and validate a dict into a CreativeDesignDocument.
    Raises pydantic.ValidationError on invalid payload.
    """
    return CreativeDesignDocument.model_validate(data)


def validate_document_json_str(json_str: str) -> CreativeDesignDocument:
    """
    Parse and validate a JSON string into a CreativeDesignDocument.
    """
    import json
    parsed = json.loads(json_str)
    return load_document(parsed)

class AccountInfo(BaseModel):
    accountId: str
    agencyId: str
    brandIds: list[str]

class ApiClientInfo(BaseModel):
    clientEntityParentIdentifier: str
    clientEntityIdentifier: str
    clientEntityStatus: str
    clientEntityParentStatus: str
    clientEntityParentName: str
    clientEntityLinkUrl: Optional[str] = None
    clientEntityParentLinkUrl: str
    clientType: str
    clientEntityName: str
    clientEntityDescription: str
    clientEntityParentDescription: str
    contacts: list[ContactReference]
    dueDate: str
    adEndDate: str
    adStartDate: str
    usesHarrisTeeter: Optional[bool] = None
    clientEntityRequiresApproval: Optional[bool] = None
    backgroundInfo: Optional[dict] = None
    optionalFeatures: Optional[dict] = None
    rulesetData: Optional[dict] = None


class CreativeAdGroupRequest(BaseModel):
    accountInfo: AccountInfo
    apiClientInfo: ApiClientInfo
    designGroupName: str


class CreativeAdGroupCreateResponse(BaseModel):
    version: int
    contentVersion: int
    designGroupId: str
    name: str
    templateGroupId: str
    templateGroupDisplayName: str
    creativeDesigns: list[CreativeDesign]
    fields: list[CreativeField]
    bulkUploadFields: list
    status: str
    accountInfo: AccountInfo
    apiClientInfo: ApiClientInfo
    warningMessages: list
    requiresGeneratedAssets: bool