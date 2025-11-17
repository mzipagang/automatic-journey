from app.common.model.campaign_types import InternalCampaignType
from app.common.model.downstream.bid_manager import ValidateBidRequest, MinCarouselUpcCount
from app.common.model.placement import PlacementType

def get_bid_ranges() -> dict:
    return {
        InternalCampaignType.PLA: {
            PlacementType.SEARCH_AND_BROWSE.value: ValidateBidRequest(
                minimumBidAmount=0.5,
                maximumBidAmount=50,
            ),
            PlacementType.BASKET_BUILDER.value: ValidateBidRequest(
                minimumBidAmount=0.6,
                maximumBidAmount=50,
            ),
            PlacementType.SAVINGS.value: ValidateBidRequest(
                minimumBidAmount=0.3,
                maximumBidAmount=50,
            )
        },
        InternalCampaignType.TOA: {
            PlacementType.SEARCH_AND_BROWSE.value: ValidateBidRequest(
                minimumBidAmount=28,
                maximumBidAmount=100
            ),
            PlacementType.SAVINGS.value: ValidateBidRequest(
                minimumBidAmount=28,
                maximumBidAmount=100
            ),
            PlacementType.SHOP_AND_DISCOVER.value: ValidateBidRequest(
                minimumBidAmount=28,
                maximumBidAmount=100
            ),
            PlacementType.IN_STORE.value: ValidateBidRequest(
                minimumBidAmount=28,
                maximumBidAmount=100
            )
        },
        InternalCampaignType.CAROUSEL: {
            PlacementType.SEARCH_AND_BROWSE_PPC.value: ValidateBidRequest(
                minimumBidAmount=0.9,
                maximumBidAmount=50,
                minimumBidCount=MinCarouselUpcCount.THREE_UPC,
                maximumBidCount=32
            )
        }
    }
