import json
from typing import List

from fastapi import Depends
from pydantic import ValidationError

from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.model.downstream.location_groups import LocationGroupResponseData, LocationGroupResponse, LocationGroup
from app.common.model.division import DivisionServiceResponse
from app.common.utils import filtered_logger
from app.common.utils.async_adapter import AsyncAdapter

logger = filtered_logger.get_logger(__name__)

class DivisionGateway:
    __external_api_http_client: AsyncAdapter

    def __init__(
            self,
            async_external_api_http_client_service: AsyncExternalApiHttpClientService = Depends(AsyncExternalApiHttpClientService),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__external_api_http_client = AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_DIVISION,
            harness_service=harness_service
        )

    async def get_divisions(self) -> List[DivisionServiceResponse]:
        path = '/map-location-manager/options'
        logger.info('Request to %s', path)

        response = await self.__external_api_http_client.post(
            path=path,
            json={'select': {'type': 'all'}},
            response_body_type="json",
            forward_client_error_response_content=True
        )
        response_json = response.json()
        return [DivisionServiceResponse(**r) for r in response_json]

    async def __get_location_groups(self, division_banners) -> LocationGroupResponseData:
        """
            Calls location groups with a list of division banner ids
            This function is only used internally since it needs to be batched
            The downstream service only supports a max of 50 ids
        """
        query_params = {"ids": ",".join(division_banners)}
        path = "/location-groups/v1/"
        response = await self.__external_api_http_client.get(
            path=path,
            params=query_params,
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )
        response_json = response.json()
        return LocationGroupResponse(**response_json).data

    async def create_location_group(self, payload: dict) -> LocationGroup:
        path = '/location-groups/v1/'
        response = await self.__external_api_http_client.post(
            path=path, json=payload, forward_client_error_response_content=True)
        return LocationGroup(**response.json())

    async def get_location_groups(self, division_banners: List[str]) -> LocationGroupResponseData:
        """
            Gets all location groups for the given list of division banner ids
            This function helps us batch calls to the downstream service and aggregate the responses.
        """
        response = LocationGroupResponseData()
        if not division_banners:
            return response

        filtered_banners = [i for i in division_banners if i]
        if not filtered_banners:
            return response

        # Create batches of 50 ids
        # map-location-group can only support up to 50 ids at a time
        batches = [filtered_banners[i:i + 50] for i in range(0, len(filtered_banners), 50)]

        for batch in batches:
            try:
                location_groups_response = await self.__get_location_groups(batch)
                response.found.extend(location_groups_response.found)
                response.notFound.extend(location_groups_response.notFound)
            except json.JSONDecodeError as ex:
                logger.error("JSONDecodeError - Unable to decode JSON for batch %s: %s", batch, ex.doc)
                continue
            except ValidationError as ex:
                logger.error(
                    "Response Validation Error for batch %s: %s",
                    batch, str(ex)
                )
                continue

        return response
