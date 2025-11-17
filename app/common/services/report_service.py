from typing import List, Set, Dict, Tuple

from datetime import datetime

from fastapi import Depends, HTTPException

from app.common.gateways.campaign_service_gateway import CampaignServiceGateway
from app.common.model.campaign_types import InternalCampaignType, convert_enum, \
    KoddiReportExperienceType
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.model.report import UniqueReportIds, ExternalIdByKoddiId, IdGroup
from app.common.services.async_http_client_service import AsyncKoddiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.services.lookup_service import LookupService
from app.common.model.downstream.campaign_service import CampaignSearchRequest
from app.common.translations.report_translation import ReportTranslation
from app.common.utils.async_adapter import AsyncAdapter
from app.common.view_models import KrogerError, ErrorDetail, ErrorDateTime
from app.common.view_models.report import ReportRequestCommon, ReportResultResponse, Dimensions, Filter
from app.common.services.http_client_service import KoddiHttpClientService
from app.common.utils import filtered_logger
from app.v2.view_models.report import(
    CarrouselInvalidDimensionsV2,
    TOAInvalidMetricsV2,
    TOAInvalidDimensionsV2,
    ReportRequestV2,
    MetricsV2,
    DimensionsV2,
    MetricsV1,
    DimensionsV1,
    CarrouselInvalidDimensionsV1,
    ReportRequestV1
)

logger = filtered_logger.get_logger(__name__)

CURRENCY_CODE = 'USD'

MAP_OPERATORS = {
    'EQUALS': '=',
    'NOT_EQUALS': '!=',
    'GREATER_THAN': '>',
    'GREATER_THAN_OR_EQUAL': '>=',
    'LESS_THAN': '<',
    'LESS_THAN_OR_EQUAL': '<=',
    'LIKE_IN': 'LIKE IN',
    'NOT_IN': 'NOT IN',
    'IS_NULL': 'IS NULL',
    'NOT_NULL': 'NOT NULL',
    'NOT_LIKE': 'NOT LIKE',
    'BETWEEN': 'BETWEEN'
    # Add more operators as needed
}

