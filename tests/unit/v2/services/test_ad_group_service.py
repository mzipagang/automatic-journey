from typing import List
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, call, patch

from fastapi import HTTPException

from app.common.view_models import (
    EntitiesRequest,
    KeywordsResponse,
    SingleResponse,
    AdGroupStatus,
    KeywordBidModifiersRequest,
    KeywordBidModifier, Entity,
)
from app.v2.model.downstream.activation_service import ChannelConfig, ActivationPayload, ChannelData, ActivationMetaData
from app.common.model.campaign_types import InternalCampaignType
from app.common.model.placement import PlacementType
from app.common.model.shared import UpstreamValidationWarning, BudgetType
from app.common.model.targets import Target, TargetTypeId, TargetAdgroupRequest
from app.common.utils.bid_manager_errors import NO_KEYWORDS_FOUND
from app.v2.view_models import Campaign as CampaignV2, AdGroupFromActivation
from app.v2.view_models.ad_group import AdGroupV2, AdGroupUpdateRequestV2
from app.v2.model.downstream.activation_service import ActivationResponseV2, ActivationResponse, EditableField, \
    ActivationStatus, ActivationUpdatePayload
from app.common.model.downstream.bid_manager import ValidateBidRequest, BidEntityFailure
from app.common.model.shared import Warnings, PublishStatus, EntityMeta
from app.v2.services.ad_group_service import AdGroupService, PatchAction
from app.v2.view_models import AdGroupV2Request
from tests.unit.services.constants import SIMPLE_ACTIVATION_JSON


