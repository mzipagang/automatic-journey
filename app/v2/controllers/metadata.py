from fastapi.params import Depends, Query
from fastapi_versioning import version
from starlette import status

from app.common.controllers.metadata import get_products_common, router, get_contacts_common, \
    get_addresses_common, get_advertisers_common
from app.common.decorators.requires_all_roles import requires_all_roles
from app.common.model.address import AdvertiserAddressResponse
from app.common.model.advertiser import AdvertiserResponse
from app.common.model.campaign_types import convert_enum, CampaignType, InternalCampaignType
from app.common.model.contact import AdvertiserContactResponse
from app.common.model.product import ProductResponse
from app.common.services.account_service import AccountService
from app.common.services.address_service import AdvertiserAddressService
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.contact_service import AdvertiserContactService
from app.common.services.product_service import ProductService
from app.common.utils.jwt import validate_user
from app.common.view_models import AuthRole


@version(2)
@router.get(path="/metadata/products",
            name="Get Products",
            description="Returns a list of all the available products for a given advertiser.",
            response_model=ProductResponse,
            status_code=status.HTTP_200_OK)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_products(
        current_user=Depends(validate_user),
        advertiser_id: int = Query(alias="advertiser_id", description="The advertiser ID to get products for"),
        offset: int = Query(default=0, description="The offset of the first product to return"),
        size: int = Query(default=10, le=100, ge=1, description="The number of products to return"),
        type: CampaignType = Query(default=CampaignType.PLA, description="Type for this products"),
        product_service: ProductService = Depends(ProductService),
        advertiser_service: AdvertiserService = Depends(AdvertiserService)) -> ProductResponse:
    return await get_products_common(
        current_user,
        advertiser_id,
        offset,
        size,
        convert_enum(type, InternalCampaignType),
        product_service,
        advertiser_service
    )

@version(2)
@router.get(path="/metadata/contacts",
            name="Get Contacts",
            description="Returns a list of all the available contacts for a given account. Read more about "
                        "[Contacts]"
                        "(https://mp-help.8451.com/mp-help/content/how-to/create-campaign.htm#EnterContactInformation) "
                        "in the Media Platform Learning Center. "
                        "Whenever there is an update to contacts, users are required to make a GET /accounts call. "
                        "This will cache the updated contacts.",
            response_model=AdvertiserContactResponse,
            status_code=status.HTTP_200_OK)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_contacts(
        current_user=Depends(validate_user),
        account_id: int = Query(alias="account_id", description="The account id to get contacts for"),
        offset: int = Query(default=0, description="The offset of the first contact to return"),
        size: int = Query(default=10, le=100, ge=1, description="The number of contacts to return"),
        contact_service: AdvertiserContactService = Depends(AdvertiserContactService),
        account_service: AccountService = Depends(AccountService)) -> AdvertiserContactResponse:
    return await get_contacts_common(current_user, account_id, offset, size, contact_service, account_service)

@version(2)
@router.get(path="/metadata/addresses",
            name="Get Addresses",
            description="Returns a list of all the available addresses for a given account. Read more about "
                        "[Addresses]"
                        "(https://mp-help.8451.com/mp-help/content/how-to/create-campaign.htm#EnterContactInformation) "
                        "in the Media Platform Learning Center. "
                        "Whenever there is an update to addresses, users are required to make a GET /accounts call. "
                        "This will cache the updated addresses."
                        "Important: For Agency users, this endpoint will return available Agency and CPG addresses." 
                        "CPG users are limited to retrieve CPG-only addresses.",
            response_model=AdvertiserAddressResponse,
            status_code=status.HTTP_200_OK)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_addresses(
        current_user=Depends(validate_user),
        account_id: int = Query(alias="account_id", description="The account id to get contacts for"),
        offset: int = Query(default=0, description="The offset of the first contact to return"),
        size: int = Query(default=10, le=100, ge=1, description="The number of contacts to return"),
        address_service: AdvertiserAddressService = Depends(AdvertiserAddressService),
        account_service: AccountService = Depends(AccountService)) -> AdvertiserAddressResponse:
    return await get_addresses_common(current_user, account_id, offset, size, address_service, account_service)


@version(2)
@router.get(path="/metadata/advertisers",
            name="Get Advertisers",
            description="Returns a list of all the available advertisers for a given account.",
            response_model=AdvertiserResponse,
            status_code=status.HTTP_200_OK)
async def get_advertisers(
        current_user=Depends(validate_user),
        account_id: int = Query(alias="account_id", description="The account ID to get advertisers for"),
        offset: int = Query(default=0, description="The offset of the first advertiser to return"),
        size: int = Query(default=10, le=100, ge=1, description="The number of advertisers to return"),
        advertiser_service: AdvertiserService = Depends(AdvertiserService),
        account_service: AccountService = Depends(AccountService)) -> AdvertiserResponse:
    return await get_advertisers_common(current_user, account_id, offset, size, advertiser_service, account_service)