class ReportService:
    __koddi_http_client: AsyncAdapter
    lookup_service: LookupService
    campaign_gateway: CampaignServiceGateway
    translation: ReportTranslation

    def __init__(
            self,
            koddi_http_client_service: KoddiHttpClientService = Depends(KoddiHttpClientService),
            async_koddi_http_client_service: AsyncKoddiHttpClientService = Depends(AsyncKoddiHttpClientService),
            lookup_service: LookupService = Depends(LookupService),
            campaign_gateway: CampaignServiceGateway = Depends(CampaignServiceGateway),
            translation: ReportTranslation = Depends(ReportTranslation),
            harness_service: HarnessService = Depends(HarnessService),
    ):
        """Constructor for the ReportService class"""
        self.lookup_service = lookup_service
        self.campaign_gateway = campaign_gateway
        self.translation = translation
        self.__koddi_http_client = AsyncAdapter(
            koddi_http_client_service,
            async_koddi_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_REPORT,
            harness_service=harness_service
        )

    @staticmethod
    def validate_request_report_dates(report_request: ReportRequestCommon):
        if report_request.startDate > report_request.endDate:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        # Dates must be in YYYY-MM-DD format using datetime
        try:
            datetime.strptime(report_request.startDate, '%Y-%m-%d')
            datetime.strptime(report_request.endDate, '%Y-%m-%d')
        except ValueError as err:
            raise HTTPException(status_code=400, detail="Start date and end date must be in YYYY-MM-DD format") from err

    @staticmethod
    def validate_request_filter_and_sort(
            report_request: ReportRequestV1 | ReportRequestV2,
            experience_name: InternalCampaignType
    ):

        available_metrics, available_dimensions = ExperienceNameParamFactory.get_valid_params(
            experience_name,
            report_request
        )

        # Convert to sets for access to set functions
        requested_metrics = {m for m in report_request.metrics}
        requested_dimensions = {d for d in report_request.dimensions}
        requested_filters = {f.field for f in report_request.filters}
        requested_sorts = {s.field for s in report_request.sort}

        # collect unavailable metrics and dimensions
        unavailable_metrics = requested_metrics - available_metrics
        unavailable_dimensions = requested_dimensions - available_dimensions

        # collect invalid or missing filters
        missing_filters = requested_filters.difference(requested_metrics, requested_dimensions)
        filters_with_available_metrics = missing_filters.intersection(available_metrics)
        filters_with_available_dimensions = missing_filters.intersection(available_dimensions)
        invalid_filters = missing_filters.difference(available_metrics, available_dimensions)

        # collect invalid or missing sorts
        missing_sorts = requested_sorts.difference(requested_metrics, requested_dimensions)
        sorts_with_available_metrics = missing_sorts.intersection(available_metrics)
        sorts_with_available_dimensions = missing_sorts.intersection(available_dimensions)
        invalid_sorts = missing_sorts.difference(available_metrics, available_dimensions)

        errors = []
        # Filter errors
        if unavailable_metrics:
            errors.append(ReportService.__build_invalid_value_error(
                "metric",
                unavailable_metrics
            ))
        if unavailable_dimensions:
            errors.append(ReportService.__build_invalid_value_error(
                "dimension",
                unavailable_dimensions
            ))
        if filters_with_available_metrics:
            errors.append(ReportService.__build_missing_value_error(
                "filter",
                "metric",
                filters_with_available_metrics
            ))

        if filters_with_available_dimensions:
            errors.append(ReportService.__build_missing_value_error(
                "filter",
                "dimension",
                filters_with_available_dimensions
            ))

        if invalid_filters:
            errors.append(ReportService.__build_invalid_value_error(
                "filter",
                invalid_filters,
            ))

        # Sort errors
        if sorts_with_available_metrics:
            errors.append(ReportService.__build_missing_value_error(
                "sort",
                "metric",
                sorts_with_available_metrics
            ))

        if sorts_with_available_dimensions:
            errors.append(ReportService.__build_missing_value_error(
                "sort",
                "dimension",
                sorts_with_available_dimensions
            ))

        if invalid_sorts:
            errors.append(ReportService.__build_invalid_value_error(
                "sort",
                invalid_sorts,
            ))

        if errors:
            raise HTTPException(status_code=400, detail={"errors": errors})


    @staticmethod
    def __build_missing_value_error(source: str, destination: str, items: Set[str]) -> KrogerError:
        return KrogerError(
            code=f"{source}s-with-missing-{destination}s",
            reason=f"{source}s were provided without adding {destination}s to the request.",
            rootCauses=[
                ErrorDetail(
                    code=f"{source}-with-missing-{destination}",
                    reason=f"{item} must be included in the request {destination}s to be {source}ed"
                )
                for item in items
            ],
            datetime=ErrorDateTime.now()
        )

    @staticmethod
    def __build_invalid_value_error(source: str, items: Set[str]) -> KrogerError:
        return KrogerError(
            code=f"{source}s-with-invalid-values",
            reason=f"{source}s were provided with invalid values",
            rootCauses=[
                ErrorDetail(
                    code=f"{source}-with-invalid-value",
                    reason=f"{item} must be removed from {source} or replaced with a valid metric or dimension."
                )
                for item in items
            ],
            datetime=ErrorDateTime.now()
        )

    async def __search_and_save_koddi_campaign_ids(
            self,
            short_campaign_ids: List[str],
            cached_koddi_campaign_ids: List[str]) -> List[str | None]:
        # Search the associated koddi campaign id for the short id
        missing_short_ids = [
            short_campaign_id for short_campaign_id, koddi_campaign_id in
            zip(short_campaign_ids, cached_koddi_campaign_ids) if koddi_campaign_id is None
        ]
        payload = CampaignSearchRequest(shortIDs=missing_short_ids, page_offset=0, page_size=len(missing_short_ids))
        campaigns = await self.campaign_gateway.search_campaigns(payload)
        dict_koddi_short_campaigns = {
            campaign.shortId: str(external_id.id)
            for campaign in campaigns.data
            for external_id in campaign.externalIDs
            if external_id.partner == "KODDI_CAMPAIGN_ID"
        }
        koddi_campaign_ids = list(dict_koddi_short_campaigns.values())
        if koddi_campaign_ids:
            if len(koddi_campaign_ids) != len(missing_short_ids):
                # This cause the service is not returning one or many campaign's KODDI_CAMPAIGN_ID
                raise HTTPException(status_code=400, detail="Error trying to get some campaigns information")
            await self.lookup_service.set_koddi_campaign_id_by_short_id_batch(dict_koddi_short_campaigns)
        return koddi_campaign_ids

    async def __translate_internal_short_campaign_id_to_koddi_id(self, short_campaign_ids: List[str]) -> List[str]:
        koddi_campaign_ids = await self.lookup_service.get_koddi_campaign_id_by_short_id_batch(short_campaign_ids)
        if any(koddi_campaign_id is None for koddi_campaign_id in koddi_campaign_ids):
            existing_cached_koddi_campaign_ids = [
                koddi_id for koddi_id in koddi_campaign_ids if koddi_id is not None
            ]
            koddi_campaign_ids = await self.__search_and_save_koddi_campaign_ids(
                short_campaign_ids,
                koddi_campaign_ids,
            )
            koddi_campaign_ids += existing_cached_koddi_campaign_ids
        return koddi_campaign_ids

    async def __create_filters(self, request_filters: List[Filter]) -> List:
        """
        Create filters for the report request
        """
        filters = []
        for item in request_filters:
            operator = MAP_OPERATORS.get(item.operator)
            if not operator:
                raise HTTPException(status_code=400, detail=f"Filter operator {item.operator} is not valid")
            if item.field == "campaign_id":
                short_campaign_ids = item.values
                # Translate to Koddi ids:
                koddi_campaign_ids = await self.__translate_internal_short_campaign_id_to_koddi_id(short_campaign_ids)
                item.values = koddi_campaign_ids
            filters.append({
                "field": item.field,
                "operation": operator,
                "value": item.values
            })
        return filters

    async def request_report(
            self,
            report_request: ReportRequestV1 | ReportRequestV2,
            koddi_brand_ids: Dict[int, List[IdGroup]],
            experience_name: InternalCampaignType,
    ) -> ReportResultResponse:
        logger.info("Requesting report")

        path = '/console/v2/report/targeting'

        filters = await self.__create_filters(report_request.filters)

        # Always include the experience_name filter to return results for the correct campaign type
        filters.append({
            "field": "experience_name",
            "operation": "=",
            "value": [convert_enum(experience_name, KoddiReportExperienceType)]
        })

        dimensions = []
        for item in report_request.dimensions:
            dimensions.append(item.value)

        metrics = []
        for item in report_request.metrics:
            metrics.append(item.value)

        sort = []
        for item in report_request.sort:
            sort.append({
                "field": item.field.value,
                "order": item.order.value
            })
        params = {
            "dimensions": dimensions,
            "metrics": metrics,
            "pagination": {
                "start": report_request.pagination.offset,
                "count": report_request.pagination.size
            },
            "filters": filters,
            "sort": sort,
            "advertiser_ids": list(koddi_brand_ids.keys()),
            "currency_code": CURRENCY_CODE,
            "start_date": report_request.startDate,
            "end_date": report_request.endDate
        }

        logger.info("Report request params: %s", params)

        response = await self.__koddi_http_client.post(
            path=path,
            json=params,
            response_body_type="json",
            forward_client_error_response_content=True
        )

        response_json = response.json()

        if 'status' not in response_json or response_json['status'] != 'success':
            logger.error("Response content: %s", response.content)
            raise HTTPException(status_code=500, detail="Reporting server unavailable. Try again later.")

        total_count = 0
        if response_json['result']['total_count']:
            total_count = response_json['result']['total_count']

        # Dimensions that need to be translated:
        # AD_GROUP_ID -> Internal Ad Group -> Cached Int
        # ADVERTISER_ID -> Internal Advertiser -> Cached Int
        # CAMPAIGN_ID -> Internal Campaign -> Cached Int
        # ENTITY_ID (UPC) -> Internal Product -> Cached Int
        # PURCHASED_ENTITY_ID (UPC) -> Internal Product -> Cached Int
        response_data = response_json['result']['data']
        result_data = []

        unique_response_ids = self.__get_response_ids(response_data)
        external_ids = ExternalIdByKoddiId()
        external_ids.ad_group = await self.translation.build_ad_group_translation(
            unique_response_ids.ad_group_ids
        )
        external_ids.advertiser = self.translation.build_advertiser_translation(
            unique_response_ids.advertiser_ids,
            koddi_brand_ids
        )
        external_ids.campaign = await self.translation.build_campaign_translation(
            unique_response_ids.campaign_ids
        )
        external_ids.upc = await self.translation.build_upc_translation(
            unique_response_ids.upcs,
        )

        missing_lookups = self.translation.build_missing_lookup_warnings(unique_response_ids, external_ids)
        if missing_lookups:
            serialized_warnings = [warning.model_dump() for warning in missing_lookups]
            logger.warning("Could not convert some Koddi ids to external short ids: %s", serialized_warnings)

        for item in response_data:
            koddi_advertiser_id = item.get("advertiser_id")
            translated_report_item = self.__translate_item_ids(item, external_ids)
            self.__add_advertiser_ids(
                koddi_advertiser_id,
                translated_report_item,
                koddi_brand_ids
            )
            result_data.append(translated_report_item)

        return ReportResultResponse(
            headers=response.json()['result']['headers'],
            data=result_data,
            totalCount=total_count
        )

    @staticmethod
    def __get_response_ids(
            response_data: List[dict],
    ) -> UniqueReportIds:
        """
        Collect ids from the response into unique sets of ids.
        We will use these sets later to make batched calls to redis
        Instead of calling redis multiple times per response item.
        """
        report_ids = UniqueReportIds()

        for item in response_data:
            ReportService.__update_id(Dimensions.AD_GROUP_ID, item, report_ids.ad_group_ids)
            ReportService.__update_id(Dimensions.ADVERTISER_ID, item, report_ids.advertiser_ids)
            ReportService.__update_id(Dimensions.CAMPAIGN_ID, item, report_ids.campaign_ids)
            ReportService.__update_id(Dimensions.ENTITY_ID, item, report_ids.upcs)
            ReportService.__update_id(Dimensions.PURCHASED_ENTITY_ID, item, report_ids.upcs)

        return report_ids

    @staticmethod
    def __update_id(
            key: str,
            item: dict,
            id_set: Set
    ):
        if key in item and item.get(key) is not None:
            id_set.add(item.get(key))

    @staticmethod
    def __translate_item_ids(
            item: dict,
            external_id_by_koddi_id: ExternalIdByKoddiId
    ) -> dict:
        """
        Given an item and a lookup table,
        Translate the current item ids using the lookup table.
        """
        ReportService.__translate_id(Dimensions.AD_GROUP_ID, item, external_id_by_koddi_id.ad_group)
        ReportService.__translate_id(Dimensions.ADVERTISER_ID, item, external_id_by_koddi_id.advertiser)
        ReportService.__translate_id(Dimensions.CAMPAIGN_ID, item, external_id_by_koddi_id.campaign)
        ReportService.__translate_id(Dimensions.ENTITY_ID, item, external_id_by_koddi_id.upc)
        ReportService.__translate_id(Dimensions.PURCHASED_ENTITY_ID, item, external_id_by_koddi_id.upc)

        return item

    @staticmethod
    def __translate_id(
            key: str,
            item: dict,
            id_lookup: dict
    ):
        if key in item:
            item[key] = id_lookup.get(item.get(key))

    @staticmethod
    def __add_advertiser_ids(
            koddi_advertiser_id: int | None,
            translated_report_item: dict,
            koddi_brand_ids: Dict[int, List[IdGroup]]
    ) -> None:
        """
        Adds all advertiser short ids to a report item if advertiser_id is present.
        """
        if Dimensions.ADVERTISER_ID in translated_report_item and koddi_advertiser_id is not None:
            id_groups = koddi_brand_ids.get(koddi_advertiser_id)
            short_advertiser_ids = [
                id_group.short_id
                for id_group in id_groups
                if id_group.short_id
            ]
            translated_report_item["advertiser_ids"] = short_advertiser_ids

