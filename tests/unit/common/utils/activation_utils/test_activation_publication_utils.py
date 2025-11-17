from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from typing_extensions import override

from app.common.utils.activation_utils import ActivationPublicationUtils
from app.common.view_models import AdGroupStatus
from app.v2.model.downstream.activation_service import ActivationResponse, ActivationResponseV2, ActivationMetaData


class TestActivationPublicationUtils(IsolatedAsyncioTestCase):
    __mock_creative_service_gateway: AsyncMock

    __subject: ActivationPublicationUtils

    @override
    async def asyncSetUp(self):
        self.__mock_creative_service_gateway = AsyncMock()

        self.__subject = ActivationPublicationUtils(creative_service_gateway=self.__mock_creative_service_gateway)

    async def test_activation_is_publishable__pause_to_active__should_return_false(self):
        current_status: AdGroupStatus = AdGroupStatus.PAUSED
        requested_status: AdGroupStatus = AdGroupStatus.ACTIVE
        mock_activation_response: MagicMock = MagicMock(
            spec=ActivationResponseV2[ActivationResponse],
            data=MagicMock(spec=ActivationResponse),
            warnings=[],
            errors=[])

        result = await self.__subject.activation_is_publishable(
            ad_group_current_status=current_status,
            ad_group_requested_status=requested_status,
            activation_response=mock_activation_response)

        self.assertFalse(result)

    async def test_activation_is_publishable__unapproved__should_return_false(self):
        current_status: AdGroupStatus = AdGroupStatus.ACTIVE
        requested_status: AdGroupStatus = AdGroupStatus.ACTIVE
        mock_activation_response: MagicMock = MagicMock(
            spec=ActivationResponseV2[ActivationResponse],
            data=MagicMock(
                spec=ActivationResponse,
                metadata=MagicMock(spec=ActivationMetaData, approved=False),
                channel_data=dict(),
                is_video_carousel_activation=lambda: False
            ),
            warnings=[],
            errors=[])

        result = await self.__subject.activation_is_publishable(
            ad_group_current_status=current_status,
            ad_group_requested_status=requested_status,
            activation_response=mock_activation_response)

        self.assertFalse(result)

    async def test_activation_is_publishable__creative_not_ready__should_return_false(self):
        current_status: AdGroupStatus = AdGroupStatus.ACTIVE
        requested_status: AdGroupStatus = AdGroupStatus.ACTIVE
        mock_activation_response: MagicMock = MagicMock(
            spec=ActivationResponseV2[ActivationResponse],
            data=MagicMock(
                spec=ActivationResponse,
                metadata=MagicMock(spec=ActivationMetaData, approved=False),
                channel_data={'creativeGroupEntities': ['abc-123']},
                is_video_carousel_activation=lambda: True
            ),
            warnings=[],
            errors=[])

        self.__mock_creative_service_gateway.creative_group_is_ready.return_value = False

        result = await self.__subject.activation_is_publishable(
            ad_group_current_status=current_status,
            ad_group_requested_status=requested_status,
            activation_response=mock_activation_response)

        self.assertFalse(result)

        self.__mock_creative_service_gateway.creative_group_is_ready.assert_called_with('abc-123')
