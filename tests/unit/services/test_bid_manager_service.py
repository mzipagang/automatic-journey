from copy import deepcopy
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, call, patch, Mock

import pytest
from fastapi import HTTPException

from app.common.gateways.bid_manager_gateway import BidManagerGateway
from app.common.model.campaign_types import InternalCampaignType, BidManagerCampaignType
from app.common.model.downstream.product_manager import ProductSearchResponse, ProductManagerMeta, \
    ProductManagerMetaPage, Product, Taxonomy, TaxonomyProperties
from app.common.model.redis import CachedProduct
from app.common.view_models import EntitiesRequest, Entity
from app.v2.model.downstream.activation_service import (
    ActivationResponse,
    ActivationResponseV2, ChannelConfig,
)
from app.common.model.downstream.bid_manager import (
    Bid,
    BidEntityFailure,
    BidFailure,
    BidIdentifier,
    BidsResponseData,
    BidValidationResponse,
    CreateBidsRequest,
    EmptyBid,
    IncorrectBidAmountFailure,
    IncorrectBids,
    IncorrectMaxBid,
    IncorrectMinBid,
    MultipleBidsResponseData,
    SuggestionsResponse,
    ValidateBidRequest,
    ValidatedBidIdentifiers,
    BidData,
)
from app.common.model.shared import SingleDataResponse
from app.common.services.bid_manager_service import BidManagerService
from tests.unit.services.constants import UPDATED_ACTIVATION_RESPONSE_JSON
from app.common.utils.deep_merge import deep_merge