class ExperienceNameParamFactory:
    @staticmethod
    def get_valid_params(
            experience_name: InternalCampaignType,
            report_request: ReportRequestV1 | ReportRequestV2
    ) -> Tuple[Set[MetricsV1 | MetricsV2],Set[DimensionsV1 | DimensionsV2]]:
        """
        Returns a tuple of available metrics and dimensions based on the experience name.
        """
        available_metrics: Set[MetricsV1 | MetricsV2] = set()
        available_dimensions: Set[DimensionsV1 | DimensionsV2] = set()

        # Check the experience name and filter out invalid metrics and dimensions
        if isinstance(report_request, ReportRequestV1):
            available_metrics = {m for m in MetricsV1}
            available_dimensions = {d for d in DimensionsV1}
            if experience_name == InternalCampaignType.CAROUSEL:
                available_dimensions -= {d for d in CarrouselInvalidDimensionsV1}

        elif isinstance(report_request, ReportRequestV2):
            available_metrics = {m for m in MetricsV2}
            available_dimensions = {d for d in DimensionsV2}
            if experience_name == InternalCampaignType.TOA:
                available_metrics -= {m for m in TOAInvalidMetricsV2}
                available_dimensions -= {d for d in TOAInvalidDimensionsV2}

            elif experience_name == InternalCampaignType.CAROUSEL:
                available_dimensions -= {d for d in CarrouselInvalidDimensionsV2}

        return available_metrics, available_dimensions
