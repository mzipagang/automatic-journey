from typing import List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from app.common.configuration.constants import UPCS_LAST_SOLD_WITHIN_DAYS
from app.common.gateways.activation_gateway import ActivationGateway
from app.common.gateways.campaign_service_gateway import CampaignServiceGateway
from app.common.model.downstream.campaign_activation_service import CASAccount, CASCampaign
from app.common.model.downstream.campaign_service import CampaignResponse
from app.common.model.product import Product
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.lookup_service import LookupService
from app.common.services.product_service import ProductService
from app.v2.model.downstream.activation_service import ActivationResponseV2, ActivationResponse, Included, \
    ConfigurationByActivation, EditableField
from app.v2.services.ad_group_product_service import AdGroupProductService


class TestAdGroupProductService(IsolatedAsyncioTestCase):
    def setUp(self):
        self.__mock_lookup = AsyncMock(spec=LookupService)
        self.__mock_advertiser_service = AsyncMock(spec=AdvertiserService)
        self.__mock_activation_gateway = AsyncMock(spec=ActivationGateway)
        self.__mock_product_service = AsyncMock(spec=ProductService)
        self.__mock_campaign_gateway = AsyncMock(spec=CampaignServiceGateway)
        self.__mock_campaign_service = AsyncMock()

        self.subject = AdGroupProductService(
            lookup=self.__mock_lookup,
            advertiser_service=self.__mock_advertiser_service,
            activation_gateway=self.__mock_activation_gateway,
            product_service=self.__mock_product_service,
            campaign_gateway=self.__mock_campaign_gateway)

    def _base_case_setup__get_products_by_ad_group(self):
        self.__mock_lookup.get_adgroup_long_id_by_short_id.return_value = "ag123"
        self.__mock_activation_gateway.get_activation_by_id.return_value = AsyncMock(
            spec=ActivationResponseV2[ActivationResponse],
            data=MagicMock(
                spec=ActivationResponse,
                campaign_id="c123"),
            included=MagicMock(
                spec=Included,
                configuration_by_activation={
                    'ag123': MagicMock(
                        spec=ConfigurationByActivation,
                        biddableEntities=MagicMock(
                            spec=EditableField,
                            last_sold_within_days=29.0))}))
        self.__mock_campaign_gateway.get_campaign.return_value = AsyncMock(
            spec=CampaignResponse,
            publishedChanges=MagicMock(
                spec=CASCampaign,
                primaryAccount=MagicMock(spec=CASAccount, brands=MagicMock(spec=List[str])),
                get_koddi_advertiser_id=lambda: 4242))
        self.__mock_product_service.get_products_by_brand.return_value = (MagicMock(spec=Product), MagicMock(spec=bool))

    async def _basic_call__get_products_by_ad_group(self):
        return await self.subject.get_products_by_ad_group(
            current_user={'is_agency': False},
            ad_group_id=123,
            offset=0,
            page_size=100)

    def _basic_assertions__get_products_by_ad_group(self):
        self.assertEqual(0,
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['offset'])
        self.assertEqual(100,
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['limit'])
        self.__mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(123)

    def _common_assertion__get_products_by_ad_group__last_sold_within_days(self):
        self.assertEqual(29.0,
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['last_sold_within_days'])

    async def test_get_products_by_ad_group__agency_user(self):
        self._base_case_setup__get_products_by_ad_group()

        await self.subject.get_products_by_ad_group(
            current_user={'works_for': {'clientId': 'agency123'}, 'is_agency': True},
            ad_group_id=123,
            offset=0,
            page_size=100)

        self.__mock_product_service.get_products_by_brand.assert_called_once()
        self._common_assertion__get_products_by_ad_group__last_sold_within_days()
        self._basic_assertions__get_products_by_ad_group()
        self.assertEqual(
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['agency_id'], 'agency123')

    async def test_get_products_by_ad_group__published_changes(self):
        self._base_case_setup__get_products_by_ad_group()
        self.__mock_campaign_gateway.get_campaign.return_value = AsyncMock(
            spec=CampaignResponse,
            publishedChanges=MagicMock(
                spec=CASCampaign,
                primaryAccount=MagicMock(spec=CASAccount, brands=[123, 456]),
                get_koddi_advertiser_id=lambda: 4343))

        await self._basic_call__get_products_by_ad_group()

        self.__mock_product_service.get_products_by_brand.assert_called_once()
        self._common_assertion__get_products_by_ad_group__last_sold_within_days()
        self._basic_assertions__get_products_by_ad_group()
        self.assertEqual(
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['koddi_advertiser_id'], 4343)
        self.__mock_lookup.get_advertiser_short_id_by_long_id_batch.assert_called_once_with([123, 456])

    async def test_get_products_by_ad_group__un_published_changes(self):
        self._base_case_setup__get_products_by_ad_group()
        self.__mock_campaign_gateway.get_campaign.return_value = AsyncMock(
            spec=CampaignResponse,
            publishedChanges=None,
            unpublishedChanges=MagicMock(
                spec=CASCampaign,
                primaryAccount=MagicMock(spec=CASAccount, brands=[123, 456]),
                get_koddi_advertiser_id=lambda: 4444))

        await self._basic_call__get_products_by_ad_group()

        self.assertEqual(
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['koddi_advertiser_id'], 4444)
        self.__mock_lookup.get_advertiser_short_id_by_long_id_batch.assert_called_once_with([123, 456])

    async def test_get_products_by_ad_group__activation_data_no_config_by_activation_key(self):
        self._base_case_setup__get_products_by_ad_group()
        self.__mock_activation_gateway.get_activation_by_id.return_value = AsyncMock(
            spec=ActivationResponseV2[ActivationResponse],
            data=MagicMock(
                spec=ActivationResponse,
                campaign_id="c123"),
            included=MagicMock(
                spec=Included,
                configuration_by_activation={}))

        await self._basic_call__get_products_by_ad_group()

        self.__mock_product_service.get_products_by_brand.assert_called_once()
        self._basic_assertions__get_products_by_ad_group()
        self.assertEqual(
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['last_sold_within_days'],
            UPCS_LAST_SOLD_WITHIN_DAYS
        )

    async def test_get_products_by_ad_group__activation_data_no_config_by_activation(self):
        self._base_case_setup__get_products_by_ad_group()
        self.__mock_activation_gateway.get_activation_by_id.return_value = AsyncMock(
            spec=ActivationResponseV2[ActivationResponse],
            data=MagicMock(
                spec=ActivationResponse,
                campaign_id="c123"),
            included=MagicMock(
                spec=Included,
                configuration_by_activation=None))

        await self._basic_call__get_products_by_ad_group()

        self.__mock_product_service.get_products_by_brand.assert_called_once()
        self._basic_assertions__get_products_by_ad_group()
        self.assertEqual(
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['last_sold_within_days'],
            UPCS_LAST_SOLD_WITHIN_DAYS
        )

    async def test_get_products_by_ad_group__activation_data_no_included(self):
        self._base_case_setup__get_products_by_ad_group()
        self.__mock_activation_gateway.get_activation_by_id.return_value = AsyncMock(
            spec=ActivationResponseV2[ActivationResponse],
            data=MagicMock(
                spec=ActivationResponse,
                campaign_id="c123"),
            included=None)

        await self._basic_call__get_products_by_ad_group()

        self.__mock_product_service.get_products_by_brand.assert_called_once()
        self._basic_assertions__get_products_by_ad_group()
        self.assertEqual(
            self.__mock_product_service.get_products_by_brand.call_args.kwargs['last_sold_within_days'],
            UPCS_LAST_SOLD_WITHIN_DAYS
        )