class TestAdGroupServiceV2(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_lookup = AsyncMock()
        self.mock_activation_gateway = AsyncMock()
        self.mock_ad_group_translation = AsyncMock()
        self.mock_bid_manager_service = AsyncMock()
        self.mock_keyword_service = AsyncMock()
        self.mock_campaign_gateway = AsyncMock()
        self.mock_placement_service = AsyncMock()
        self.mock_campaign_service = AsyncMock()
        self.mock_division_service = AsyncMock()
        self.mock_target_translation = AsyncMock()
        self.mock_bid_manager_service.validate_bid = AsyncMock(return_value=[])
        self.mock_bid_manager_service.build_validation_request = MagicMock()

        self.ad_group_service = AdGroupService(
            lookup=self.mock_lookup,
            activation_gateway=self.mock_activation_gateway,
            ad_group_translation=self.mock_ad_group_translation,
            bid_manager_service=self.mock_bid_manager_service,
            keyword_service=self.mock_keyword_service,
            campaign_gateway=self.mock_campaign_gateway,
            placement_service=self.mock_placement_service,
            campaign_service=self.mock_campaign_service,
            division_service=self.mock_division_service,
            target_translation=self.mock_target_translation
        )

    def __mock_dependencies(self):
        ad_group_id = 1234
        activation_id = "activation_id"
        bid_group_id = "bid_group_id"
        entities_request = EntitiesRequest(entities=[])
        mock_activation_config = MagicMock()
        mock_activation_config.biddableEntities = EditableField(
            is_editable=True,
            min_bid_amount=0.1,
            max_bid_amount=50,
        )
        mock_activation = MagicMock(spec=ActivationResponseV2[ActivationResponse])
        mock_activation.data = MagicMock()
        mock_activation.data.id = activation_id
        mock_activation.included = MagicMock()
        mock_activation.included.configuration_by_activation = {
            activation_id: mock_activation_config
        }
        mock_activation.warnings = []
        mock_activation.errors = []
        mock_updated_activation = MagicMock()
        mock_updated_activation_response = MagicMock(spec=ActivationResponseV2[ActivationResponse])
        mock_updated_activation_response.data = mock_updated_activation
        mock_updated_activation_response.warnings = MagicMock()
        mock_updated_activation_response.errors = MagicMock()
        mock_ad_group = MagicMock(spec=AdGroupV2)
        mock_warnings = Warnings(validation=[])
        mock_errors = []
        mock_validation_request = MagicMock(spec=ValidateBidRequest)
        expected_response = SingleResponse[AdGroupV2](
            data=mock_ad_group,
            meta=EntityMeta(
                success=True,
                publishStatus=PublishStatus.PUBLISHED,
                warnings=mock_warnings,
                errors=mock_errors,
            )
        )
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = activation_id
        self.mock_activation_gateway.get_activation_by_id.return_value = mock_activation
        self.mock_bid_manager_service.update_entities.return_value = bid_group_id
        self.mock_activation_gateway.update_activation.return_value = mock_updated_activation_response
        self.mock_ad_group_translation.ad_group_from_activation.return_value = AdGroupFromActivation(
            adGroup=mock_ad_group,
            entityErrors=[]
        )
        self.mock_ad_group_translation.warnings_from_activation_warnings = MagicMock(return_value=mock_warnings)
        self.mock_ad_group_translation.publish_status_from_activation = MagicMock(return_value=PublishStatus.PUBLISHED)
        self.mock_ad_group_translation.validation_request_from_activation = MagicMock(
            return_value=mock_validation_request
        )

        return {
            "ad_group_id": ad_group_id,
            "activation_id": activation_id,
            "bid_group_id": bid_group_id,
            "entities_request": entities_request,
            "mock_activation": mock_activation,
            "mock_activation_config": mock_activation_config,
            "mock_updated_activation": mock_updated_activation,
            "mock_updated_activation_response": mock_updated_activation_response,
            "mock_ad_group": mock_ad_group,
            "mock_warnings": mock_warnings,
            "mock_validation_request": mock_validation_request,
            "expected_response": expected_response
        }

    @patch("logging.Logger.warning")
    async def test_get_ad_group_by_id__raises_error_if_activation_id_not_found(
            self,
            mock_logger_warning
    ):
        ad_group_id = 1234
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = None

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.get_ad_group_by_id(ad_group_id)

        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)
        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Ad group not found", context.exception.detail)
        mock_logger_warning.assert_called_once_with(
            "Activation not found for ad_group_id: %s",
            ad_group_id
        )

    async def test_get_ad_group_by_id__gets_activation_and_builds_ad_group(self):
        ad_group_id = 1234
        activation_id = "activation_id"
        mock_activation_response = MagicMock()
        mock_activation = MagicMock()
        mock_activation_response.data = mock_activation
        mock_activation_response.warnings = MagicMock()
        mock_activation_response.errors = MagicMock()
        mock_ad_group = MagicMock(spec=AdGroupV2)
        mock_warnings = Warnings(validation=[])
        expected_result = SingleResponse[AdGroupV2](
            data=mock_ad_group,
            meta=EntityMeta(
                success=True,
                publishStatus=PublishStatus.PUBLISHED,
                warnings=mock_warnings
            )
        )
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = activation_id
        self.mock_activation_gateway.get_activation_by_id.return_value = mock_activation_response
        self.mock_ad_group_translation.ad_group_from_activation.return_value = AdGroupFromActivation(
            adGroup=mock_ad_group,
            entityErrors=[]
        )
        self.mock_ad_group_translation.warnings_from_activation_warnings = MagicMock(return_value=mock_warnings)
        self.mock_ad_group_translation.publish_status_from_activation = MagicMock(return_value=PublishStatus.PUBLISHED)

        result = await self.ad_group_service.get_ad_group_by_id(ad_group_id)
        self.assertEqual(expected_result, result)
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)
        self.mock_activation_gateway.get_activation_by_id.assert_called_once_with(activation_id)
        self.mock_ad_group_translation.ad_group_from_activation.assert_called_once_with(mock_activation, [])
        self.mock_ad_group_translation.warnings_from_activation_warnings.assert_called_once_with(mock_activation_response.warnings)
        self.mock_ad_group_translation.publish_status_from_activation.assert_called_once_with(mock_activation)

    async def test_update_entities__raises_error_if_activation_not_found(self):
        mocks = self.__mock_dependencies()
        ad_group_id = mocks["ad_group_id"]
        entities_request = mocks["entities_request"]
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = None

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.update_entities(ad_group_id, entities_request)

        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Ad group not found", context.exception.detail)
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)

    async def test_update_entities__raises_error_if_activation_is_ended(self):
        mocks = self.__mock_dependencies()
        ad_group_id = mocks["ad_group_id"]
        activation_id = mocks["activation_id"]
        entities_request = mocks["entities_request"]
        mock_activation = mocks["mock_activation"]
        mock_activation.data.status = ActivationStatus.ENDED

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.update_entities(ad_group_id, entities_request)

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "Cannot update ad group with Ended status",
            context.exception.detail
        )
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)
        self.mock_activation_gateway.get_activation_by_id.assert_called_once_with(activation_id)

    async def test_update_entities__raises_error_if_bid_manager_raises_error(self):
        mocks = self.__mock_dependencies()
        ad_group_id = mocks["ad_group_id"]
        activation_id = mocks["activation_id"]
        entities_request = mocks["entities_request"]
        mock_activation = mocks["mock_activation"]
        self.mock_bid_manager_service.update_entities.side_effect = [
            HTTPException(
                status_code=422,
                detail="Invalid bid"
            )
        ]

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.update_entities(ad_group_id, entities_request)

        self.assertEqual(422, context.exception.status_code)
        self.assertEqual(
            "Invalid bid",
            context.exception.detail
        )
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)
        self.mock_activation_gateway.get_activation_by_id.assert_called_once_with(activation_id)
        self.mock_bid_manager_service.update_entities.assert_called_once_with(
            mock_activation,
            entities_request
        )

    async def test_update_entities__updates_activation_with_empty_biddable_entities_if_bid_group_id_is_none(self):
        mocks = self.__mock_dependencies()
        ad_group_id = mocks["ad_group_id"]
        activation_id = mocks["activation_id"]
        entities_request = mocks["entities_request"]
        expected_response = mocks["expected_response"]
        mock_activation = mocks["mock_activation"]
        self.mock_bid_manager_service.update_entities.return_value = None

        response = await self.ad_group_service.update_entities(ad_group_id, entities_request)

        self.assertEqual(expected_response, response)
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)
        self.mock_activation_gateway.get_activation_by_id.assert_called_once_with(activation_id)
        self.mock_bid_manager_service.update_entities.assert_called_once_with(
            mock_activation,
            entities_request
        )
        self.mock_activation_gateway.update_activation.assert_called_once_with(
            ActivationUpdatePayload(**{"channel_data": {"biddableEntities": []}}),
            activation_id
        )

    async def test_update_entities__creates_and_validates_bid_group(self):
        mocks = self.__mock_dependencies()
        ad_group_id = mocks["ad_group_id"]
        activation_id = mocks["activation_id"]
        bid_group_id = mocks["bid_group_id"]
        entities_request = mocks["entities_request"]
        mock_activation = mocks["mock_activation"]
        mock_validation_request = mocks["mock_validation_request"]

        self.mock_bid_manager_service.update_entities.return_value = bid_group_id
        self.mock_bid_manager_service.validate_bid = AsyncMock(return_value=[BidEntityFailure(field="UPC", message="Invalid UPC", entity_id="entity1")])



        result = await self.ad_group_service.update_entities(ad_group_id, entities_request)
        self.assertEqual(result.meta.errors, [{
                "field": "UPC",
                "message": "Invalid UPC",
                "entity_id": "entity1"
        }])
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)
        self.mock_activation_gateway.get_activation_by_id.assert_called_once_with(activation_id)
        self.mock_bid_manager_service.update_entities.assert_called_once_with(
            mock_activation,
            entities_request
        )
        self.mock_bid_manager_service.validate_bid.assert_called_once_with(
            bid_group_id,
            mock_validation_request
        )

        self.mock_bid_manager_service.validate_bid = AsyncMock(return_value=[])
        self.mock_activation_gateway.update_activation.assert_called_once()

    async def test_get_ad_groups_by_campaign_id__raises_error_if_campaign_id_is_none(self):
        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.get_ad_groups_by_campaign_id(None)

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual("Campaign ID is required", context.exception.detail)

    async def test_get_ad_groups_by_campaign_id__raises_error_if_translation_raises_error(self):
        campaign_id = 1234
        mock_activations_response = MagicMock(spec=ActivationResponseV2[List[ActivationResponse]])
        mock_activation = MagicMock(ActivationResponse)
        mock_activation.id = "234567"
        mock_activation.metadata = MagicMock(ActivationMetaData)
        mock_activation.metadata.short_id = "456"
        mock_activations_response.data = [mock_activation]
        self.mock_campaign_service.get_campaign_long_id.return_value = "campaign_id"
        self.mock_activation_gateway.get_activations.return_value = mock_activations_response
        self.mock_ad_group_translation.ad_group_from_activation.side_effect = [
            HTTPException(status_code=503, detail="Temporary service error. Please try again.")
        ]

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.get_ad_groups_by_campaign_id(campaign_id)

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("Temporary service error. Please try again.", context.exception.detail)
        self.mock_ad_group_translation.ad_group_from_activation.assert_called_once_with(mock_activation)

    async def test_get_ad_groups_by_campaign_id__converts_found_activations_to_ad_group_list_response(self):
        campaign_id = 1234
        mock_activations_response = MagicMock(spec=ActivationResponseV2[List[ActivationResponse]])
        mock_activation_1 = MagicMock(ActivationResponse)
        mock_activation_2 = MagicMock(ActivationResponse)
        mock_activation_1.id = "234567"
        mock_activation_2.id = "345678"
        mock_activation_1.metadata = MagicMock(ActivationMetaData)
        mock_activation_2.metadata = MagicMock(ActivationMetaData)
        mock_activation_1.metadata.short_id = "234"
        mock_activation_2.metadata.short_id = "456"
        mock_activations_response.data = [mock_activation_1, mock_activation_2]
        mock_ad_group_1 = AdGroupFromActivation(adGroup=MagicMock(spec=AdGroupV2), entityErrors=[])
        mock_ad_group_2 = AdGroupFromActivation(adGroup=MagicMock(spec=AdGroupV2), entityErrors=[])
        self.mock_campaign_service.get_campaign_long_id.return_value = "campaign_id"
        self.mock_activation_gateway.get_activations.return_value = mock_activations_response
        self.mock_ad_group_translation.ad_group_from_activation.side_effect = [
            mock_ad_group_1,
            mock_ad_group_2
        ]

        response = await self.ad_group_service.get_ad_groups_by_campaign_id(campaign_id)

        self.mock_ad_group_translation.ad_group_from_activation.assert_has_calls([
            call(mock_activation_1),
            call(mock_activation_2)
        ])

        self.assertEqual(mock_ad_group_1.adGroup, response.data[0])
        self.assertEqual(mock_ad_group_2.adGroup, response.data[1])
        self.assertEqual(0, response.meta.page.offset)
        self.assertEqual(2, response.meta.page.size)
        self.assertEqual(False, response.meta.page.hasMore)

    async def test_create_carousel_ad_group__should_succeed(self):
        await self.__create_ad_group_assertions(
            ad_group_request=MagicMock(
                spec=AdGroupV2Request,
                name="Test Adgroup",
                carouselHeadline='headline',
                campaignId=123,
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[TargetAdgroupRequest(type=1, values=[1, 2])]
            ),
            campaign_type=InternalCampaignType.CAROUSEL)

    async def test_create_pla_ad_group_should_succeed(self):
        await self.__create_ad_group_assertions(
            ad_group_request=MagicMock(
                spec=AdGroupV2Request,
                name="Test Adgroup",
                campaignId=123,
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[TargetAdgroupRequest(type=1, values=[1, 2])]
            ),
            campaign_type=InternalCampaignType.PLA)

    async def test_create_ad_group__not_campaign_id_found(self):
        with self.assertRaises(HTTPException) as context:
            await self.__create_ad_group_assertions(
                ad_group_request=MagicMock(
                    spec=AdGroupV2Request,
                    name="Test Adgroup",
                    campaignId="mock_not_found",
                    startDate="2024-05-20",
                    endDate="2024-06-20",
                    budgetAmount=250,
                    status=AdGroupStatus.DRAFT,
                    baseBid=2.50,
                    entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                    targets=[TargetAdgroupRequest(type=1, values=[1, 2])]
                ),
                campaign_type=InternalCampaignType.PLA,
                raise_exception=True
            )

    @patch("app.v2.services.ad_group_service.AdGroupRequestValidator.validate_ad_group_request_single_call",
           return_value=([], [], []))
    @patch("app.v2.services.ad_group_service.AdGroupService.get_ad_group_by_id",
           return_value=AsyncMock(spec=SingleResponse[AdGroupV2])
    )
    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__approve_and_publish_ad_group")
    @patch("app.v2.services.ad_group_service.AdGroupRequestValidator.validate_ad_group_targets")
    async def __create_ad_group_assertions(
            self,
            mock_validate_ad_group_targets: MagicMock,
            mock_approve_and_publish_ad_group: AsyncMock,
            mock_get_ad_group_by_id: AsyncMock,
            mock_validate_ad_group_request_single_call: MagicMock,
            ad_group_request: AdGroupV2Request,
            campaign_type: InternalCampaignType,
            raise_exception: bool = False
    ):
        campaign_long_id: str = "internal_campaign_id"
        campaign_short_id: int = ad_group_request.campaignId
        campaign: CampaignV2 = MagicMock(
            spec=CampaignV2,
            id=campaign_long_id,
            campaignType=campaign_type,
            budgetType=BudgetType.DAILY
        )
        campaign.advertiserIds = [123]
        mock_get_ad_group_by_id.return_value = SingleResponse[AdGroupV2](
            data=AdGroupV2(
                adGroupId=456,
                campaignId=123,
                name="Test Adgroup",
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[Target(type="1", values=[1, 2])],
                keywordBidModifiers=[],
                isArchived=False,
                carouselHeadline="headline"
            ),
            meta=EntityMeta(
                success=True,
                publishStatus=PublishStatus.PUBLISHED,
                warnings=None,
                errors=[],
                message=None,
                code=None
            )
        )
        self.ad_group_service.target_translation.fetch_ad_group_targets = MagicMock(return_value=([], [], []))
        self.ad_group_service.ad_group_translation.build_activation_payload = MagicMock()
        activation_id = 4321
        self.mock_campaign_service.get_campaign_by_id.return_value =\
            campaign, MagicMock(spec=PublishStatus)
        self.mock_campaign_service.get_internal_campaign_id.return_value = campaign_long_id

        self.mock_campaign_service.get_campaign_single_response_by_id.return_value = SingleResponse[CampaignV2](
            data=campaign,
            meta=EntityMeta(success=True))

        if raise_exception:
            self.mock_lookup.get_campaign_long_id_by_internal_short_id.return_value = None
        else:
            self.mock_lookup.get_campaign_long_id_by_internal_short_id.return_value = campaign_long_id
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = None
        self.mock_lookup.get_adgroup_short_id_by_long_id.return_value = None
        (await self.mock_activation_gateway.create_activation()).data.id = activation_id
        (await self.mock_activation_gateway.create_activation()).data.metadata.short_id = 456

        # Act
        await self.ad_group_service.create_ad_group(ad_group_request=ad_group_request)

        # Assert
        self.mock_campaign_service.get_campaign_single_response_by_id.assert_called_once_with(campaign_short_id)
        self.mock_lookup.get_campaign_long_id_by_internal_short_id.assert_called_once_with(campaign_short_id)
        self.ad_group_service.ad_group_translation.build_activation_payload.assert_called_once()
        mock_get_ad_group_by_id.assert_called_once()
        mock_validate_ad_group_request_single_call.assert_called_once()

    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__get_activation_by_ad_group_id")
    async def test_get_keywords_by_ad_group_id__raises_error_if_campign_is_not_PLA(self, mock_get_activation_by_ad_group_id):
        ad_group_id = 1234
        activation_id = "activation_id"
        mock_activation = MagicMock(spec=ActivationResponseV2[ActivationResponse])
        mock_activation.data = MagicMock()
        mock_activation.data.channel_data["biddableEntities"] = ["test_bid_group_id"]
        mock_activation.data.channel_config = ChannelConfig(type="test_type", version="1.0")
        mock_activation.data.id = activation_id
        mock_activation.included = MagicMock()
        self.mock_ad_group_translation.get_campaign_type.return_value = InternalCampaignType.CAROUSEL
        mock_get_activation_by_ad_group_id.return_value = mock_activation

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.get_keywords_by_ad_group_id(ad_group_id)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Ad group must be in PLA type campaign to have keyword bids")
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        mock_get_activation_by_ad_group_id.assert_awaited()
        mock_get_activation_by_ad_group_id.assert_called_once_with(ad_group_id)


    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__get_activation_by_ad_group_id")
    async def test_get_keywords_by_ad_group_id__success(self, mock_get_activation_by_ad_group_id):
        ad_group_id = 1234
        activation_id = "activation_id"
        mock_activation_config = MagicMock()
        mock_activation_config.biddableEntities = EditableField(
            is_editable=True,
            min_bid_amount=0.1,
            max_bid_amount=50,
        )
        mock_activation = MagicMock(spec=ActivationResponseV2[ActivationResponse])
        mock_activation.data = MagicMock()
        mock_activation.data.channel_data["biddableEntities"] = ["test_bid_group_id"]
        mock_activation.data.channel_config = ChannelConfig(type="test_type", version="1.0")
        mock_activation.data.id = activation_id
        mock_activation.included = MagicMock()
        mock_activation.included.configuration_by_activation = {
            activation_id: mock_activation_config
        }
        self.mock_ad_group_translation.get_campaign_type = MagicMock()
        self.mock_ad_group_translation.get_campaign_type.return_value = InternalCampaignType.PLA
        mock_get_activation_by_ad_group_id.return_value = mock_activation

        self.mock_activation_gateway.get_activation_by_id.return_value = mock_activation


        self.mock_bid_manager_service.get_upcs_by_bid_group_id.return_value = ["entity1", "entity2"]
        self.mock_keyword_service.get_eligible_keywords_from_upcs.return_value = ["keyword1", "keyword2"]

        # Act
        result = await self.ad_group_service.get_keywords_by_ad_group_id(ad_group_id)

        # Assert
        self.assertIsInstance(result, KeywordsResponse)
        self.assertEqual(result.data, ["keyword1", "keyword2"])
        self.assertEqual(result.meta.size, 2)
        self.assertIsNone(result.meta.message)
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        mock_get_activation_by_ad_group_id.assert_awaited()
        mock_get_activation_by_ad_group_id.assert_called_once_with(ad_group_id)

    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__get_activation_by_ad_group_id")
    async def test_get_keywords_by_ad_group_id__no_keywords_found(self, mock_get_activation_by_ad_group_id):
        ad_group_id = 1234
        activation_id = "activation_id"
        mock_activation_config = MagicMock()
        mock_activation_config.biddableEntities = EditableField(
            is_editable=True,
            min_bid_amount=0.1,
            max_bid_amount=50,
        )
        mock_activation = MagicMock(spec=ActivationResponseV2[ActivationResponse])
        mock_activation.data = MagicMock()
        mock_activation.data.channel_data["biddableEntities"] = ["test_bid_group_id"]
        mock_activation.data.channel_config = ChannelConfig(type="test_type", version="1.0")
        mock_activation.data.id = activation_id
        mock_activation.included = MagicMock()
        self.mock_ad_group_translation.get_campaign_type = MagicMock()
        self.mock_ad_group_translation.get_campaign_type.return_value = InternalCampaignType.PLA
        mock_get_activation_by_ad_group_id.return_value = mock_activation
        mock_activation.included.configuration_by_activation = {
            activation_id: mock_activation_config
        }

        self.mock_activation_gateway.get_activation_by_id.return_value = mock_activation


        self.mock_bid_manager_service.get_upcs_by_bid_group_id.return_value = []
        self.mock_keyword_service.get_eligible_keywords_from_upcs.return_value = []

        # Act
        result = await self.ad_group_service.get_keywords_by_ad_group_id(ad_group_id)

        # Assert
        self.assertIsInstance(result, KeywordsResponse)
        self.assertEqual(result.data, [])
        self.assertEqual(result.meta.size, 0)
        self.assertEqual(result.meta.message, NO_KEYWORDS_FOUND)
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        mock_get_activation_by_ad_group_id.assert_awaited()
        mock_get_activation_by_ad_group_id.assert_called_once_with(ad_group_id)

    async def test_get_keywords_by_ad_group_id__activation_not_found(self):
        ad_group_id = 123
        self.mock_activation_gateway.get_activation_by_id.side_effect = [HTTPException(status_code=404, detail="Ad group not found")]

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.get_keywords_by_ad_group_id(ad_group_id)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Ad group not found")

    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__get_activation_by_ad_group_id")
    async def test_get_keywords_by_ad_group_id__bid_manager_error(
            self,
            mock_get_activation_by_ad_group_id,
    ):
        # Arrange
        ad_group_id = 1234
        mock_activation = ActivationResponseV2[ActivationResponse](**SIMPLE_ACTIVATION_JSON)
        mock_get_activation_by_ad_group_id.return_value = mock_activation
        self.mock_ad_group_translation.get_campaign_type = MagicMock()
        self.mock_ad_group_translation.get_campaign_type.return_value = InternalCampaignType.PLA
        self.mock_bid_manager_service.get_upcs_by_bid_group_id.side_effect = Exception("Bid Manager Error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            await self.ad_group_service.get_keywords_by_ad_group_id(ad_group_id)

        self.assertEqual(str(context.exception), "Bid Manager Error")
        self.mock_bid_manager_service.get_upcs_by_bid_group_id.assert_called_once_with(
            mock_activation.data.channel_data["biddableEntities"], mock_activation.data.channel_config.type
        )
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        self.mock_ad_group_translation.get_campaign_type.assert_called_once()
        mock_get_activation_by_ad_group_id.assert_awaited()
        mock_get_activation_by_ad_group_id.assert_called_once_with(ad_group_id)

    async def test_get_campaign_by_ad_group_id__gets_and_caches_long_id_if_not_cached(self):
        ad_group_id = 1234
        activation_id = "activation_id"
        long_campaign_id = "long_id"
        short_campaign_id = 4321
        mock_activation = MagicMock(spec=ActivationResponseV2[ActivationResponse])
        mock_activation.data = MagicMock(spec=ActivationResponse)
        mock_activation.data.campaign_id = long_campaign_id
        mock_campaign = MagicMock(spec=CampaignV2)
        mock_campaign_response = MagicMock(spec=SingleResponse[CampaignV2], data=mock_campaign)
        self.mock_lookup.get_campaign_long_id_by_short_adgroup_id.return_value = None
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = activation_id
        self.mock_lookup.get_campaign_short_id_by_long_id.return_value = short_campaign_id
        self.mock_activation_gateway.get_activation_by_id.return_value = mock_activation
        self.mock_campaign_service.get_campaign_single_response_by_id.return_value = mock_campaign_response

        result = await self.ad_group_service.get_campaign_by_ad_group_id(ad_group_id)

        self.assertEqual(mock_campaign_response.data, result)
        self.mock_lookup.get_campaign_long_id_by_short_adgroup_id.assert_called_once_with(ad_group_id)
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(ad_group_id)
        self.mock_lookup.get_campaign_short_id_by_long_id.assert_called_once_with(long_campaign_id)
        self.mock_lookup.set_campaign_long_id_by_short_adgroup_id.assert_called_once_with(ad_group_id, long_campaign_id)
        self.mock_activation_gateway.get_activation_by_id.assert_called_once_with(activation_id)
        self.mock_campaign_service.get_campaign_single_response_by_id.assert_called_once_with(short_campaign_id)

    async def test_validate_keywords_updatable__raises_if_campaign_type_is_not_pla(self):
        ad_group_response = MagicMock()

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.validate_keywords_updatable(
                ad_group_response,
                InternalCampaignType.CAROUSEL
            )

        self.assertIsNotNone(context)
        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "Ad group must be in PLA type campaign to have keyword bids",
            context.exception.detail
        )

    async def test_validate_keywords_updatable__raises_for_ended_ad_group(self):
        ad_group_response = MagicMock()
        ad_group_response.data = MagicMock()
        ad_group_response.data.status = AdGroupStatus.ENDED

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.validate_keywords_updatable(ad_group_response)

        self.assertIsNotNone(context)
        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "Cannot update/get keywords ad group with ENDED status",
            context.exception.detail
        )

    async def test_validate_keywords_updatable__raises_for_ad_group_without_targets(self):
        ad_group_response = MagicMock()
        ad_group_response.data = MagicMock()
        ad_group_response.data.status = AdGroupStatus.DRAFT
        ad_group_response.data.targets = []

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.validate_keywords_updatable(ad_group_response)

        self.assertIsNotNone(context)
        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "Must have Search and Browse Placement to add keyword modifiers",
            context.exception.detail
        )

    async def test_validate_keywords_updatable__raises_for_ad_group_without_proper_target(self):
        ad_group_response = MagicMock()
        ad_group_response.data = MagicMock()
        ad_group_response.data.status = AdGroupStatus.DRAFT
        ad_group_response.data.targets = [
            Target(
                type=str(TargetTypeId.DIVISION.value),
                id=1
            ),
            Target(
                type=str(TargetTypeId.PLACEMENT.value),
                id=2
            )
        ]
        self.mock_placement_service.get_cache_placement.return_value = {
            "name": PlacementType.BASKET_BUILDER.value
        }

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.validate_keywords_updatable(ad_group_response)

        self.assertIsNotNone(context)
        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "Must have Search and Browse Placement to add keyword modifiers",
            context.exception.detail
        )

    async def test_validate_keywords_updatable__returns_true_for_ad_group_with_proper_target(self):
        ad_group_response = MagicMock()
        ad_group_response.data = MagicMock()
        ad_group_response.data.status = AdGroupStatus.DRAFT
        ad_group_response.data.targets = [
            Target(
                type=str(TargetTypeId.PLACEMENT.value),
                id=1
            )
        ]
        self.mock_placement_service.get_cache_placement.return_value = {
            "name": PlacementType.SEARCH_AND_BROWSE.value
        }

        result = await self.ad_group_service.validate_keywords_updatable(ad_group_response)

        self.assertTrue(result)

    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__activation_to_single_ad_group_response")
    async def test_update_ad_group_keyword_bid_modifiers__updates_ad_group_with_new_keywords(
            self,
            mock_activation_to_single_ad_group_response
    ):
        mocks = self.__mock_dependencies()
        ad_group_id = mocks["ad_group_id"]
        ad_group = mocks["mock_ad_group"]
        keywords = KeywordBidModifiersRequest(
            keywordBidModifiers=[
                KeywordBidModifier(keyword="random keyword", modifier=0.1, deleted=False)
            ]
        )
        ad_group.status = AdGroupStatus.DRAFT
        ad_group.targets = [
            Target(
                type=str(TargetTypeId.PLACEMENT.value),
                id=1
            )
        ]
        bid_group_id = "bid_group_id"
        mock_warnings = [UpstreamValidationWarning(
            detail=['"random keyword" is not an allowed keyword, ignoring this keyword'],
            path="data.keywordBidModifiers"
        )]
        self.mock_placement_service.get_cache_placement.return_value = {
            "name": PlacementType.SEARCH_AND_BROWSE.value
        }
        self.mock_keyword_service.update_keywords = AsyncMock(return_value=(
            bid_group_id,
            mock_warnings
        ))
        self.mock_ad_group_translation.get_campaign_type = MagicMock(return_value=InternalCampaignType.PLA)
        mock_activation_to_single_ad_group_response.side_effect = [
            MagicMock(
                spec=SingleResponse[AdGroupV2],
                data=MagicMock(
                    id=123,
                    targets=[
                        Target(type=str(TargetTypeId.PLACEMENT.value), id=1)
                    ]
                )
            ),
            MagicMock(
                meta = MagicMock(warnings=MagicMock(validation=mock_warnings))
            )
        ]
        response = await self.ad_group_service.update_ad_group_keyword_bid_modifiers(
            ad_group_id,
            keywords
        )

        self.assertEqual(mock_warnings, response.meta.warnings.validation)
        self.assertEqual(PublishStatus.PUBLISHED, response.meta.publishStatus)

    async def test__apply_triggered_action_APPROVE_success(self):
        mock_updated_activation_response = ActivationResponseV2(
            data=MagicMock(spec=ActivationResponse),
            warnings=None,
            errors=None,
        )
        internal_activation_id = "activation_id"
        action = PatchAction.APPROVE

        await self.ad_group_service._AdGroupService__apply_triggered_action(
            mock_updated_activation_response,
            internal_activation_id,
            action
        )
        self.mock_activation_gateway.approve_activation.assert_called_once()

    async def test__apply_triggered_action_APPROVE_not_calling_gateway(self):
        mock_updated_activation_response = MagicMock(spec=ActivationResponseV2(
            data=MagicMock(spec=ActivationResponse),
            warnings=[],
            errors=[],
        ))
        internal_activation_id = "activation_id"
        action = PatchAction.APPROVE

        response = await self.ad_group_service._AdGroupService__apply_triggered_action(
            mock_updated_activation_response,
            internal_activation_id,
            action
        )
        self.assertIsNotNone(response)

    async def test__apply_triggered_action_PAUSE_success(self):
        mock_updated_activation_response = ActivationResponseV2(
            data=MagicMock(spec=ActivationResponse),
            warnings=None,
            errors=None,
        )
        internal_activation_id = "activation_id"
        action = PatchAction.PAUSE

        await self.ad_group_service._AdGroupService__apply_triggered_action(
            mock_updated_activation_response,
            internal_activation_id,
            action
        )
        self.mock_activation_gateway.pause_activation.assert_called_once()

    async def test__apply_triggered_action_UNPAUSE_success(self):
        mock_updated_activation_response = ActivationResponseV2(
            data=MagicMock(spec=ActivationResponse),
            warnings=None,
            errors=None,
        )
        internal_activation_id = "activation_id"
        action = PatchAction.UNPAUSE

        await self.ad_group_service._AdGroupService__apply_triggered_action(
            mock_updated_activation_response,
            internal_activation_id,
            action
        )
        self.mock_activation_gateway.unpause_activation.assert_called_once()

    async def test__apply_triggered_action_error(self):
        self.mock_activation_gateway.test_action_activation = None
        mock_updated_activation_response = ActivationResponseV2(
            data=MagicMock(spec=ActivationResponse),
            warnings=None,
            errors=None,
        )
        internal_activation_id = "activation_id"
        action = MagicMock(value="test_action")
        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service._AdGroupService__apply_triggered_action(
                mock_updated_activation_response,
                internal_activation_id,
                action
            )
        self.assertEqual("Unsupported action: test_action", context.exception.detail)

    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__publish_activation_if_publishable")
    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__apply_triggered_action")
    async def test_approve_and_publish_ad_group_valid_action(
            self,
            mock_apply_triggered_action,
            mock_publish_activation_if_publishable
    ):
        ad_group_request_status = AdGroupStatus.ACTIVE
        activation = MagicMock()
        long_activation_id = "test_id"

        await self.ad_group_service._AdGroupService__approve_and_publish_ad_group(
            ad_group_request_status,
            activation,
            long_activation_id
        )

        mock_apply_triggered_action.assert_called_once_with(activation, long_activation_id, PatchAction.APPROVE)
        mock_publish_activation_if_publishable.assert_called_once()

    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__publish_activation_if_publishable")
    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__apply_triggered_action")
    async def test_approve_and_publish_ad_group_special_action(
            self,
            mock_apply_triggered_action,
            mock_publish_activation_if_publishable
    ):
        ad_group_request_status = AdGroupStatus.ACTIVE
        activation = MagicMock()
        activation.data.status = ActivationStatus.PAUSED
        long_activation_id = "test_id"

        await self.ad_group_service._AdGroupService__approve_and_publish_ad_group(
            ad_group_request_status,
            activation,
            long_activation_id
        )

        mock_apply_triggered_action.assert_called_once_with(activation, long_activation_id, PatchAction.UNPAUSE)
        mock_publish_activation_if_publishable.assert_called_once()

    async def test_approve_and_publish_ad_group_no_action(
            self,
    ):
        ad_group_request_status = AdGroupStatus.FAILED
        activation = MagicMock()
        activation.data.status = ActivationStatus.PAUSED
        long_activation_id = "test_id"

        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service._AdGroupService__approve_and_publish_ad_group(
                ad_group_request_status,
                activation,
                long_activation_id
            )

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "Unsupported ad group status: FAILED",
            context.exception.detail
        )

    async def test_update_ad_group_not_activation_id(self):
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = None
        with self.assertRaises(HTTPException) as context:
            await self.ad_group_service.update_ad_group(123, AdGroupUpdateRequestV2())
        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Ad group not found", context.exception.detail)

    @patch("app.v2.services.ad_group_service.AdGroupService.get_ad_group_by_id")
    @patch("app.v2.services.ad_group_service.AdGroupService.get_campaign_by_ad_group_id")
    async def test_update_ad_group_not_secret_ad_group_not_changes(
            self,
            mock_get_campaign_by_ad_group_id: AsyncMock,
            mock_get_ad_group_by_id: AsyncMock
    ):
        ad_group_response = SingleResponse[AdGroupV2](
            data= AdGroupV2(
                adGroupId=123,
                campaignId=123,
                name="Test Adgroup",
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[Target(type="1", id=1)],
                keywordBidModifiers=[],
                isArchived=False,
                carouselHeadline=None
            ),
            meta=EntityMeta(
                success=True,
                publishStatus=PublishStatus.PUBLISHED,
                warnings=None,
                errors=[],
                message=None,
                code=None
            )

        )
        mock_get_ad_group_by_id.return_value = ad_group_response
        ad_group_request = AdGroupUpdateRequestV2(name="Test Adgroup")

        result = await self.ad_group_service.update_ad_group(123, ad_group_request)

        self.assertEqual(result, ad_group_response)
        mock_get_campaign_by_ad_group_id.assert_called_once_with(123)
        mock_get_ad_group_by_id.assert_called_once_with(123)

    @patch("app.v2.services.ad_group_service.AdGroupService.get_ad_group_by_id")
    @patch("app.v2.services.ad_group_service.AdGroupService.get_campaign_by_ad_group_id")
    async def test_update_ad_group_not_secret_ad_group_not_changes(
            self,
            mock_get_campaign_by_ad_group_id: AsyncMock,
            mock_get_ad_group_by_id: AsyncMock
    ):
        self.ad_group_service.ad_group_translation = MagicMock()
        self.mock_target_translation.fetch_ad_group_targets = MagicMock(return_value=([], [], []))
        ad_group_response = SingleResponse[AdGroupV2](
            data=AdGroupV2(
                adGroupId=123,
                campaignId=123,
                name="Test Adgroup",
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[Target(type="1", id=1)],
                keywordBidModifiers=[],
                isArchived=False,
                carouselHeadline=None
            ),
            meta=EntityMeta(
                success=True,
                publishStatus=PublishStatus.PUBLISHED,
                warnings=None,
                errors=[],
                message=None,
                code=None
            )

        )
        mock_get_ad_group_by_id.return_value = ad_group_response
        ad_group_request = AdGroupUpdateRequestV2(name="Test Adgroup")
        self.ad_group_service.ad_group_translation.parse_ad_group_update_request.return_value = ad_group_request.model_dump(exclude_unset=True)

        result = await self.ad_group_service.update_ad_group(123, ad_group_request)

        self.assertEqual(result, ad_group_response)
        self.mock_lookup.get_adgroup_long_id_by_short_id.assert_called_once_with(123)
        mock_get_campaign_by_ad_group_id.assert_called_once_with(123)
        mock_get_ad_group_by_id.assert_called_once_with(123)

    @patch("app.v2.services.ad_group_service.AdGroupService.get_ad_group_by_id")
    @patch("app.v2.services.ad_group_service.AdGroupService.get_campaign_by_ad_group_id")
    @patch("app.v2.services.ad_group_service.AdGroupRequestValidator.validate_ad_group_request_single_call")
    @patch(
        "app.v2.services.ad_group_service.AdGroupRequestValidator.extra_validations_for_update")
    @patch("app.v2.services.ad_group_service.AdGroupService._AdGroupService__approve_and_publish_ad_group")
    @patch("app.v2.services.ad_group_service.AdGroupRequestValidator.validate_ad_group_targets")
    async def test_update_ad_group_not_secret_ad_group_success(
            self,
            mock_validate_ad_group_targets: MagicMock,
            mock_approve_and_publish_ad_group: AsyncMock,
            mock_extra_validations_for_update: AsyncMock,
            mock_validate_ad_group_request_single_call: MagicMock,
            mock_get_campaign_by_ad_group_id: AsyncMock,
            mock_get_ad_group_by_id: AsyncMock
    ):
        self.ad_group_service.ad_group_translation = MagicMock()
        self.mock_target_translation.fetch_ad_group_targets = MagicMock(return_value=([], [], []))
        ad_group_response = SingleResponse[AdGroupV2](
            data=AdGroupV2(
                adGroupId=123,
                campaignId=123,
                budgetType= BudgetType.DAILY,
                name="Test Adgroup",
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[Target(type="1", id=1)],
                keywordBidModifiers=[],
                isArchived=False,
                carouselHeadline=None
            ),
            meta=EntityMeta(
                success=True,
                publishStatus=PublishStatus.PUBLISHED,
                warnings=None,
                errors=[],
                message=None,
                code=None
            )

        )
        activation_update_payload = ActivationUpdatePayload(
            channel_data=ChannelData(
                carouselHeadline=None,
                name='Test Adgroup 2',
                startDate='2024-05-20',
                endDate='2024-06-20',
                alwaysOn=False,
                budgetType='Daily',
                budgetAmount=250.0,
                biddableEntities=None,
                keywordBidModifierGroup=None,
                divisionBanners=None,
                placementType=None,
                dayPartingStart=None,
                dayPartingEnd=None,
            )
        )
        ad_group_request = AdGroupUpdateRequestV2(name="Test Adgroup 1", status=AdGroupStatus.ACTIVE)
        self.mock_lookup.get_adgroup_long_id_by_short_id.return_value = "test_id"
        self.ad_group_service.ad_group_translation.parse_ad_group_update_request.return_value = ad_group_request.model_dump(exclude_unset=True)
        mock_get_ad_group_by_id.return_value = ad_group_response
        mock_get_campaign_by_ad_group_id.return_value = MagicMock(campaignType=InternalCampaignType.PLA)
        self.ad_group_service.ad_group_translation.build_update_activation_payload.return_value=activation_update_payload

        result = await self.ad_group_service.update_ad_group(123, ad_group_request)

        self.assertEqual(result, ad_group_response)
        mock_get_ad_group_by_id.assert_has_calls(
            [
                call(123),
                call(123)
            ]
        )
        mock_get_campaign_by_ad_group_id.assert_called_once_with(123)
        self.mock_activation_gateway.update_activation.assert_called_once_with(activation_update_payload, "test_id")
        mock_approve_and_publish_ad_group.assert_called_once()
        mock_extra_validations_for_update.assert_called_once()
        mock_validate_ad_group_request_single_call.assert_called_once()
