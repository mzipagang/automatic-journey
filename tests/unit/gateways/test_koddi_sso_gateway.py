from typing import List
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import HTTPException
from httpx import Response

from app.common.gateways.koddi_sso_gateway import KoddiSSOGateway
from app.common.model.downstream.advertiser_service import KoddiAdvertiserMultiBrand, KoddiAdvertiserMultiBrandRequest
from tests.utils_for_testing.auto_mock import auto_mock


class TestKoddiSSOGateway(IsolatedAsyncioTestCase):
    def setUp(self):
        self.__mock_external_http_client_service = MagicMock()
        self.__mock_async_external_http_client_service = AsyncMock()
        self.__mock_harness_service = MagicMock()

        self.__mock_harness_service.is_harness_flag_on.return_value = True

        self.koddi_sso_gateway = KoddiSSOGateway(
                self.__mock_async_external_http_client_service,
                self.__mock_external_http_client_service,
                self.__mock_harness_service)

    def __generate_brand_response(
            self,
            advertiser_ids: List[str],
            agency_id: str,
            koddi_ids: List[int],
    ) -> dict:
        return {
            "data": [
                {
                    "brandIds": advertiser_ids,
                    "percentages": None,
                    "koddiId": koddi_ids[0],
                    "agencyId": agency_id,
                    "primaryBrandId": advertiser_ids[0],
                },
                {
                    "brandIds": advertiser_ids,
                    "percentages": None,
                    "koddiId": koddi_ids[1],
                    "agencyId": None,
                    "primaryBrandId": advertiser_ids[0],
                }
            ]
        }

    @patch('logging.Logger.error')
    async def test_get_advertisers(self, mock_logger_error: MagicMock):
        self.__mock_async_external_http_client_service.get.side_effect = HTTPException(
            status_code=500, detail="Backend service unavailable"
        )

        with self.assertRaises(HTTPException) as context:
            await self.koddi_sso_gateway.get_advertisers(
                internal_advertiser_id="abc123"
            )

        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Backend service unavailable", context.exception.detail)

        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path="/map-koddi-sso-service/koddi/v1/brands",
            params={"filter.brandId": "abc123"},
            response_body_type='json',
            json_has_data_field=True,
            forward_client_error_response_content=True
        )

    async def test_get_advertisers_http_client_error(self):
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=500, json={'error': 'Test Error'})

        self.__mock_async_external_http_client_service.get.side_effect = HTTPException(
            status_code=500, detail="Backend service unavailable"
        )

        with self.assertRaises(HTTPException) as context:
            await self.koddi_sso_gateway.get_advertisers("abc123")

        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Backend service unavailable", context.exception.detail)

        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            forward_client_error_response_content=True,
            json_has_data_field=True,
            params={'filter.brandId': 'abc123'},
            path='/map-koddi-sso-service/koddi/v1/brands',
            response_body_type='json'
        )

    async def test__kodi_advertiser_multi_brand_upstream(self):
        # Arrange
        response_data = {
            "statusCode": "100 CONTINUE",
            "message": "string",
            "data": {
                "id": 37645,
                "brandItemRequests": [
                    { "brandId": "brandMain","primary": True, "percentage": 1.0 }
                ],
                "agencyId": "agency1",
                "brands": [
                    {"id": "1234", "name": "nameMain", "type": "BRAND"}
                ],
            }
        }
        request = KoddiAdvertiserMultiBrandRequest(
            brandItemRequests=[
                KoddiAdvertiserMultiBrand(brandId="brandMain", primary=True, percentage=1.0),
            ],
            agencyId="agency1",
        )

        self.__mock_async_external_http_client_service.post.side_effect = [Response(
            status_code=200,
            json=response_data)]

        # Act
        result = await self.koddi_sso_gateway.create_multi_brand_advertiser(request)

        self.assertEqual(37645, result.id )
        self.assertEqual("agency1", result.agencyId)
        self.assertEqual(1.0, result.brandItemRequests[0].percentage)
        self.__mock_async_external_http_client_service.post.assert_called_once_with(
            path="/map-koddi-sso-service/koddi/v1/brands",
            json={
                "brandItemRequests": [{
                    "brandId": "brandMain",
                    "primary": True,
                    "percentage": 1.0
                }],
                "agencyId": "agency1"
            },
            response_body_type='json',
            json_has_data_field=True,
            forward_client_error_response_content=True
        )

    @patch('logging.Logger.error')
    async def test_get_koddi_advertiser_id_for_agency__should_use_http_client(self, mock_logger_error: MagicMock):
        self.__mock_async_external_http_client_service.get.side_effect = HTTPException(
            status_code=500, detail="Backend service unavailable"
        )

        with self.assertRaises(HTTPException) as context:
            await self.koddi_sso_gateway.get_advertiser_by_agency("abc123", "xyz456")

        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Backend service unavailable", context.exception.detail)

        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path="/map-koddi-sso-service/koddi/v1/brands",
            params={'filter.brandId': "abc123"},
            response_body_type='json',
            json_has_data_field=True,
            forward_client_error_response_content=True
        )

    async def test_get_multi_brand_advertiser__should_use_http_client(self):
        advertiser_ids = ["1234", "5678"]
        agency_id = "4321"
        brands_response = self.__generate_brand_response(
            advertiser_ids=advertiser_ids,
            agency_id=agency_id,
            koddi_ids=[9876, 8765],
        )
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json=brands_response,
        )

        response = await self.koddi_sso_gateway.get_multi_brand_advertiser(advertiser_ids)
        response_with_agency = await self.koddi_sso_gateway.get_multi_brand_advertiser(
            advertiser_ids,
            agency_id
        )

        self.assertEqual(8765, response.koddiId)
        self.assertEqual(9876, response_with_agency.koddiId)

    async def test_get_advertisers__returns_brands(self):
        advertiser_ids = ["1234"]
        agency_id = "4321"
        koddi_ids = [9876, 8765]
        brands_response = self.__generate_brand_response(
            advertiser_ids=advertiser_ids,
            agency_id=agency_id,
            koddi_ids=koddi_ids,
        )
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json=brands_response,
        )

        response = await self.koddi_sso_gateway.get_advertisers(advertiser_ids[0])

        self.assertEqual(2, len(response))
        self.assertEqual(koddi_ids[0], response[0].koddiId)

    async def test_get_advertiser_by_agency__returns_matching_brand(self):
        advertiser_ids = ["1234"]
        agency_id = "4321"
        koddi_ids = [9876, 8765]
        brands_response = self.__generate_brand_response(
            advertiser_ids=advertiser_ids,
            agency_id=agency_id,
            koddi_ids=koddi_ids,
        )
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json=brands_response,
        )

        response = await self.koddi_sso_gateway.get_advertiser_by_agency(
            advertiser_ids[0],
            agency_id
        )

        self.assertEqual(koddi_ids[0], response.koddiId)

    async def test_get_advertiser_by_agency__returns_none_if_no_matching_brand(self):
        advertiser_ids = ["1234"]
        agency_id = "4321"
        koddi_ids = [9876, 8765]
        brands_response = self.__generate_brand_response(
            advertiser_ids=advertiser_ids,
            agency_id=agency_id,
            koddi_ids=koddi_ids,
        )
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json=brands_response,
        )

        response = await self.koddi_sso_gateway.get_advertiser_by_agency(
            advertiser_ids[0],
            "5678"
        )

        self.assertIsNone(response)

    def test_advertiser_lock_key__generates_key(self):
        advertiser_id="1234"
        agency_id="5678"

        lock_key = self.koddi_sso_gateway.advertiser_lock_key(advertiser_id)
        lock_key_with_agency = self.koddi_sso_gateway.advertiser_lock_key(advertiser_id, agency_id)

        self.assertEqual(
            advertiser_id,
            lock_key
        )
        self.assertEqual(
            f"{advertiser_id}:{agency_id}",
            lock_key_with_agency
        )

    def test_multi_brand_lock_key__generates_key(self):
        advertiser_ids=["1234", "5678"]
        agency_id="4321"
        brand_request = auto_mock({
            "brandItemRequests": [
                {"brandId": advertiser_id}
                for advertiser_id in advertiser_ids
            ],
            "agencyId": None
        }, MagicMock(spec=KoddiAdvertiserMultiBrandRequest))
        brand_request_with_agency = auto_mock({
            "brandItemRequests": [
                {"brandId": advertiser_id}
                for advertiser_id in advertiser_ids
            ],
            "agencyId": agency_id,
        }, MagicMock(spec=KoddiAdvertiserMultiBrandRequest))

        multi_brand_key = self.koddi_sso_gateway.multi_brand_lock_key(
            brand_request
        )
        multi_brand_key_with_agency = self.koddi_sso_gateway.multi_brand_lock_key(
            brand_request_with_agency
        )

        self.assertEqual(
            f"{",".join(advertiser_ids)}",
            multi_brand_key
        )
        self.assertEqual(
            f"{",".join(advertiser_ids)}:{agency_id}",
            multi_brand_key_with_agency
        )

    async def test_create_advertiser_by_agency__creates_koddi_brand(self):
        advertiser_id="1234"
        agency_id="5678"
        koddi_id=9876
        response = {
            "data": {
                "id": koddi_id,
                "brandItemRequests": [{
                    "brandId": advertiser_id,
                }],
                "agencyId": agency_id,
            }
        }
        self.__mock_async_external_http_client_service.post.return_value = Response(
            status_code=200,
            json=response,
        )

        koddi_advertiser = await self.koddi_sso_gateway.create_advertiser_by_agency(
            advertiser_id,
            agency_id
        )

        self.assertEqual(koddi_id, koddi_advertiser.id)
        self.assertEqual(agency_id, koddi_advertiser.agencyId)
        self.assertEqual(advertiser_id, koddi_advertiser.brandItemRequests[0].brandId)

    async def test_get_advertisers_for_user__returns_advertisers(self):
        brand_id="1234"
        koddi_id=4321
        agency_id="5678"
        response_data = {
            "data": [{
                "brandIds": [brand_id],
                "koddiId": koddi_id,
                "agencyId": agency_id,
                "primaryBrandId": brand_id,
            }]
        }
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json=response_data,
        )

        advertisers = await self.koddi_sso_gateway.get_advertisers_for_user()

        self.assertEqual(1, len(advertisers))
        self.assertEqual(brand_id, advertisers[0].brandIds[0])
        self.assertEqual(brand_id, advertisers[0].primaryBrandId)
        self.assertEqual(koddi_id, advertisers[0].koddiId)
        self.assertEqual(agency_id, advertisers[0].agencyId)
