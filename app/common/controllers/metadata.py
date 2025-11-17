from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi_versioning import version

from app.common.decorators.decorators import disable_if_flag_on
from app.common.decorators.requires_all_roles import requires_all_roles
from app.common.model.account import AccountResponse
from app.common.model.address import AdvertiserAddressResponse
from app.common.model.advertiser import AdvertiserResponse, AdvertiserType
from app.common.model.campaign_types import InternalCampaignType
from app.common.model.contact import AdvertiserContactResponse
from app.common.model.division import DivisionResponse
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.model.placement import PlacementResponse
from app.common.model.product import ProductResponse
from app.common.model.shared import Meta, Page
from app.common.model.targets import TargetResponse
from app.common.services.account_service import AccountService
from app.common.services.address_service import AdvertiserAddressService
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.contact_service import AdvertiserContactService
from app.common.services.division_service import DivisionService
from app.common.services.metadata_service import MetadataService
from app.common.services.placement_service import PlacementService
from app.common.services.product_service import ProductService
from app.common.services.target_service import TargetService
from app.common.utils import filtered_logger
from app.common.utils.exceptions import CustomHTTPExceptionRoute
from app.common.utils.jwt import validate_account, validate_advertiser, validate_user
from app.common.view_models import AuthRole

logger = filtered_logger.get_logger(__name__)

router = APIRouter(
    route_class=CustomHTTPExceptionRoute,
    tags=["Metadata Endpoints"]
)

@version(2)
@router.get(path="/metadata/accounts",
            name="Get Accounts",
            description="Returns a list of all the available accounts for a given account. "
                        "Read more about [Contacts]"
                        "(https://mp-help.8451.com/mp-help/content/how-to/create-campaign.htm#EnterContactInformation) "
                        "in the Media Platform Learning Center. "
                        "Whenever there is an update to contacts or addresses, users are required to make a GET /accounts call. "
                        "This will cache the updated contacts and addresses.",
            response_model=AccountResponse,
            status_code=status.HTTP_200_OK)
@disable_if_flag_on(
    HarnessFeatureFlags.DISABLE_V1,
    message="endpoint deprecated, please use v2/metadata/accounts instead"
)
async def get_accounts(
        request: Request,
        offset: int = Query(default=0, description="The offset of the first accounts to return"),
        size: int = Query(default=10, le=100, ge=1, description="The number of accounts to return"),
        metadata_service: MetadataService = Depends(MetadataService)
) -> AccountResponse:
    logger.info("GET /accounts request received")

    return await metadata_service.get_accounts_and_cache_addresses_and_contacts(offset, size)

@version(2)
@router.get(path="/metadata/placements",
            name="Get Placements",
            description="Returns a list of all the available placements. Read more about "
                        "[Placements]"
                        "(https://mp-help.8451.com/mp-help/content/how-to/create-pla.htm?Highlight="
                        "placements#EnterAdGroupDetails) in the Media Platform Learning Center.",
            response_model=PlacementResponse,
            dependencies=[Depends(validate_user)],
            status_code=status.HTTP_200_OK)
@disable_if_flag_on(
    HarnessFeatureFlags.DISABLE_V1,
    message="endpoint deprecated, please use v2/metadata/placements instead"
)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_placements(request: Request, offset: int = Query(default=0, description="The offset of the first placement to return"),
                         size: int = Query(default=10, le=100, ge=1, description="The number of placements to return"),
                         placement_service: PlacementService = Depends(PlacementService)) -> PlacementResponse:

    logger.info("GET /placements Getting all placements")
    placements = await placement_service.get_placements()

    has_more = len(placements) > offset + size

    placements = placements[offset:offset + size]

    return PlacementResponse(
        data=jsonable_encoder(placements),
        meta={"page": {"offset": offset, "size": size, "hasMore": has_more}}
    )

@version(2)
@router.get(path="/metadata/divisions",
            name="Get Divisions",
            description="Returns a list of all the available division. Read more about "
                        "[Divisions]"
                        "(https://mp-help.8451.com/mp-help/content/how-to/create-pla.htm?Highlight=division#Editbids) "
                        "in the Media Platform Learning Center.",
            response_model=DivisionResponse,
            dependencies=[Depends(validate_user)],
            status_code=status.HTTP_200_OK)
@disable_if_flag_on(
    HarnessFeatureFlags.DISABLE_V1,
    message="endpoint deprecated, please use v2/metadata/divisions instead"
)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_divisions(request: Request, offset: int = Query(default=0, description="The offset of the first divisions to return"),
                        size: int = Query(default=10, le=100, ge=1, description="The number of divisions to return"),
                        division_service: DivisionService = Depends(DivisionService)) -> DivisionResponse:

    logger.info("GET /divisions Getting all divisions")
    divisions = await division_service.get_divisions()

    has_more = len(divisions) > offset + size

    divisions = divisions[offset:offset + size]

    return DivisionResponse(
        data=jsonable_encoder(divisions),
        meta={"page": {"offset": offset, "size": size, "hasMore": has_more}}
    )

### GET targets endpoint missing on arch diagram - Returns a list of targets.

@version(2)
@router.get(path="/metadata/targets",
            name="Get Targets",
            description="Returns a list of all the available targets.",
            response_model=TargetResponse,
            dependencies=[Depends(validate_user)],
            status_code=status.HTTP_200_OK,
            response_model_exclude_none=True)
