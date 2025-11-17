from fastapi import Depends, HTTPException

from app.common.model.downstream.bid_modifiers import (
    BidModifierGroupRequest,
    BidModifierGroupResponse,
    KeywordBidModifiersResponse,
    KeywordsRequest,
    KeywordsResponse,
)
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger
from app.common.utils.async_adapter import AsyncAdapter

logger = filtered_logger.get_logger(__name__)


class KeywordBiddingGateway:
    """KeywordBiddingGateway is a class that provides methods to interact with the keyword bidding API.

    Raises:
        HTTPException
            If the API response indicates a server error or if the request fails.
    """
    __external_api_http_client: AsyncAdapter
    ENDPOINT = "/media/bid-modifiers/v1"

    def __init__(
            self,
            async_external_api_http_client_service: AsyncExternalApiHttpClientService = Depends(AsyncExternalApiHttpClientService),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__external_api_http_client = AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_KEYWORD_BIDDING,
            harness_service=harness_service
        )

    async def create_keyword_bid_modifier_group(
        self, create_bid_modifier_group_payload: BidModifierGroupRequest
    ) -> BidModifierGroupResponse:
        """Method that creates a keyword bid modifier group.

        Args:
            create_bid_modifier_group_payload (BidModifierGroupRequest): _payload to create a keyword bid modifier group.

        Raises:
            HTTPException: If the API response indicates a server error or if the request fails.

        Returns:
            BidModifierGroupResponse: Response from the API containing the created keyword bid modifier group.
        """
        path = f"{self.ENDPOINT}/keyword_bid_modifiers"
        response = await self.__external_api_http_client.post(
            path=path, json=create_bid_modifier_group_payload.model_dump()
        )

        if response.is_server_error:
            logger.error(
                "Upstream bid-modifiers service failed with status %s", response.status_code
            )
            raise HTTPException(status_code=500, detail="Backend service unavailable")

        if response.is_success:
            return BidModifierGroupResponse(**response.json())

        raise HTTPException(status_code=400, detail="Failed to create keyword bid modifier group")

    async def get_eligible_keywords(self, keywords_payload: KeywordsRequest) -> KeywordsResponse:
        """Method that retrieves eligible keywords for a given payload.

        Args:
            keywords_payload (KeywordsRequest): _payload containing the keywords to be checked.

        Raises:
            HTTPException: If the API response indicates a server error or if the request fails.

        Returns:
            KeywordsResponse: Response from the API containing the eligible keywords.
        """
        path = f"{self.ENDPOINT}/keywords"
        response = await self.__external_api_http_client.post(
            path=path,
            json=keywords_payload.model_dump(exclude_none=True),
            response_body_type="json",
            forward_client_error_response_content=True,
        )

        if response.is_server_error:
            logger.error(
                "Upstream bid-modifiers service failed with status %s", response.status_code
            )
            raise HTTPException(status_code=500, detail="Backend service unavailable")

        if response.is_success:
            return KeywordsResponse(**response.json())

        raise HTTPException(status_code=400, detail="Failed to get eligible keywords")

    async def get_keyword_bid_modifier_group(self, keyword_bid_modifier_group_id: str) -> KeywordBidModifiersResponse:
        """Method that retrieves a keyword bid modifier group by its ID.

        Args:
            keyword_bid_modifier_group_id (str): _ID of the keyword bid modifier group to be retrieved.

        Raises:
            HTTPException: If the API response indicates a server error or if the request fails.

        Returns:
            KeywordBidModifiersResponse: Response from the API containing the keyword bid modifier group.
        """
        path = f"/media/bid-modifiers/v1/keyword_bid_modifiers/{keyword_bid_modifier_group_id}"
        response = await self.__external_api_http_client.get(
            path=path,
            response_body_type="json",
            forward_client_error_response_content=True
        )

        if response.is_server_error:
            logger.error(
                "Upstream bid-modifiers service failed with status %s", response.status_code
            )
            raise HTTPException(status_code=500, detail="Backend service unavailable")

        if response.is_success:
            return KeywordBidModifiersResponse(**response.json())
        raise HTTPException(status_code=400, detail="Failed to get keyword bid modifier group")
