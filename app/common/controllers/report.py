from typing import Dict, List

from fastapi import Depends, HTTPException

from app.common.context.context import logging_extra_context
from app.common.model.advertiser import CachedAdvertiser, KoddiAdvertiser
from app.common.model.campaign_types import InternalCampaignType
from app.common.model.report import IdGroup
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.report_service import ReportService
from app.common.utils import filtered_logger
from app.common.utils.context_tools import update_context
from app.common.utils.jwt import validate_user
from app.common.view_models.report import (
    ReportRequestCommon,
    ReportResultResponse,
)
from app.v2.view_models.report import ReportRequestV2, ReportRequestV1

logger = filtered_logger.get_logger(__name__)

async def get_report(
        report_request: ReportRequestV1 | ReportRequestV2,
        experience_name: InternalCampaignType,
        current_user=Depends(validate_user),
        report_service: ReportService = Depends(ReportService),
        advertiser_service: AdvertiserService = Depends(AdvertiserService)
) -> ReportResultResponse:
    update_context(
        logging_extra_context,
        reporting=report_request.model_dump(mode='json')
    )
    logger.info("Submitting report")

    # Check report request start and end date validity
    report_service.validate_request_report_dates(report_request)

    # Check that the requested filter and sort operations match up to requested metrics and dimensions
    report_service.validate_request_filter_and_sort(report_request, experience_name)

    # build koddi brand id lookup table
    koddi_brand_ids = await build_koddi_id_dict(
        report_request.advertiserIds,
        current_user,
        advertiser_service
    )

    report_response = await report_service.request_report(report_request, koddi_brand_ids, experience_name)

    log_response(report_response, report_request, current_user)

    return report_response

async def get_advertisers_and_id_map(
    external_short_advertiser_ids: list[int],
    advertiser_service: AdvertiserService
):
    external_short_advertiser_ids_by_brand_id = {}
    advertisers = await advertiser_service.get_advertisers_by_numeric_ids(external_short_advertiser_ids)
    for external_short_advertiser_id, advertiser in zip(external_short_advertiser_ids, advertisers):
        external_short_advertiser_ids_by_brand_id[advertiser.brandId] = external_short_advertiser_id

    return advertisers, external_short_advertiser_ids_by_brand_id

def check_advertiser_access(
        current_user: dict,
        advertisers: list[CachedAdvertiser]
):
    # Find advertisers the user does not have access to
    advertisers_without_access = list(filter(
        lambda advertiser: current_user['internal'] is False and advertiser.brandId not in current_user['brands'],
        advertisers))

    # Throw an error for advertisers the user does not have access to
    if len(advertisers_without_access) > 0:
        logger.warning("User Email: %s", current_user['email'])
        logger.warning("User has access to brands: %s", current_user['brands'])
        logger.warning("User requested access to brands: %s", advertisers_without_access)
        raise HTTPException(status_code=403, detail={
            "msg": "User does not have access to advertisers",
            "advertisers": list(map(lambda item: item.id, advertisers_without_access))})

def build_user_koddi_id_dict(
        user_koddi_advertisers: list[KoddiAdvertiser],
        agency_id: str | None,
) -> Dict[str, List[int]]:
    user_koddi_ids_by_brand_id = {}
    for koddi_advertiser in user_koddi_advertisers:
        if agency_id and koddi_advertiser.agencyId != agency_id:
            continue
        for brand_id in koddi_advertiser.brandIds:
            koddi_ids = user_koddi_ids_by_brand_id.get(brand_id, [])
            koddi_ids.append(koddi_advertiser.koddiId)
            user_koddi_ids_by_brand_id[brand_id] = koddi_ids

    return user_koddi_ids_by_brand_id

async def build_koddi_id_dict (
        external_short_advertiser_ids: list[int],
        current_user: dict[str, any],
        advertiser_service: AdvertiserService,
) -> Dict[int, List[IdGroup]]:
    advertisers, short_ids_by_brand_id = await get_advertisers_and_id_map(
        external_short_advertiser_ids,
        advertiser_service)

    check_advertiser_access(current_user, advertisers)

    # Get all Koddi advertisers the current user has access to
    user_koddi_advertisers = await advertiser_service.get_advertisers_for_user()

    # Create mappings between advertiser ids (short id, long id, koddi id)
    agency_id = None
    if current_user['is_agency'] is True:
        agency_id = current_user['works_for']['clientId']

    user_koddi_ids_by_brand_id = build_user_koddi_id_dict(user_koddi_advertisers, agency_id)

    koddi_brand_ids = {}
    for advertiser in advertisers:
        koddi_ids = user_koddi_ids_by_brand_id.get(advertiser.brandId, [])
        for koddi_id in koddi_ids:
            mapped_advertiser_list = koddi_brand_ids.get(koddi_id, [])
            mapped_advertiser_list.append(IdGroup(
                koddi_id=koddi_id,
                long_id=advertiser.brandId,
                short_id=short_ids_by_brand_id.get(advertiser.brandId)
            ))
            koddi_brand_ids[koddi_id] = mapped_advertiser_list

    return koddi_brand_ids

def log_response (
        report_response,
        report_request,
        current_user: dict[str, any],
):
    koddi_total_count = report_response.totalCount
    data_len = len(report_response.data)
    requested_size = report_request.pagination.size
    requested_offset = report_request.pagination.offset
    advertisers_list_string = ", ".join([str(advertiser_id) for advertiser_id in report_request.advertiserIds])

    logger.info(
        "REPORT; User: %s, "
        "Koddi count: %d, "
        "Returned count: %d, "
        "Requested size: %d, "
        "Offset: %d, "
        "Advertisers: [%s]",
        current_user['email'],
        koddi_total_count,
        data_len,
        requested_size,
        report_request.pagination.offset,
        advertisers_list_string)

    total_returned_count = requested_offset + data_len
    if data_len < requested_size and total_returned_count < koddi_total_count:
        logger.critical(
            "REPORT; User: %s, "
            "Koddi count: %d, "
            "Returned count: %d, "
            "Requested size: %d, "
            "Offset: %d, "
            "Advertisers: [%s]",
            current_user['email'],
            koddi_total_count,
            data_len,
            requested_size,
            requested_offset,
            advertisers_list_string)