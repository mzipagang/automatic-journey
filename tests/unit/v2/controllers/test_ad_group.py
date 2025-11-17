import unittest
from unittest.mock import patch, AsyncMock, MagicMock

from app.common.view_models import (
    AdGroupStatus,
    SingleResponse,
    EntitiesRequest,
    KeywordBidModifiersRequest,
    KeywordsResponse,
    ListResponse,
    Entity,
    AuthRole)
from app.common.model.shared import BudgetType, PublishStatus, KeywordsMeta, EntityMeta, Warnings, Meta, Page
from app.common.model.targets import Target
from app.v2.controllers import (
    create_ad_group,
    get_ad_groups_by_campaign,
    get_ad_group_by_id,
    update_ad_group,
    update_ad_group_entities,
    update_ad_group_keyword_bid_modifiers,
    get_ad_group_eligible_keywords)
from app.v2.view_models import AdGroupRequest, AdGroupUpdateRequest
from app.v2.view_models.ad_group import AdGroupV2


class TestAdGroupV2(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_ad_group_service = AsyncMock()
        self.current_user = {"username": "test_user",
                        "is_agency": True,
                        "internal": True,
                        "works_for": {"clientId": "3b5c15a3-008e-4591-82be-26e06b913733"}}

        self.mock_keywords = ["1", "2", "3"]
        self.mock_ad_groups = AdGroupV2(
                    adGroupId=1,
                    campaignId=123,
                    name='Mock Item',
                    startDate='2025-01-01',
                    endDate='2025-05-05',
                    budgetType=BudgetType.DAILY,
                    budgetAmount=1000.0,
                    status='DRAFT',
                    baseBid=2.25,
                    entities=[Entity(id=255,useBaseBid=False,bidAmount= 1.5, deleted= False)],
                    targets=[
                        Target(type= "1", id=1, values=None),
                        Target(type= "2", id=1, values=None)],
                    keywordBidModifiers=[],
                    isArchived=False)

        self.mock_meta_single_response = EntityMeta(
            success=True,
            publishStatus=PublishStatus.PENDING,
            warnings=Warnings(validation=[]),
            errors=[]
        )

        self.mock_meta_list_response = Meta(page=Page(hasMore=False))

        mock_keywords = ["1", "2", "3"]

        self.mock_meta_keywords = KeywordsMeta(
            size=len(mock_keywords),
            message=None
        )
        self.mock_harness_service = MagicMock()
        self.mock_harness_service.is_harness_flag_on.return_value = True

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_create_ad_group(self, get_user_roles):
        # Arrange
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        request = AdGroupRequest(
            campaignId=1234, startDate='2025-01-01', endDate=None, status=AdGroupStatus.DRAFT, entities=[], targets=[])

        expected_response = SingleResponse[AdGroupV2](
            data=self.mock_ad_groups,
            meta=self.mock_meta_single_response
        )
        await create_ad_group(
            ad_group_request=request,
            ad_group_service=self.mock_ad_group_service
        )

        self.mock_ad_group_service.create_ad_group.assert_called_once()

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_get_ad_group_by_campaign(self, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        # Arrange
        campaign_id = 123
        expected_response = ListResponse[AdGroupV2](
            data=[self.mock_ad_groups],
            meta=self.mock_meta_list_response
        )
        self.mock_ad_group_service.get_ad_groups_by_campaign_id.return_value = expected_response
    
        #Act
        response = await get_ad_groups_by_campaign(
            campaign_id,
            include_ad_group_errors=False,
            ad_group_service=self.mock_ad_group_service,
            harness_service=self.mock_harness_service
        )
    
        self.assertEqual(expected_response.data, response.data)
        self.assertFalse(response.meta.page.hasMore)
        self.mock_ad_group_service.get_ad_groups_by_campaign_id.assert_called_with(
            campaign_id,
            include_ad_group_errors=False
        )

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_get_ad_group_by_campaign_can_include_errors(self, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        # Arrange
        campaign_id = 123
        expected_response = ListResponse[AdGroupV2](
            data=[self.mock_ad_groups],
            meta=self.mock_meta_list_response,
            errors=[],
            warnings=[]
        )
        self.mock_ad_group_service.get_ad_groups_by_campaign_id.return_value = expected_response

        # Act
        response = await get_ad_groups_by_campaign(
            campaign_id,
            include_ad_group_errors=True,
            ad_group_service=self.mock_ad_group_service,
            harness_service=self.mock_harness_service
        )

        self.assertEqual(expected_response.data, response.data)
        self.assertFalse(response.meta.page.hasMore)
        self.mock_ad_group_service.get_ad_groups_by_campaign_id.assert_called_with(
            campaign_id,
            include_ad_group_errors=True
        )

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    @patch('app.common.utils.jwt.validate_user')
    async def test_get_ad_group_by_id(self, mock_validate_user, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        # Arrange
        ad_group_id = 1

        expected_response = SingleResponse[AdGroupV2](
            data=self.mock_ad_groups,
            meta=self.mock_meta_single_response
        )

        self.mock_ad_group_service.get_ad_group_by_id.return_value = expected_response
    
        # Act
        response = await get_ad_group_by_id(ad_group_id, self.mock_ad_group_service)
    
        # Assert
        self.assertEqual(expected_response, response)
        self.assertTrue(response.meta.success)
        self.mock_ad_group_service.get_ad_group_by_id.assert_called_with(ad_group_id)

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    @patch('app.common.utils.jwt.validate_user')
    async def test_update_ad_group(self, mock_validate_user, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        # Arrange
        ad_group_id = 1
        adgroup_request = AdGroupUpdateRequest()
        expected_response = MagicMock(spec=SingleResponse[AdGroupV2])
        mock_validate_user.return_value = self.current_user
        self.mock_ad_group_service.update_ad_group.return_value = expected_response
    
        #Act
        response= await update_ad_group(
            ad_group_id,
            adgroup_request,
            self.current_user,
            self.mock_ad_group_service
        )
    
        # Assert
        self.assertEqual(expected_response, response)

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_update_ad_group_entities(self,get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        ad_group_id = 1
        entities_request = EntitiesRequest(entities=[])
        mock_response = MagicMock(spec=SingleResponse[AdGroupV2])
        self.mock_ad_group_service.update_entities.return_value = mock_response

        response = await update_ad_group_entities(
            ad_group_id,
            entities_request,
            self.mock_ad_group_service
        )

        self.assertEqual(mock_response, response)
        self.mock_ad_group_service.update_entities.assert_called_with(
            ad_group_id,
            entities_request
        )

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    @patch('app.common.utils.jwt.validate_user')
    async def test_update_ad_group_keyword_bid_modifiers(self, mock_validate_user, get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        # Arrange
        ad_group_id = 1
        keyword_bid_modifiers_request = KeywordBidModifiersRequest(keywordBidModifiers=[])

        expected_response = SingleResponse[AdGroupV2](
            data=self.mock_ad_groups,
            meta=self.mock_meta_single_response
        )
        self.mock_ad_group_service.update_ad_group_keyword_bid_modifiers.return_value = expected_response
    
        #Act
        response = await update_ad_group_keyword_bid_modifiers(
            ad_group_id,
            keyword_bid_modifiers_request,
            self.mock_ad_group_service
        )
    
        # Assert
        self.assertEqual(expected_response.model_dump(exclude_none=True, exclude_unset=True), response.model_dump(exclude_none=True, exclude_unset=True))
        self.assertTrue(response.meta.success)

    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    @patch('app.common.utils.jwt.validate_user')
    async def test_get_ad_group_eligible_keywords(self, mock_validate_user,get_user_roles):
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]
        # Arrange
        ad_group_id = 1
        expected_response = KeywordsResponse(
            data=self.mock_keywords,
            meta=self.mock_meta_keywords
        )
        self.mock_ad_group_service.get_keywords_by_ad_group_id.return_value = expected_response
    
        #Act
        response = await get_ad_group_eligible_keywords(
            ad_group_id,
            self.mock_ad_group_service
        )
    
        # Assert
        self.assertEqual(expected_response, response)
        self.assertEqual(response.meta.message, None)
        self.mock_ad_group_service.get_keywords_by_ad_group_id.assert_called_with(ad_group_id)
