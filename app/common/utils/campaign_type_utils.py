from app.common.model.shared import BidManagerCampaignType, CampaignType, InternalCampaignType


def to_bid_manager_campaign_type(original_type: str) -> BidManagerCampaignType:
    """Maps ExternalStatus to InternalStatus"""
    if InternalCampaignType(original_type) in [
        InternalCampaignType.CAROUSEL,
        InternalCampaignType.IN_CAROUSEL,
        InternalCampaignType.CS_CAROUSEL,
        InternalCampaignType.BM_CAROUSEL,
    ]:
        return BidManagerCampaignType.CAROUSEL
    return BidManagerCampaignType(original_type)

def is_carousel_campaign(campaign_type: InternalCampaignType) -> bool:
    return campaign_type in [
        InternalCampaignType.CAROUSEL,
        InternalCampaignType.CS_CAROUSEL,
        InternalCampaignType.BM_CAROUSEL,
        InternalCampaignType.IN_CAROUSEL,
    ]

def is_pla_campaign(campaign_type: CampaignType) -> bool:
    return campaign_type == CampaignType.PLA

def bid_type_matches_campaign_type(bid_group_type: str, campaign_type: str) -> bool:
    return BidManagerCampaignType(bid_group_type) == to_bid_manager_campaign_type(campaign_type)

def to_campaign_service_campaign_type(external_status: CampaignType) -> InternalCampaignType:
    """Maps ExternalStatus to InternalStatus"""
    if external_status == CampaignType.CAROUSEL:
        return InternalCampaignType.CS_CAROUSEL
    return InternalCampaignType(external_status.value)

def to_external_campaign_type(internal_status: str) -> CampaignType:
    """Maps InternalStatus to ExternalStatus"""
    internal_status = InternalCampaignType(internal_status)
    if internal_status in [
        InternalCampaignType.CS_CAROUSEL,
        InternalCampaignType.BM_CAROUSEL,
        InternalCampaignType.IN_CAROUSEL,
    ]:
        return CampaignType.CAROUSEL
    return CampaignType(internal_status.value)