class TestBidManagerService(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_redis = AsyncMock()
        self.mock_bid_manager_gateway = Mock(spec=BidManagerGateway)
        self.mock_lookup = AsyncMock()
        self.mock_product_gateway = AsyncMock()

        self.bid_manager_service = BidManagerService(
            redis_cache=self.mock_redis,
            bid_manager_gateway=self.mock_bid_manager_gateway,
            lookup=self.mock_lookup,
            product_gateway=self.mock_product_gateway,
        )

    def __mock_entities(self, **kwargs):
        default_args = {
            "id": 1234,
            "bidAmount": 0.2,
            "useBaseBid": False,
            "deleted": False
        }
        return [Entity(**({**default_args, **kwargs}))]

    @staticmethod
    def __mock_activation_response(**kwargs) -> ActivationResponseV2[ActivationResponse]:
        base_activation_json = deepcopy(UPDATED_ACTIVATION_RESPONSE_JSON)
        merged_activation_json = deep_merge(base_activation_json, kwargs)
        return ActivationResponseV2[ActivationResponse](
            **merged_activation_json
        )


    async def test_build_pla_create_bids_request_from_entities__builds_bids(self):
        # Arrange
        entity_id = 1234
        product_upc = "4011"
        entities = self.__mock_entities(id=entity_id)
        base_bid = 0.1
        expected_response = CreateBidsRequest(
            type="PLA",
            default_bid=base_bid,
            bids=[Bid(id=product_upc, bid_amount=0.2)]
        )
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [CachedProduct(**{"upc": product_upc})]

        # Act
        result = await self.bid_manager_service.build_pla_create_bids_request_from_entities(
            entities,
            base_bid
        )

        # Assert
        self.assertEqual(result, expected_response)
        self.mock_lookup.get_product_details_by_short_id_batch.assert_called_with([entity_id])

    @patch('logging.Logger.warning')
    async def test_build_pla_create_bids_request_from_entities__warns_if_cached_product_is_none(self, mock_log_warning):
        entity_id = 1234
        entities = self.__mock_entities(id=entity_id)
        base_bid = 0.1
        expected_response = CreateBidsRequest(
            type="PLA",
            default_bid=base_bid,
            bids=[]
        )
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [None]

        result = await self.bid_manager_service.build_pla_create_bids_request_from_entities(
            entities,
            base_bid
        )

        self.assertEqual(result, expected_response)
        self.mock_lookup.get_product_details_by_short_id_batch.assert_called_with([entity_id])
        mock_log_warning.assert_called_with("Product ID not found in cache [create]: %s", entity_id)

    @patch('logging.Logger.warning')
    async def test_build_pla_create_bids_request_from_entities__warns_if_product_is_null(self, mock_log_warning):
        entity_id = 1234
        entities = self.__mock_entities(id=entity_id)
        base_bid = 0.1
        expected_response = CreateBidsRequest(
            type="PLA",
            default_bid=base_bid,
            bids=[]
        )
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [None]

        result = await self.bid_manager_service.build_pla_create_bids_request_from_entities(
            entities,
            base_bid
        )

        self.assertEqual(result, expected_response)
        self.mock_lookup.get_product_details_by_short_id_batch.assert_called_with([entity_id])
        mock_log_warning.assert_called_with("Product ID not found in cache [create]: %s", entity_id)

    async def test_build_pla_create_bids_request_from_entities__sets_bid_amount_to_base_bid_if_entity_bid_amount_is_none(self):
        entities = self.__mock_entities(bidAmount=None)
        base_bid = 0.1
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [
            CachedProduct(**{"upc": "4011"})
        ]

        result = await self.bid_manager_service.build_pla_create_bids_request_from_entities(
            entities,
            base_bid
        )

        self.assertEqual(result.bids[0].bid_amount, base_bid)

    async def test_build_pla_create_bids_request_from_entities__sets_bid_amount_to_base_bid_if_use_base_bid_is_true(self):
        entities = self.__mock_entities(useBaseBid=True)
        base_bid = 0.1
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [
            CachedProduct(**{"upc": "4011"})
        ]

        result = await self.bid_manager_service.build_pla_create_bids_request_from_entities(
            entities,
            base_bid
        )

        self.assertEqual(result.bids[0].bid_amount, base_bid)

    async def test_build_pla_create_bids_request_from_entities__sets_bid_amount_to_entity_bid_amount_if_not_none(self):
        entities = self.__mock_entities()
        base_bid = 0.1
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [
            CachedProduct(**{"upc": "4011"})
        ]

        result = await self.bid_manager_service.build_pla_create_bids_request_from_entities(
            entities,
            base_bid
        )

        self.assertEqual(result.bids[0].bid_amount, entities[0].bidAmount)

    async def test_create_pla_bids_from_entities__builds_bids_and_sends_create_request(self):
        entity_id = 1234
        product_upc = "4011"
        bid_group_id="9876"
        entities = self.__mock_entities(id=entity_id)
        base_bid = 0.1
        created_bids_request = CreateBidsRequest(
            type="PLA",
            default_bid=base_bid,
            bids=[Bid(id=product_upc, bid_amount=0.2)]
        )
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [
            CachedProduct(**{"upc": product_upc})
        ]
        self.mock_bid_manager_gateway.create_bids.return_value = bid_group_id

        result = await self.bid_manager_service.create_pla_bids_from_entities(
            entities,
            base_bid
        )

        self.assertEqual(result, bid_group_id)
        self.mock_lookup.get_product_details_by_short_id_batch.assert_called_with([entity_id])
        self.mock_bid_manager_gateway.create_bids.assert_called_with(
            created_bids_request,
            enforce_validation=True
        )

    async def test_create_pla_bids_from_entities_raises_error_if_no_bids_were_built(self):
        entity_id = 1234
        entities = self.__mock_entities(id=entity_id)
        base_bid = 0.1
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [None]

        with self.assertRaises(HTTPException) as context:
            await self.bid_manager_service.create_pla_bids_from_entities(
                entities,
                base_bid
            )

        self.mock_lookup.get_product_details_by_short_id_batch.assert_called_with([entity_id])
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "No valid products selected to create bids.")

    async def test_get_entities__filters_bid_groups(self):
        biddable_entity_ids = ["1234"]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[BidsResponseData(
                id="1234",
                type=InternalCampaignType.TOA,
                bids=[Bid(id="4011", bid_amount=0.1)],
                default_bid=0.1
            )]
        )

        result, default_bid = await self.bid_manager_service.get_entities(
            biddable_entity_ids,
            InternalCampaignType.PLA
        )

        self.assertEqual(result, [])
        self.assertEqual(default_bid, 0.0)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)

    async def test_get_entities__gets_missing_entity_ids_and_missing_products(self):
        biddable_entity_ids = ["1234"]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[BidsResponseData(
                id="1234",
                type=InternalCampaignType.PLA,
                bids=[Bid(id="4011", bid_amount=0.1)],
                default_bid=0.1
            )]
        )
        generated_entity_ids = [4321]
        mock_product = MagicMock()
        mock_product.upc = "4011"
        mock_product.model_dump.return_value = {"upc": mock_product.upc}
        mock_product_response = MagicMock()
        mock_product_response.data.validProducts = [mock_product]
        expected_response = [Entity(
            id=4321,
            useBaseBid=True,
            bidAmount=0.1,
            deleted=False
        )]
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = [None]
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [None]
        self.mock_lookup.set_product_short_ids_by_upcs.return_value = generated_entity_ids
        self.mock_product_gateway.get_products_by_upcs.return_value = mock_product_response

        result, default_bid = await self.bid_manager_service.get_entities(
            biddable_entity_ids,
            InternalCampaignType.PLA
        )

        self.assertEqual(expected_response, result)
        self.assertEqual(0.1, default_bid)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)
        self.mock_lookup.get_product_short_id_by_upc_batch.assert_called_with(["4011"])
        self.mock_lookup.get_product_details_by_short_id_batch.assert_called_with([None])
        self.mock_lookup.set_product_short_ids_by_upcs.assert_called_with(["4011"])
        self.mock_product_gateway.get_products_by_upcs.assert_called_with(
            upcs=["4011"],
            advertiser_names=None,
            last_sold_within_days=None
        )
        self.mock_lookup.set_product_details_by_short_id_batch.assert_called_with({
            4321: CachedProduct(
                upc="4011",
                description=None,
                isValid=False,
                brand=None,
                quantity=None,
                taxonomy=None,
                restrictions=None,
                lastSoldDate=None
            )
        })

    async def test_get_entities__sets_use_base_bid_to_false_if_bid_amount_is_different_from_default(self):
        biddable_entity_ids = ["1234"]
        expected_entities = [
            Entity(id="4321", useBaseBid=False, bidAmount=0.2, deleted=False),
        ]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[BidsResponseData(
                id="1234",
                type=InternalCampaignType.PLA,
                bids=[Bid(id="4011", bid_amount=0.2)],
                default_bid=0.1
            )]
        )
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = ["4321"]
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [CachedProduct(**{"upc": "4321"})]

        result, default_bid = await self.bid_manager_service.get_entities(
            biddable_entity_ids,
            InternalCampaignType.PLA
        )

        self.assertEqual(result, expected_entities)
        self.assertEqual(default_bid, 0.1)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)
        self.mock_lookup.get_product_short_id_by_upc_batch.assert_called_with(["4011"])

    async def test_get_entities__aggregates_entities_for_each_bid_group(self):
        biddable_entity_ids = ["1234", "2345"]
        expected_entities = [
            Entity(id=4321, useBaseBid=False, bidAmount=0.2, deleted=False),
            Entity(id=9876, useBaseBid=True, bidAmount=0.1, deleted=False),
        ]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[
                BidsResponseData(
                    id="1234",
                    type=InternalCampaignType.PLA,
                    bids=[Bid(id="4011", bid_amount=0.2)],
                    default_bid=0.1
                ),
                BidsResponseData(
                    id="2345",
                    type=InternalCampaignType.PLA,
                    bids=[Bid(id="4012", bid_amount=0.1)],
                    default_bid=0.1
                ),
            ]
        )
        self.mock_lookup.get_product_short_id_by_upc_batch.side_effect = [
            ["4321"],
            ["9876"]
        ]
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [
            CachedProduct(**{"upc": "4321"}),
            CachedProduct(**{"upc": "9876"}),
        ]

        result, default_bid = await self.bid_manager_service.get_entities(
            biddable_entity_ids,
            InternalCampaignType.PLA
        )

        self.assertEqual(expected_entities, result)
        self.assertEqual(default_bid, 0.1)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)

    async def test_get_entities__includes_bids_with_lowercase_campaign_types(self):
        biddable_entity_ids = ["1234"]
        expected_entities = [
            Entity(id="4321", useBaseBid=False, bidAmount=0.2, deleted=False)
        ]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[
                BidsResponseData(
                    id="1234",
                    type=InternalCampaignType.PLA.lower(),
                    bids=[Bid(id="4011", bid_amount=0.2)],
                    default_bid=0.1
                )
            ]
        )
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = ["4321"]
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [CachedProduct(**{"upc": "4321"})]

        result, default_bid = await self.bid_manager_service.get_entities(
            biddable_entity_ids,
            InternalCampaignType.PLA
        )

        self.assertEqual(expected_entities, result)
        self.assertEqual(default_bid, 0.1)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)

    async def test_get_entities__includes_bids_with_lowercase_carousel_type(self):
        biddable_entity_ids = ["1234"]
        expected_entities = [
            Entity(id="4321", useBaseBid=False, bidAmount=0.2, deleted=False)
        ]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[
                BidsResponseData(
                    id="1234",
                    type=BidManagerCampaignType.CAROUSEL.lower(),
                    bids=[Bid(id="4011", bid_amount=0.2)],
                    default_bid=0.1
                )
            ]
        )
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = ["4321"]
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [CachedProduct(**{"upc": "4321"})]

        result, default_bid = await self.bid_manager_service.get_entities(
            biddable_entity_ids,
            InternalCampaignType.CAROUSEL
        )

        self.assertEqual(expected_entities, result)
        self.assertEqual(default_bid, 0.1)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)

    async def test_validate_bid_entities__filters_bid_groups_with_different_campaign_types(self):
        bid_group_ids = ["1234"]
        validation_request = ValidateBidRequest(bidIdsMustHaveValidEntities=True)
        validation_response = BidValidationResponse(valid=True)
        bids = MultipleBidsResponseData(found=[
            BidsResponseData(
                id="1234",
                type=BidManagerCampaignType.TOA,
                bids=[Bid(id="4011", bid_amount=0.1)])
        ])
        expected_result = ValidatedBidIdentifiers()
        self.mock_bid_manager_gateway.validate_bid.return_value = validation_response
        self.mock_bid_manager_gateway.get_bids.return_value = bids
        self.mock_lookup.get_product_short_ids_by_upc_batch.return_value = []

        result = await self.bid_manager_service.validate_bid_entities(
            bid_group_ids,
            validation_request,
            InternalCampaignType.PLA
        )

        self.assertEqual(result, expected_result)
        self.mock_bid_manager_gateway.validate_bid.assert_called_with(bid_group_ids[0], validation_request)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(bid_group_ids)
        self.mock_lookup.get_product_short_id_by_upc_batch.assert_called_with([])

    async def test_validate_bid_entities__includes_bids_with_lowercase_campaign_types(self):
        bid_group_ids = ["1234"]
        validation_request = ValidateBidRequest(bidIdsMustHaveValidEntities=True)
        validation_response = BidValidationResponse(valid=True)
        bids = MultipleBidsResponseData(found=[
            BidsResponseData(
                id="1234",
                type=BidManagerCampaignType.PLA.lower(),
                bids=[Bid(id="4011", bid_amount=0.1)])
        ])
        expected_result = ValidatedBidIdentifiers(valid=[
            BidIdentifier(upc='4011', entity_id='4321', bid_group_id='1234')
        ])
        self.mock_bid_manager_gateway.validate_bid.return_value = validation_response
        self.mock_bid_manager_gateway.get_bids.return_value = bids
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = ['4321']

        result = await self.bid_manager_service.validate_bid_entities(
            bid_group_ids,
            validation_request,
            InternalCampaignType.PLA
        )

        self.assertEqual(expected_result, result)
        self.mock_bid_manager_gateway.validate_bid.assert_called_with(bid_group_ids[0], validation_request)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(bid_group_ids)
        self.mock_lookup.get_product_short_id_by_upc_batch.assert_called_with(['4011'])

    async def test_validate_bid_entities__includes_bids_with_lowercase_carousel_types(self):
        bid_group_ids = ["1234"]
        validation_request = ValidateBidRequest(bidIdsMustHaveValidEntities=True)
        validation_response = BidValidationResponse(valid=True)
        bids = MultipleBidsResponseData(found=[
            BidsResponseData(
                id="1234",
                type=BidManagerCampaignType.CAROUSEL.lower(),
                bids=[Bid(id="4011", bid_amount=0.1)])
        ])
        expected_result = ValidatedBidIdentifiers(valid=[
            BidIdentifier(upc='4011', entity_id='4321', bid_group_id='1234')
        ])
        self.mock_bid_manager_gateway.validate_bid.return_value = validation_response
        self.mock_bid_manager_gateway.get_bids.return_value = bids
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = ['4321']

        result = await self.bid_manager_service.validate_bid_entities(
            bid_group_ids,
            validation_request,
            InternalCampaignType.CAROUSEL
        )

        self.assertEqual(expected_result, result)
        self.mock_bid_manager_gateway.validate_bid.assert_called_with(bid_group_ids[0], validation_request)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(bid_group_ids)
        self.mock_lookup.get_product_short_id_by_upc_batch.assert_called_with(['4011'])

    async def test_validate_bid_entities__partitions_valid_and_invalid_entities(self):
        bid_group_ids = ["1234", "2345"]
        validation_request = ValidateBidRequest(bidIdsMustHaveValidEntities=True)
        validation_response_1 = BidValidationResponse(valid=True)
        validation_response_2 = BidValidationResponse(valid=False, invalid_upcs=["4011"])
        bids = MultipleBidsResponseData(found=[
            BidsResponseData(
                id="1234",
                type=BidManagerCampaignType.PLA,
                bids=[
                    Bid(id="4012", bid_amount=0.1),
                    Bid(id="4013", bid_amount=0.1)
                ]),
            BidsResponseData(
                id="2345",
                type=BidManagerCampaignType.PLA,
                bids=[
                    Bid(id="4010", bid_amount=0.1),
                    Bid(id="4011", bid_amount=0.1)
                ])
        ])
        expected_result = ValidatedBidIdentifiers(
            valid=[
                BidIdentifier(upc='4012', entity_id='entity_4012', bid_group_id='1234'),
                BidIdentifier(upc='4013', entity_id='entity_4013', bid_group_id='1234'),
                BidIdentifier(upc='4010', entity_id='entity_4010', bid_group_id='2345'),
                BidIdentifier(upc='4011', entity_id='entity_4011', bid_group_id='2345')],
            invalid=[],
            errors=[]
        )
        self.mock_bid_manager_gateway.validate_bid.side_effect = [
            validation_response_1,
            validation_response_2
        ]
        self.mock_bid_manager_gateway.get_bids.return_value = bids
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = [
            "entity_4012",
            "entity_4013",
            "entity_4010",
            "entity_4011"
        ]

        result = await self.bid_manager_service.validate_bid_entities(
            bid_group_ids,
            validation_request,
            InternalCampaignType.PLA
        )

        self.assertEqual(result, expected_result)
        self.mock_bid_manager_gateway.validate_bid.assert_has_calls([
            call(bid_group_ids[0], validation_request),
            call(bid_group_ids[1], validation_request),
        ])
        self.mock_bid_manager_gateway.get_bids.assert_called_with(bid_group_ids)

        self.mock_lookup.get_product_short_id_by_upc_batch.assert_called_with(["4012", "4013", "4010", "4011"])

    async def test_validate_bid_entities__handles_missing_entity_ids(self):
        bid_group_ids = ["1234"]
        validation_request = ValidateBidRequest(bidIdsMustHaveValidEntities=True)
        validation_response = BidValidationResponse(valid=True)
        bids_response = MultipleBidsResponseData(found=[
            BidsResponseData(
                id="bid-group-id",
                type=BidManagerCampaignType.PLA,
                bids=[
                    Bid(id="4011", bid_amount=0.1),
                    Bid(id="4012", bid_amount=0.1),
                ],
                default_bid=1.0
            )
        ])
        self.mock_bid_manager_gateway.validate_bid.return_value = validation_response
        self.mock_bid_manager_gateway.get_bids.return_value = bids_response
        self.mock_lookup.get_product_short_id_by_upc_batch.side_effect = [
            [1234, None],
            [1234, 2345]
        ]
        expected_result = ValidatedBidIdentifiers(
            valid=[
                BidIdentifier(upc='4011', entity_id='1234', bid_group_id='bid-group-id'),
                BidIdentifier(upc='4012', entity_id='2345', bid_group_id='bid-group-id')],
            invalid=[],
            errors=[]
        )

        result = await self.bid_manager_service.validate_bid_entities(
            bid_group_ids,
            validation_request,
            InternalCampaignType.PLA
        )

        self.assertTrue(result.valid)
        self.assertEqual(result, expected_result)
        self.mock_lookup.set_product_short_ids_by_upcs.assert_called_with(["4012"])

    def test_combine_bid_validations__combines_bids(self):
        def assert_combined(key: str, current_val, next_val, expected):
            current_validation = ValidateBidRequest()
            next_validation = ValidateBidRequest()
            setattr(current_validation, key, current_val)
            setattr(next_validation, key, next_val)
            self.bid_manager_service.combine_bid_validations(current_validation, next_validation)
            combined_val = getattr(current_validation, key)
            self.assertEqual(combined_val, expected)

        assert_combined("minimumBidAmount", None, 1.0, 1.0)
        assert_combined("minimumBidAmount", 0.5, 1.0, 1.0)
        assert_combined("minimumBidAmount", 1.0, 0.5, 1.0)
        assert_combined("maximumBidAmount", None, 1.0, 1.0)
        assert_combined("maximumBidAmount", 0.5, 1.0, 0.5)
        assert_combined("maximumBidAmount", 1.0, 0.5, 0.5)
        assert_combined("minimumBidCount", None, 1, 1)
        assert_combined("minimumBidCount", 0, 1, 1)
        assert_combined("minimumBidCount", 1, 0, 1)
        assert_combined("maximumBidCount", None, 32, 32)
        assert_combined("maximumBidCount", 24, 32, 24)
        assert_combined("maximumBidCount", 32, 24, 24)

    def test_build_validation_request__builds_request(self):
        activation = deepcopy(UPDATED_ACTIVATION_RESPONSE_JSON)
        activation_model = ActivationResponse(**activation["data"])
        expected_validation_request = ValidateBidRequest(
            bidIdsMustHaveValidEntities=True,
            minimumBidAmount=0.5,
            maximumBidAmount=50,
            brandCodes=None
        )

        validation_request = self.bid_manager_service.build_validation_request(activation_model)

        self.assertEqual(validation_request, expected_validation_request)

    @patch('logging.Logger.warning')
    def test_build_validation_request__logs_invalid_placements(self, mock_logger_warning):
        activation = deepcopy(UPDATED_ACTIVATION_RESPONSE_JSON)
        activation_model = ActivationResponse(**activation["data"])
        unknown_placement = "Unknown Placement Type"
        activation["data"]['channel_data']['placementType'].append(unknown_placement)
        expected_validation_request = ValidateBidRequest(
            bidIdsMustHaveValidEntities=True,
            minimumBidAmount=0.5,
            maximumBidAmount=50
        )

        validation_request = self.bid_manager_service.build_validation_request(activation_model)

        self.assertEqual(validation_request, expected_validation_request)
        mock_logger_warning.assert_called_with(
            "Bid range not found for campaign type: %s, placement type: %s",
            "PLA",
            unknown_placement
        )

    async def test_get_valid_entries__filters_invalid_entries(self):
        activation = deepcopy(UPDATED_ACTIVATION_RESPONSE_JSON)
        activation_model = ActivationResponse(**activation["data"])
        bid_group_ids = activation['data']['channel_data']['biddableEntities']
        campaign_type = activation['data']['channel_config']['type']
        get_bids_response = MultipleBidsResponseData(
            found=[
                BidsResponseData(
                    id=bid_group_id,
                    type=campaign_type,
                    bids=[
                        Bid(id="4011", bid_amount=0.6),
                        Bid(id="4012", bid_amount=0.6)
                    ],
                    default_bid=0.5
                )
                for bid_group_id in bid_group_ids
            ]
        )
        validation_response =BidValidationResponse(valid=False, invalid_upcs=["4012"])
        expected_entities = [
            Entity(
                id=804011,
                useBaseBid=False,
                bidAmount=0.6,
                deleted=False
            ),
            Entity(
                id=804012,
                useBaseBid=False,
                bidAmount=0.6,
                deleted=False
            )
        ]
        self.mock_bid_manager_gateway.get_bids.return_value = get_bids_response
        self.mock_bid_manager_gateway.validate_bid.return_value = validation_response
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value =["804011", "804012"]
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [
            CachedProduct(**{"upc": "4011"}),
            CachedProduct(**{"upc": "4012"})
        ]
        self.mock_redis.mget.side_effect = [["804011", "804012"]]

        result = await self.bid_manager_service.get_valid_entries(activation_model)
        result_entities = result.filtered_entities
        result_default_bid = result.default_bid

        self.assertEqual(result_entities, expected_entities)
        self.assertEqual(result_default_bid, 0.5)

    async def test_validate_bid__returns_true_if_valid(self):
        bid_group_id="1234"
        validate_bid_request = ValidateBidRequest()
        mock_validation_response = BidValidationResponse(valid=True)
        self.mock_bid_manager_gateway.validate_bid.return_value = mock_validation_response

        result = await self.bid_manager_service.validate_bid(
            bid_group_id=bid_group_id,
            validate_bid_request=validate_bid_request
        )

        self.assertEqual([], result)
        self.mock_bid_manager_gateway.validate_bid.assert_called_with(bid_group_id, validate_bid_request)

    async def test_validate_bid__raises_entity_validation_errors_if_invalid(self):
        bid_group_id="1234"
        validate_bid_request = ValidateBidRequest(
            minimumBidAmount=0.5,
            maximumBidAmount=50,
            bidIdsMustHaveValidEntities=True
        )
        mock_validation_response = BidValidationResponse(
            valid=False,
            errors=[
                IncorrectBidAmountFailure(
                    bidFailures=[BidFailure(field="bidAmount", message="1234 - Bid amount is not defined.")]
                ),
                EmptyBid(
                    bidFailure=BidFailure(field="UPC", message="No UPCs Exist")
                ),
                IncorrectBids(
                    bidFailureList=[BidFailure(field="UPC", message="2345 - Invalid UPC")]
                ),
                IncorrectMaxBid(
                    bidFailureList=[BidFailure(
                        field="Bid Amount",
                        message="3456 - Bid amount is greater than max bid amount."
                    )]
                ),
                IncorrectMinBid(
                    bidFailureList=[BidFailure(
                        field="Bid Amount",
                        message="4567 - Bid amount is less than min bid amount."
                    )]
                )
            ]
        )
        expected_errors = [
            BidEntityFailure(
                field='bidAmount',
                message='1 - Bid amount is not defined.',
                entity_id='1'
            ),
            BidEntityFailure(
                field='UPC',
                message='No UPCs Exist',
                entity_id=None
            ),
            BidEntityFailure(
                field='UPC',
                message='2 - Invalid UPC',
                entity_id='2'
            ),
            BidEntityFailure(
                field='Bid Amount',
                message='3 - Bid amount is greater than max bid amount.',
                entity_id='3'
            ),
            BidEntityFailure(
                field='Bid Amount',
                message='4 - Bid amount is less than min bid amount.',
                entity_id='4'
            )
        ]
        self.mock_bid_manager_gateway.validate_bid.return_value = mock_validation_response
        self.mock_redis.mget.return_value = ["1", "2", "3", "4"]

        result = await self.bid_manager_service.validate_bid(
            bid_group_id=bid_group_id,
            validate_bid_request=validate_bid_request
        )

        self.assertEqual(expected_errors, result)

    async def test_validate_bid__returns_empty_list_if_no_errors(self):
        bid_group_id = "1234"
        validate_bid_request = ValidateBidRequest()
        mock_validation_response = BidValidationResponse(valid=False)
        self.mock_bid_manager_gateway.validate_bid.return_value = mock_validation_response

        result = await self.bid_manager_service.validate_bid(
            bid_group_id=bid_group_id,
            validate_bid_request=validate_bid_request
        )

        self.assertEqual([], result)

    async def test_get_suggestions__calls_gateway(self):
        koddi_advertiser_id = 1234
        upcs = ["UPC1", "UPC2"]
        type = InternalCampaignType.PLA
        expected_response = SuggestionsResponse()
        self.mock_bid_manager_gateway.get_suggestions_response.return_value = expected_response

        response = await self.bid_manager_service.get_suggestions(koddi_advertiser_id, upcs, type)

        self.mock_bid_manager_gateway.get_suggestions_response.assert_called_with(koddi_advertiser_id, upcs, type)
        self.assertEqual(expected_response, response)

    async def test_create_bids_from_entities__returns_none_if_there_are_no_entities(self):
        base_bid = 0.1


        result = await self.bid_manager_service.create_bids_from_entities(
                entities=[],
                campaign_type=InternalCampaignType.PLA,
                base_bid=base_bid,
            )

        self.assertIsNone(result)

    async def test_create_bids_from_entities__raises_if_there_are_no_valid_entities(self):
        mock_activation = MagicMock()
        mock_channel_config = MagicMock(spec=ChannelConfig, type=InternalCampaignType.PLA)
        mock_activation.channel_config = mock_channel_config
        mock_activation_response = MagicMock()
        mock_activation_response.data = mock_activation
        entities = self.__mock_entities()
        base_bid = 0.1
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [None]

        with self.assertRaises(HTTPException) as context:
            await self.bid_manager_service.create_bids_from_entities(
                entities=entities,
                campaign_type=InternalCampaignType.PLA,
                base_bid=base_bid,
            )

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "No valid products selected to create bids.",
            context.exception.detail
        )

    @pytest.mark.asyncio
    async def test_create_bids_from_entities__creates_bid_group(self):
        mock_activation = MagicMock()
        mock_activation.channel_config = MagicMock()
        mock_activation.channel_config.type = InternalCampaignType.PLA
        mock_activation_response = MagicMock()
        mock_activation_response.data = mock_activation
        entities = self.__mock_entities()
        base_bid = 0.1
        bid_group_id = "bid_group_id"
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [CachedProduct(**{"upc": "4011"})]
        self.mock_bid_manager_gateway.create_bids.return_value = bid_group_id

        result = await self.bid_manager_service.create_bids_from_entities(
                entities=entities,
                campaign_type=InternalCampaignType.PLA,
                base_bid=base_bid,
            )

        self.assertEqual(bid_group_id, result)
        self.mock_bid_manager_gateway.create_bids.assert_called_with(
            CreateBidsRequest(
                type=InternalCampaignType.PLA,
                default_bid=base_bid,
                bids=[Bid(id="4011", bid_amount=0.2)],
            ),
            enforce_validation=True,
        )

    async def test_create_bids_from_entities__updates_carousel_bids(self):
        mock_activation_response = self.__mock_activation_response(
            data={
                "channel_config":{"type": InternalCampaignType.CAROUSEL}
            }
        )
        entities = self.__mock_entities()
        entities.extend(self.__mock_entities())
        base_bid = 0.1
        bid_group_id = "bid_group_id"
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [
            CachedProduct(**{"upc": "4011"}),
            CachedProduct(**{"upc": "4012"})
        ]
        self.mock_bid_manager_gateway.create_bids.return_value = bid_group_id

        result = await self.bid_manager_service.create_bids_from_entities(
                entities=entities,
                campaign_type=InternalCampaignType.CAROUSEL,
                base_bid=base_bid,
            )

        self.assertEqual(bid_group_id, result)
        self.mock_bid_manager_gateway.create_bids.assert_called_with(
            CreateBidsRequest(
                type=InternalCampaignType.CAROUSEL,
                default_bid=base_bid,
                bids=[
                    Bid(id="4011", bid_amount=base_bid, additionalProperties={"order": "0"}),
                    Bid(id="4012", bid_amount=base_bid, additionalProperties={"order": "1"})
                ],
            ),
            enforce_validation=True,
        )

    async def test_update_entities__defaults_base_bid_to_zero_if_there_is_no_bid_group(self):
        mock_activation_response = self.__mock_activation_response(
            channel_config={"type", InternalCampaignType.PLA},
            channel_data={"biddableEntities": None}
        )
        entities_request = EntitiesRequest(
            entities=self.__mock_entities(),
        )
        expected_bid_request = CreateBidsRequest(
            type=InternalCampaignType.PLA,
            default_bid=0,
            bids=[Bid(id="4011", bid_amount=0.2)],
        )
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData()
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [CachedProduct(**{"upc": "4011"})]

        await self.bid_manager_service.update_entities(
            mock_activation_response,
            entities_request
        )

        self.mock_bid_manager_gateway.create_bids.assert_called_with(
            expected_bid_request,
            enforce_validation=True
        )

    async def test_update_entities__uses_requested_base_bid_if_it_exists(self):
        current_bid_group_id = "current_bid_group_id"
        mock_activation_response = self.__mock_activation_response(
            data={
                "channel_config": {"type": InternalCampaignType.PLA.value},
                "channel_data": {"biddableEntities": current_bid_group_id}
            }
        )
        entities_request = EntitiesRequest(
            baseBid=0.1,
            entities=self.__mock_entities(),
        )
        expected_bid_request = CreateBidsRequest(
            type=InternalCampaignType.PLA,
            default_bid=0.1,
            bids=[Bid(id="4011", bid_amount=0.2)],
        )
        bid_group_id = "bid_group_id"
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[BidsResponseData(
                id="1234",
                type=InternalCampaignType.PLA,
                bids=[Bid(id="4011", bid_amount=0.1)],
                default_bid=0.1
            )]
        )
        self.mock_lookup.get_product_details_by_short_id_batch.return_value = [CachedProduct(**{"upc": "4011"})]
        self.mock_lookup.get_product_short_id_by_upc_batch.return_value = [1234]
        self.mock_bid_manager_gateway.create_bids.return_value = bid_group_id

        result = await self.bid_manager_service.update_entities(
            mock_activation_response,
            entities_request
        )

        self.assertEqual(bid_group_id, result)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(
            current_bid_group_id
        )
        self.mock_lookup.get_product_details_by_short_id_batch.assert_called_with(
            [1234]
        )
        self.mock_bid_manager_gateway.create_bids.assert_called_with(
            expected_bid_request,
            enforce_validation=True
        )

    async def test_merge_entities__merges_entity_lists(self):
        use_base_bid = self.bid_manager_service.merge_entities(
            [Entity(id=1234, bidAmount=0.1, useBaseBid=False, deleted=False)],
            [Entity(id=1234, bidAmount=0.1, useBaseBid=True, deleted=False)],
            0.2
        )
        delete_bid = self.bid_manager_service.merge_entities(
            [
                Entity(id=1234, bidAmount=0.1, useBaseBid=False, deleted=False),
                Entity(id=2345, bidAmount=0.1, useBaseBid=False, deleted=False)
            ],
            [
                Entity(id=1234, bidAmount=0.1, useBaseBid=False, deleted=True)
            ],
            0.2
        )
        update_bid = self.bid_manager_service.merge_entities(
            [Entity(id=1234, bidAmount=0.1, useBaseBid=False, deleted=False)],
            [Entity(id=1234, bidAmount=0.3, useBaseBid=False, deleted=False)],
            0.2
        )
        add_bid = self.bid_manager_service.merge_entities(
            [Entity(id=2345, bidAmount=0.1, useBaseBid=False, deleted=False)],
            [Entity(id=1234, bidAmount=0.1, useBaseBid=False, deleted=False)],
            0.2
        )

        self.assertEqual(0.2, use_base_bid[0].bidAmount)
        self.assertEqual(1, len(delete_bid))
        self.assertEqual(2345, delete_bid[0].id)
        self.assertEqual(0.3, update_bid[0].bidAmount)
        self.assertEqual(2, len(add_bid))
        self.assertEqual(2345, add_bid[0].id)
        self.assertEqual(1234, add_bid[1].id)

    async def test_get_entities_by_bid_group_id__filters_bid_groups(self):
        biddable_entity_ids = ["1234"]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[BidsResponseData(
                id="1234",
                type=BidManagerCampaignType.TOA,
                bids=[Bid(id="4011", bid_amount=0.1)],
                default_bid=0.1
            )]
        )

        result = await self.bid_manager_service.get_upcs_by_bid_group_id(
            biddable_entity_ids,
            InternalCampaignType.PLA
        )

        self.assertEqual(result, [])
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)

    async def test_get_entities_by_bid_group_id__aggregates_entities_for_each_bid_group(self):
        biddable_entity_ids = ["1234", "2345"]
        expected_entities = [
            "4011", "4012"
        ]
        self.mock_bid_manager_gateway.get_bids.return_value = MultipleBidsResponseData(
            found=[
                BidsResponseData(
                    id="1234",
                    type=BidManagerCampaignType.PLA,
                    bids=[Bid(id="4011", bid_amount=0.2)],
                    default_bid=0.1
                ),
                BidsResponseData(
                    id="2345",
                    type=BidManagerCampaignType.PLA,
                    bids=[Bid(id="4012", bid_amount=0.1)],
                    default_bid=0.1
                ),
            ]
        )

        result = await self.bid_manager_service.get_upcs_by_bid_group_id(
            biddable_entity_ids,
            InternalCampaignType.PLA
        )

        self.assertEqual(expected_entities, result)
        self.mock_bid_manager_gateway.get_bids.assert_called_with(biddable_entity_ids)

    async def test_bind_missing_products__stores_missing_products(self):
        bid_data_by_upc = {
            "4011": BidData(
                bid=Bid(id="4011", bid_amount=0.1),
                entity_id=1234,
                product=None
            )
        }
        product = Product(
            upc="4011",
            description="Bananas",
            isValid=True,
            brand="Dole",
            quantity="1",
            taxonomy=Taxonomy(
                department=TaxonomyProperties(id="1234", name="name"),
                commodity=TaxonomyProperties(id="1234", name="name"),
                subCommodity=TaxonomyProperties(id="1234", name="name")
            ),
            restrictions=None,
            lastSoldDate="2025-07-02"
        )
        expected_products_to_cache = {
            1234: CachedProduct(**product.model_dump())
        }
        self.mock_product_gateway.get_products_by_upcs.return_value = SingleDataResponse[ProductSearchResponse, ProductManagerMeta](
            data=ProductSearchResponse(
                validProducts=[product],
                invalidProducts=[]
            ),
            meta=ProductManagerMeta(
                page=ProductManagerMetaPage(
                    offset=0,
                    size=10,
                    totalSize=1
                )
            )
        )

        await self.bid_manager_service.bind_missing_products(bid_data_by_upc)

        self.mock_lookup.set_product_details_by_short_id_batch.assert_called_with(expected_products_to_cache)
