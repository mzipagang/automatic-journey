import unittest
from copy import deepcopy
from unittest.mock import patch, AsyncMock, Mock, call, MagicMock
from fastapi import Request

from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.v2.controllers import (
    create_campaign,
    get_campaign_by_id,
    get_campaigns_by_advertiser,
    update_campaign
)
from app.common.view_models import CampaignPutRequest, AuthRole
from app.v2.view_models import CampaignRequest
from app.common.model.campaign_types import CampaignType, InternalCampaignType
from tests.unit.v2 import CAMPAIGN_SINGLE_RESPONSE, CAMPAIGN_LIST_RESPONSE


class TestCampaignsV2(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_request = Mock(spec=Request)
        self.mock_campaign_service = AsyncMock()
        self.mock_advertiser_service = AsyncMock()
        self.current_user = {'username': 'test_user', 'internal': True}
        self.campaign_request = CampaignRequest(
            name='Test Campaign',
            status='DRAFT',
            budgetAmount=1000.0,
            budgetType='DAILY',
            pacingType='EVEN',
            startDate='2025-01-01',
            advertiserIds=[1, 2],
            accountId=1,
            billingInsertionOrder='IO-001',
            billingContactId=1,
            billingAddressId=1
        )
        self.mock_harness_service = MagicMock()
        self.mock_harness_service.is_harness_flag_on.return_value = True


    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    @patch('app.common.utils.http_request.get_consumer_source', return_value='MEDIA_ACTIVATION_PLATFORM')
    @patch('app.v2.controllers.validate_user', new_callable=AsyncMock)
    async def test_create_campaign__should_succeed(self, mock_validate_user, mock_get_source, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        self.mock_campaign_service.create_campaign.return_value = CAMPAIGN_SINGLE_RESPONSE
        mock_validate_user.return_value = self.current_user

        result = await create_campaign(
            request=self.mock_request,
            campaign_request=self.campaign_request,
            current_user=self.current_user,
            campaign_service=self.mock_campaign_service,
        )

        self.assertEqual(result, CAMPAIGN_SINGLE_RESPONSE)
        self.mock_campaign_service.create_campaign.assert_called_once()

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_get_campaign_by_id__should_return_campaign(self, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        self.mock_campaign_service.get_campaign_single_response_by_id.return_value = CAMPAIGN_SINGLE_RESPONSE

        response = await get_campaign_by_id(
            campaign_id=1,
            include_ad_groups=False,
            include_ad_group_errors=False,
            campaign_service=self.mock_campaign_service,
            harness_service=self.mock_harness_service,
        )

        self.assertEqual(response, CAMPAIGN_SINGLE_RESPONSE)
        self.mock_campaign_service.get_campaign_single_response_by_id.assert_called_once()

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_get_campaign_by_id__can_get_ad_group_errors(self, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        expected_response = deepcopy(CAMPAIGN_SINGLE_RESPONSE)
        expected_response.errors = []
        expected_response.warnings = []
        self.mock_campaign_service.get_campaign_single_response_by_id.return_value = expected_response

        response = await get_campaign_by_id(
            campaign_id=1,
            include_ad_groups=True,
            include_ad_group_errors=True,
            campaign_service=self.mock_campaign_service,
            harness_service=self.mock_harness_service,
        )

        self.assertEqual(expected_response, response)
        self.mock_campaign_service.get_campaign_single_response_by_id.assert_called_once()

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    @patch('app.v2.controllers.validate_user', new_callable=AsyncMock)
    @patch('app.v2.controllers.validate_advertiser', new_callable=AsyncMock)
    async def test_get_campaigns_by_advertiser__should_succeed(self, mock_validate_advertiser, mock_validate_user, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        mock_advertiser = MagicMock()
        self.mock_advertiser_service.get_advertiser_by_numeric_id.return_value = mock_advertiser
        self.mock_campaign_service.get_campaigns_paginated_by_external_advertiser.return_value = CAMPAIGN_LIST_RESPONSE
        mock_validate_user.return_value = self.current_user

        result = await get_campaigns_by_advertiser(
            current_user=self.current_user,
            advertiser_id=1,
            campaign_type=CampaignType.PLA,
            offset=0,
            size=10,
            campaign_service=self.mock_campaign_service,
            advertiser_service=self.mock_advertiser_service
        )

        self.assertEqual(result, CAMPAIGN_LIST_RESPONSE)
        self.mock_campaign_service.get_campaigns_paginated_by_external_advertiser.assert_called_with(
            mock_advertiser,
            InternalCampaignType.PLA,
            0,
            10
        )

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    @patch('app.common.utils.http_request.get_consumer_source', return_value='MEDIA_ACTIVATION_PLATFORM')
    @patch('app.v2.controllers.validate_user', new_callable=AsyncMock)
    @patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag',
           return_value={"enabled": False})
    async def test_update_campaign__should_succeed(self, mock_fetch_multivariate_flag, mock_validate_user, mock_get_source,get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        campaign_put_request = CampaignPutRequest(
            name='Test Campaign',
            status='DRAFT',
            budgetAmount=1000.0,
            pacingType='EVEN',
            startDate='2025-01-01'
        )
        self.mock_campaign_service.update_campaign.return_value = CAMPAIGN_SINGLE_RESPONSE
        mock_validate_user.return_value = self.current_user

        result = await update_campaign(
            request=self.mock_request,
            campaign_id=1,
            campaign_request=campaign_put_request,
            current_user=self.current_user,
            campaign_service=self.mock_campaign_service,
        )

        self.assertEqual(result, CAMPAIGN_SINGLE_RESPONSE)
        self.mock_campaign_service.update_campaign.assert_called_once()
        mock_fetch_multivariate_flag.assert_has_calls([call(
            flag_name=HarnessFeatureFlags.UPDATE_CAMPAIGN_LOCK_CONFIG,
            target_id="default")])
