from typing import List
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import HTTPException
from httpx import Response
from httpx import codes as httpx_codes

from app.common.exceptions import ActivationLockedException, AdGroupNotPublishedException
from app.common.gateways.activation_gateway import ActivationGateway
from app.common.model.shared import EntityMeta, PublishStatus, Warnings
from app.common.view_models import SingleResponse
from app.v2.model.downstream.activation_service import (
    ActivationsQueryBody,
    ActivationMetaData,
    ActivationPayload,
    ActivationResponse,
    ActivationStatus,
    ActivationUpdatePayload,
    ChannelConfig,
    ChannelData,
    Included, ActivationResponseV2,
)
from app.v2.view_models import AdGroupV2


class TestActivationGateway(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_async_internal_http_client_service = AsyncMock()
        self.mock_internal_http_client_service = MagicMock()
        self.mock_harness_service = MagicMock()

        self.mock_harness_service.is_harness_flag_on.return_value = True

        self.activation_gateway = ActivationGateway(
            async_internal_api_http_client_service=self.mock_async_internal_http_client_service,
            internal_api_http_client_service=self.mock_internal_http_client_service,
            harness_service=self.mock_harness_service,
        )

    @staticmethod
    def __v2_activation(activation: ActivationResponse) -> ActivationResponseV2[ActivationResponse]:
        return ActivationResponseV2[ActivationResponse](
            data=activation,
            included=Included(
                configuration=[],
                configuration_by_activation={}
            )
        )

    @staticmethod
    def __v2_activations(activations: List[ActivationResponse]) -> ActivationResponseV2[List[ActivationResponse]]:
        return ActivationResponseV2[List[ActivationResponse]](
            data=activations,
            included=Included(
                configuration=[],
                configuration_by_activation={}
            )
        )

    @staticmethod
    def __v2_activation_new(activation: ActivationResponse) -> ActivationResponseV2[ActivationResponse]:
        return ActivationResponseV2[ActivationResponse](
            data=activation,
            meta=EntityMeta(
                success=True,
                publishStatus=PublishStatus.PUBLISHED
            )
        )

    async def test_get_activation_by_id(self):
        activation_id = "1234"
        expected_activation = self.__v2_activation(ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        ))
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.get_activation_by_id(activation_id)

        self.assertEqual(result, expected_activation)

    async def test_get_activations_single_id(self):
        config = ActivationsQueryBody(ids=["1234"])
        expected_activation = self.__v2_activations([ActivationResponse(
            id="1234",
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        )])
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.get_activations(config)

        self.assertEqual(expected_activation, result)

    async def test_get_activations_multiple_ids(self):
        config = ActivationsQueryBody(ids=["1234", "5678"])
        expected_activations = self.__v2_activations([
            ActivationResponse(
                id=id,
                channel_config=ChannelConfig(type="example", version="1.0"),
                campaign_id="example_campaign_id",
                status=ActivationStatus.DRAFT,
                metadata=ActivationMetaData(
                    created_at="2025-02-25T12:00:00",
                    last_publish_system_errors=[],
                    last_publish_field_errors=[]
                )
            ) for id in config.ids
        ])
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activations.model_dump())

        result = await self.activation_gateway.get_activations(config)

        self.assertEqual(result, expected_activations)

    async def test_get_activations_by_koddi_id(self):
        config = ActivationsQueryBody(koddi_id="koddi_1234")
        expected_activations = self.__v2_activations([
            ActivationResponse(
                id="1234",
                channel_config=ChannelConfig(type="example", version="1.0"),
                campaign_id="example_campaign_id",
                status=ActivationStatus.DRAFT,
                metadata=ActivationMetaData(
                    created_at="2025-02-25T12:00:00",
                    last_publish_system_errors=[],
                    last_publish_field_errors=[]
                )
            ),
            ActivationResponse(
                id="5678",
                channel_config=ChannelConfig(type="example", version="1.0"),
                campaign_id="example_campaign_id",
                status=ActivationStatus.DRAFT,
                metadata=ActivationMetaData(
                    created_at="2025-02-25T12:00:00",
                    last_publish_system_errors=[],
                    last_publish_field_errors=[]
                )
            )
        ])

        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activations.model_dump())

        result = await self.activation_gateway.get_activations(config)

        self.assertEqual(result, expected_activations)

    @patch("app.common.gateways.activation_gateway.logger")
    async def test_create_activation(self, mock_logger):
        activation_payload = ActivationPayload(
            channel_data=ChannelData(
                name="example_name"
            ),
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id"
        )
        expected_activation = self.__v2_activation(ActivationResponse(
            id="1234",
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        ))
        self.mock_async_internal_http_client_service.post.return_value = Response(
            200,
            json=expected_activation.model_dump()
        )

        result = await self.activation_gateway.create_activation(activation_payload)

        self.assertEqual(expected_activation, result)

    async def test_update_activation_exception(self):
        payload = ActivationUpdatePayload(
            channel_data=ChannelData(
                name="example_name"
            )
        )
        expected_activation = self.__v2_activation(ActivationResponse(
            id="1234",
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        ))
        expected_activation = expected_activation.model_dump()

        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activation)

        del expected_activation['data']['id']
        self.mock_async_internal_http_client_service.patch.return_value = Response(200, json=expected_activation)

        with self.assertRaises(HTTPException) as context:
            await self.activation_gateway.update_activation(payload, "")

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Failed to update activation", context.exception.detail)

    @patch("app.common.gateways.activation_gateway.logger")
    async def test_update_activation_success(self, mock_logger):
        payload = ActivationUpdatePayload(
            channel_data=ChannelData(
                name="example_name"
            )
        )
        expected_activation = self.__v2_activation(ActivationResponse(
            id="1234",
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        ))
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activation.model_dump())
        self.mock_async_internal_http_client_service.patch.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.update_activation(payload, "1234")

        self.assertEqual(result, expected_activation)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch("app.common.gateways.activation_gateway.logger")
    async def test_publish_activation_success(self, mock_logger, mock_is_harness_flag_on):
        activation_id = "1234"
        expected_activation = ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            ),
            unpublished_data = {}
        )

        mock_is_harness_flag_on.return_value = True
        expected_activation_wrapper = self.__v2_activation(expected_activation)

        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activation_wrapper.model_dump())
        self.mock_async_internal_http_client_service.patch.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.publish_activation(activation_id)
        self.assertEqual(result, expected_activation)
        mock_logger.info.assert_any_call("Published activation response: %s", expected_activation.model_dump())
        mock_logger.info.assert_any_call("Fetching adgroup until publication is settled...")

    @patch("app.common.gateways.activation_gateway.logger")
    async def test_publish_activation_fail(self, mock_logger):
        activation_id = "1234"
        expected_activation = self.__v2_activation(ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            ),
            unpublished_data = {
                "endDate": "2025-07-13",
                "alwaysOn": True
            }
        ))
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activation.model_dump())
        self.mock_async_internal_http_client_service.patch.return_value = Response(httpx_codes.INTERNAL_SERVER_ERROR, json={})

        with self.assertRaises(HTTPException) as context:
            await self.activation_gateway.publish_activation(activation_id)

        self.assertEqual(context.exception.status_code, 400)
        mock_logger.error.assert_called_with(
            "Activation API publishing call returned error %s: for id: %s",
            httpx_codes.INTERNAL_SERVER_ERROR,
            activation_id,
        )

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch("app.common.gateways.activation_gateway.logger")
    async def test_publish_activation_upstream_patch_behavior(self, mock_logger, mock_is_harness_flag_on):
        activation_id = "1234"
        expected_activation = ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        )
        mock_is_harness_flag_on.return_value = True
        expected_activation_wrapper = self.__v2_activation(expected_activation)
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=expected_activation_wrapper.model_dump())
        self.mock_async_internal_http_client_service.patch.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.publish_activation(activation_id)

        self.assertEqual(result, expected_activation)
        mock_logger.info.assert_any_call("Published activation response: %s", expected_activation.model_dump())


    @patch("app.common.gateways.activation_gateway.logger")
    async def test_publish_activation_locked_metadata(self, mock_logger):
        activation_id = "1234"
        locked_activation = self.__v2_activation(ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[],
                is_locked=True
            )
        ))
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=locked_activation.model_dump())

        with self.assertRaises(ActivationLockedException):
            await self.activation_gateway.publish_activation(activation_id)

    async def test_validate_activation_success(self):
        activation_id = "1234"
        validation_response = {
            "valid": True,
            "errors": []
        }
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=validation_response)

        result = await self.activation_gateway.validate_activation(activation_id)

        self.assertTrue(result)

    async def test_validate_activation_fail(self):
        activation_id = "1234"
        validation_response = {
            "valid": False,
            "errors": [{"field": "test", "type": "test_type", "mismatch_description": "test fail"}]
        }
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=validation_response)

        with self.assertRaises(HTTPException) as context:
            await self.activation_gateway.validate_activation(activation_id)

        self.assertEqual(context.exception.status_code, 422)

    async def test_validate_activation_invalid(self):
        activation_id = "1234"
        validation_response = {
            "valid": False,
            "errors": []
        }
        self.mock_async_internal_http_client_service.get.return_value = Response(200, json=validation_response)

        with self.assertRaises(HTTPException) as context:
            await self.activation_gateway.validate_activation(activation_id)

        self.assertEqual(context.exception.status_code, 400)

    @patch("app.common.gateways.activation_gateway.logger")
    async def test_approve_activation(self, mock_logger):
        activation_id = "1234"
        expected_activation = ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        )
        self.mock_async_internal_http_client_service.patch.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.approve_activation(activation_id)

        self.assertEqual(result, ActivationResponseV2(data=expected_activation))

    @patch("app.common.gateways.activation_gateway.logger")
    async def test_pause_activation(self, mock_logger):
        activation_id = "1234"
        expected_activation = ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.PAUSED,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        )
        self.mock_async_internal_http_client_service.patch.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.pause_activation(activation_id)

        self.assertEqual(result, ActivationResponseV2(data=expected_activation))

    @patch("app.common.gateways.activation_gateway.logger")
    async def test_unpause_activation(self, mock_logger):
        activation_id = "1234"
        expected_activation = ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.ACTIVE,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            )
        )
        self.mock_async_internal_http_client_service.patch.return_value = Response(200, json=expected_activation.model_dump())

        result = await self.activation_gateway.unpause_activation(activation_id)

        self.assertEqual(result, ActivationResponseV2(data=expected_activation))

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch("app.common.gateways.activation_gateway.ActivationGateway.get_activation_by_id")
    @patch("app.common.gateways.activation_gateway.logger")
    async def test_wait_for_adgroup_publication_status_to_settle(self, mock_logger, mock_get_activation_by_id, mock_is_harness_flag_on):
        activation_id = "1234"
        expected_response = self.__v2_activation(ActivationResponse(
                id=activation_id,
                channel_config=ChannelConfig(type="example", version="1.0"),
                campaign_id="example_campaign_id",
                status=ActivationStatus.PAUSED,
                metadata=ActivationMetaData(
                    created_at="2025-02-25T12:00:00",
                    last_publish_system_errors=[],
                    last_publish_field_errors=[]
                ),
                unpublished_data={}
            )
        )

        mock_get_activation_by_id.return_value = expected_response
        mock_is_harness_flag_on.return_value = True

        await self.activation_gateway.wait_for_adgroup_publication_status_to_settle(activation_id)
        mock_get_activation_by_id.assert_called()
        mock_logger.info.assert_any_call("Fetching adgroup until publication is settled...")

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch("app.common.gateways.activation_gateway.ActivationGateway.get_activation_by_id")
    @patch("app.common.gateways.activation_gateway.logger")
    async def test_wait_for_adgroup_publication_status_to_settle_Pending(self, mock_logger, mock_get_activation_by_id,
                                                                 mock_is_harness_flag_on):
        activation_id = "1234"
        expected_response = self.__v2_activation(ActivationResponse(
                id=activation_id,
                channel_config=ChannelConfig(type="example", version="1.0"),
                campaign_id="example_campaign_id",
                status=ActivationStatus.PAUSED,
                metadata=ActivationMetaData(
                    created_at="2025-02-25T12:00:00",
                    last_publish_system_errors=[],
                    last_publish_field_errors=[]
                ),
                unpublished_data={
                    "endDate": "2025-07-13",
                    "alwaysOn": True
                }
            )
        )
        mock_get_activation_by_id.return_value = expected_response
        mock_is_harness_flag_on.return_value = True

        with self.assertRaises(AdGroupNotPublishedException):
            await self.activation_gateway.wait_for_adgroup_publication_status_to_settle(activation_id)
        mock_logger.info.assert_any_call("Fetching adgroup until publication is settled...")
        mock_logger.info.assert_any_call("Adgroup %s is not yet published, re-fetching...", activation_id)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch("app.common.gateways.activation_gateway.ActivationGateway.get_activation_by_id")
    @patch("app.common.gateways.activation_gateway.logger")
    async def test_wait_for_adgroup_publication_status_to_settle_create_adgroup(self, mock_logger, mock_get_activation_by_id,
                                                                         mock_is_harness_flag_on):
        activation_id = "1234"
        mock_errors = [{
                "code": "biddableEntities",
                "reason": "Bid management is incomplete or has an error",
                "datetime": {
                    "value": "2025-08-14T17:17:11.330000",
                    "timezone": "UTC"
                },
                "field_name": "biddableEntities",
                "identifier": 1234
            },
            {
                "field": "Bid Amount",
                "message": "237 - 100.0 - Bid amount is greater than max bid amount.",
                "entity_id": "237"
            }
        ]
        expected_response = self.__v2_activation(ActivationResponse(
                id=activation_id,
                channel_config=ChannelConfig(type="example", version="1.0"),
                campaign_id="example_campaign_id",
                status=ActivationStatus.PAUSED,
                metadata=ActivationMetaData(
                    created_at="2025-02-25T12:00:00",
                    last_publish_system_errors=[],
                    last_publish_field_errors=[]
                ),
                unpublished_data={
                    "endDate": "2025-07-13",
                    "alwaysOn": True
                }
            )
        )
        expected_response.errors = mock_errors
        mock_get_activation_by_id.return_value = expected_response
        mock_is_harness_flag_on.return_value = True

        await self.activation_gateway.wait_for_adgroup_publication_status_to_settle(activation_id)
        mock_logger.info.assert_any_call("Fetching adgroup until publication is settled...")
        # assert that the "Adgroup %s is not yet published, re-fetching..." log was not called because there are errors,
        # retry should not happen
        self.assertNotIn(("Adgroup %s is not yet published, re-fetching...", activation_id), mock_logger.info.call_args_list)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=False)
    @patch("app.common.gateways.activation_gateway.logger")
    async def test_wait_for_adgroup_publication_status_to_settle_feature_flag_off(self, mock_logger, mock_is_harness_flag_on):
        activation_id = "1234"
        expected_activation = ActivationResponse(
            id=activation_id,
            channel_config=ChannelConfig(type="example", version="1.0"),
            campaign_id="example_campaign_id",
            status=ActivationStatus.DRAFT,
            metadata=ActivationMetaData(
                created_at="2025-02-25T12:00:00",
                last_publish_system_errors=[],
                last_publish_field_errors=[]
            ),
            unpublished_data = {}
        )

        mock_is_harness_flag_on.return_value = False
        expected_activation_wrapper = self.__v2_activation(expected_activation)

        self.mock_async_internal_http_client_service.get.return_value = Response(200,
                                                                                 json=expected_activation_wrapper.model_dump())
        self.mock_async_internal_http_client_service.patch.return_value = Response(200,
                                                                                   json=expected_activation.model_dump())

        result = await self.activation_gateway.publish_activation(activation_id)
        self.assertNotIn(("Fetching adgroup until publication is settled...", activation_id),
                         mock_logger.info.call_args_list)