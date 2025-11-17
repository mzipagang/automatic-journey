from enum import StrEnum
from typing import TypeVar, Type, Any

from app.common.model.shared import IgnoreCaseStrEnum
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

FallbackEnum = TypeVar('FallbackEnum', bound=StrEnum)
def ignore_case_with_unsupported_fallback(
        cls: Type[FallbackEnum],
        value,
) -> FallbackEnum:
    # Make sure the given class is a StrEnum and has an UNSUPPORTED key
    if not issubclass(cls, StrEnum):
        raise TypeError(f"{cls.__name__} must be a subclass of StrEnum")

    keys = cls.__members__.keys()
    if "UNSUPPORTED" not in keys:
        raise TypeError(f"{cls.__name__} must have UNSUPPORTED key")

    # Get the first matching value, or return None
    target_value = next((
        member
        for member in cls.__members__.values()
        if member.value.lower() == str(value).lower()
    ), None)

    # Return the matching value, or return UNSUPPORTED
    return target_value or cls.UNSUPPORTED


class CampaignType(IgnoreCaseStrEnum):
    """
    External user facing campaign types
    """
    PLA = "PLA" # Product Listing Ad
    TOA = "TOA" # Targeted Onsite Ad
    CAROUSEL = "CAROUSEL" # Promoted Products Carousel


class InternalCampaignType(StrEnum):
    """
    Internal unified campaign type to use across project
    """
    PLA = "PLA"  # Product Listing Ad
    TOA = "TOA"  # Targeted Onsite Ad
    CAROUSEL = "CAROUSEL"  # Promoted Products Carousel
    UNSUPPORTED = "UNSUPPORTED"

    @classmethod
    def _missing_(cls, value):
        return ignore_case_with_unsupported_fallback(cls, value)


class BidManagerCampaignType(StrEnum):
    """
    Upstream campaign type for Bid Manager
    """
    PLA = "PLA"  # Product Listing Ad
    TOA = "TOA"  # Targeted Onsite Ad
    CAROUSEL = "PPC"  # Promoted Products Carousel
    UNSUPPORTED = "UNSUPPORTED"

    @classmethod
    def _missing_(cls, value):
        return ignore_case_with_unsupported_fallback(cls, value)


class CASCampaignType(StrEnum):
    """
    Upstream campaign type for campaign and activation service
    """
    PLA = "PLA" # Product Listing Ad
    TOA = "TOA" # Targeted Onsite Ad
    CAROUSEL = "Promoted_Products_Carousel" # Promoted Products Carousel
    UNSUPPORTED = "UNSUPPORTED"

    @classmethod
    def _missing_(cls, value):
        return ignore_case_with_unsupported_fallback(cls, value)


class KoddiReportExperienceType(IgnoreCaseStrEnum):
    """
    Upstream experience type for koddi reports
    This enum is only for outgoing values
    """
    PLA = "PLA"  # Product Listing Ad
    TOA = "TOA"  # Targeted Onsite Ad
    CAROUSEL = "Carousel"  # Promoted Products Carousel


GivenEnum = TypeVar("GivenEnum", bound=StrEnum)
TargetEnum = TypeVar("TargetEnum", bound=StrEnum)
def convert_enum(
        enum_value_a: GivenEnum,
        enum_class_b: Type[TargetEnum]
) -> TargetEnum | None:
    """
    Used to convert between enums assuming the enums have the same keys.
    If a mapping is not found, return None
    """
    enum_key_a = enum_value_a.name
    has_mapping = hasattr(enum_class_b, enum_key_a)
    if has_mapping:
        enum_value_b = getattr(enum_class_b, enum_key_a)
        return enum_value_b

    return None

def parse_campaign_type(value: Any, target_type: Type[TargetEnum]) -> InternalCampaignType | None:
    converted_type = InternalCampaignType.UNSUPPORTED
    if value is None:
        converted_type = None
    elif isinstance(value, StrEnum):
        converted_type = convert_enum(value, InternalCampaignType)
    elif isinstance(value, str):
        upstream_campaign_type = target_type(value)
        converted_type = convert_enum(upstream_campaign_type, InternalCampaignType)

    if converted_type == InternalCampaignType.UNSUPPORTED:
        target_name = target_type.__name__
        logger.warning(
            f"Unsupported campaign type {value} is not a supported {target_name}.",
            extra = {
                "campaign_type": value,
                "target_type": target_name,
            }
        )

    return converted_type

def serialize_campaign_type(
        value: InternalCampaignType | None,
        target_type: Type[TargetEnum]
) -> TargetEnum | None:
    if value is None:
        return None
    return convert_enum(value, target_type)