@disable_if_flag_on(
    HarnessFeatureFlags.DISABLE_V1,
    message="endpoint deprecated, please use v2/metadata/targets instead"
)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_targets(
        request: Request,
        offset: int = Query(default=0, description="The offset of the first target to return"),
        size: int = Query(default=10, le=100, ge=1, description="The number of targets to return"),
        target_service: TargetService = Depends(TargetService)
) -> TargetResponse:
    logger.info("GET /targets Getting all targets")
    targets = target_service.get_targets()

    has_more = len(targets) > offset + size

    targets = targets[offset:offset + size]

    return TargetResponse(
        data=jsonable_encoder(targets),
        meta={"page": {"offset": offset, "size": size, "hasMore": has_more}}
    )

async def get_products_common(
        current_user: Dict[str, Any],
        advertiser_id: int,
        offset: int,
        size: int,
        type: InternalCampaignType,
        product_service: ProductService,
        advertiser_service: AdvertiserService
) -> ProductResponse:
    await validate_advertiser(current_user, advertiser_id, advertiser_service)
    agency_id = None
    if current_user['is_agency'] is True:
        agency_id = current_user['works_for']['clientId']

    logger.info("GET /products Getting all products")

    advertiser = await advertiser_service.get_advertiser_by_numeric_id(advertiser_id)
    if advertiser is None:
        raise HTTPException(status_code=404, detail="Advertiser not found")

    products, has_more = await product_service.get_products_by_brand(
        [advertiser],
        offset,
        size,
        agency_id,
        type
    )

    return ProductResponse(
        data=jsonable_encoder(products),
        meta=Meta(
            page=Page(
                offset=offset,
                size=size,
                hasMore=has_more)))


async def get_contacts_common(current_user: Dict[str, Any],
                              account_id: int,
                              offset: int,
                              size: int,
                              contact_service: AdvertiserContactService,
                              account_service: AccountService) -> AdvertiserContactResponse:

    await validate_account(current_user, account_id, account_service)
    internal_account_id = await account_service.get_account_by_numeric_id(account_id)
    if internal_account_id is None:
        raise HTTPException(status_code=404, detail="Account not found")

    logger.info("GET /contacts getting contacts for account")

    if current_user['is_agency'] is True:
        agency_id = current_user['works_for']['clientId']
        contacts = (await contact_service.get_contacts_by_account(contact_type=AdvertiserType.CPG,
                                                            client_account_id=internal_account_id)
                    + await contact_service.get_contacts_by_account(contact_type=AdvertiserType.AGENCY,
                                                              client_account_id=internal_account_id,
                                                              agency_account_id=agency_id))
        logger.info('CPG + Agency contacts received %s', len(contacts))
    else:
        contacts = await contact_service.get_contacts_by_account(
            contact_type=AdvertiserType.CPG,
            client_account_id=internal_account_id)

        logger.info('CPG contacts received %s', len(contacts))

    has_more = len(contacts) > offset + size

    contacts = contacts[offset:offset + size]

    return AdvertiserContactResponse(
        data=jsonable_encoder(contacts),
        meta={"page": {"offset": offset, "size": size, "hasMore": has_more}}
    )


async def get_addresses_common(current_user: Dict[str, Any],
                               account_id: int,
                               offset: int,
                               size: int,
                               address_service: AdvertiserAddressService,
                               account_service: AccountService) -> AdvertiserAddressResponse:
    await validate_account(current_user, account_id, account_service)

    logger.info("GET /addresses Getting user accounts")
    account = await account_service.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    logger.info("GET /addresses getting addresses for account")

    if current_user['is_agency'] is True:
        agency_id = current_user['works_for']['clientId']
        agency_name = current_user['works_for']['displayName']
        logger.info("current user: %s", current_user)
        addresses = (await address_service.get_and_cache_addresses_by_account(account.id, account.name, AdvertiserType.CPG) +
                     await address_service.get_and_cache_addresses_by_account(agency_id, agency_name, AdvertiserType.AGENCY))
    else:
        addresses = await (address_service.get_and_cache_addresses_by_account(account.id, account.name, AdvertiserType.CPG))

    has_more = len(addresses) > offset + size

    result = addresses[offset:offset + size]

    return AdvertiserAddressResponse(
        data=jsonable_encoder(result),
        meta={"page": {"offset": offset, "size": size, "hasMore": has_more}}
    )


async def get_advertisers_common(current_user: Dict[str, Any],
                                account_id: int,
                                offset: int,
                                size: int,
                                advertiser_service: AdvertiserService,
                                account_service: AccountService) -> AdvertiserResponse:
    await validate_account(current_user, account_id, account_service)
    has_more = False

    logger.info("GET /advertisers Getting user accounts")
    account = await account_service.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    logger.info("GET /advertisers getting advertisers for account")
    advertisers = await advertiser_service.get_advertisers(account, account_id)

    if len(advertisers) > offset + size:
        has_more = True

    advertisers = advertisers[offset:offset + size]

    return AdvertiserResponse(
        data=jsonable_encoder(advertisers),
        meta={"page": {"offset": offset, "size": size, "hasMore": has_more}}
    )
