from typing import Callable, List, Tuple

from fastapi import Depends, HTTPException

from app.common.gateways.product_gateway import ProductGateway
from app.common.model.redis import CachedProduct
from app.common.services.lookup_service import LookupService
from app.common.view_models import EntitiesRequest, Entity, CreateEntitiesRequest
from app.common.database.async_client import AsyncRedisClientService, RedisKeyTypes
from app.common.gateways.bid_manager_gateway import BidManagerGateway
from app.v2.model.downstream.activation_service import (
    ActivationResponse,
    ActivationResponseV2,
)
from app.common.model.downstream.bid_manager import (
    Bid,
    BidEntityFailure,
    BidFailure,
    BidIdentifier,
    BidsResponseData,
    BidValidationFailure,
    CreateBidsRequest,
    SuggestionsResponse,
    ValidateBidRequest,
    ValidatedBidIdentifiers, ValidationResponse, BidData,
)
from app.common.model.campaign_types import InternalCampaignType
from app.common.utils import filtered_logger
from app.common.utils.bid_ranges import get_bid_ranges

logger = filtered_logger.get_logger(__name__)

class BidManagerService:
    redis_cache: AsyncRedisClientService
    __bid_manager_gateway: BidManagerGateway
    lookup: LookupService
    product_gateway: ProductGateway

    def __init__(
            self,
            redis_cache: AsyncRedisClientService = Depends(AsyncRedisClientService),
            bid_manager_gateway: BidManagerGateway = Depends(BidManagerGateway),
            lookup: LookupService = Depends(LookupService),
            product_gateway: ProductGateway = Depends(ProductGateway),
    ):
        self.redis_cache = redis_cache
        self.__bid_manager_gateway = bid_manager_gateway
        self.lookup = lookup
        self.product_gateway = product_gateway

    async def build_pla_create_bids_request_from_entities(
            self,
            entities: List[Entity],
            base_bid: float
    ) -> CreateBidsRequest:
        bids = []

        entity_ids = [entity.id for entity in entities]
        products = await self.lookup.get_product_details_by_short_id_batch(entity_ids)
        for index, entity in enumerate(entities):
            cached_product = products[index]
            if not cached_product:
                logger.warning("Product ID not found in cache [create]: %s", entity.id)
                continue

            product = cached_product
            bid_amount = base_bid\
                if entity.bidAmount is None or entity.useBaseBid\
                else entity.bidAmount
            bids.append(Bid(
                id=product.upc,
                bid_amount=bid_amount
            ))

        return CreateBidsRequest(
            type=InternalCampaignType.PLA,
            default_bid=base_bid,
            bids=bids
        )

    async def create_pla_bids_from_entities(
            self,
            entities: List[Entity],
            base_bid: float
    ) -> str:
        bids_request = await self.build_pla_create_bids_request_from_entities(entities, base_bid)
        # If no bids are in the list, we need to stop
        # If we send an empty bids list to bid manager, we'll get an error.
        if len(bids_request.bids) == 0:
            raise HTTPException(status_code=400, detail="No valid products selected to create bids.")
        bid_group_id = await self.__bid_manager_gateway.create_bids(bids_request, enforce_validation=True)

        return bid_group_id

    async def create_bids_from_entities(
            self,
            entities: List[Entity],
            campaign_type: InternalCampaignType,
            base_bid: float
    ) -> str | None:
        if not entities:
            return None

        bids_request = await self.build_pla_create_bids_request_from_entities(entities, base_bid)
        bids_request.type = campaign_type or InternalCampaignType.PLA

        if len(bids_request.bids) == 0:
            raise HTTPException(status_code=400, detail="No valid products selected to create bids.")

        if campaign_type == InternalCampaignType.CAROUSEL:
            for index, bid in enumerate(bids_request.bids):
                bid.additionalProperties = {"order": str(index)}
                bid.bid_amount = base_bid
        bid_group_id = await self.__bid_manager_gateway.create_bids(bids_request, enforce_validation=True)

        return bid_group_id


    async def get_entities(
            self,
            biddable_entity_ids: List[str],
            campaign_type: InternalCampaignType,
    ) -> Tuple[List[Entity], float]:
        entities = []
        default_bid = 0.0
        if not biddable_entity_ids:
            return entities, default_bid

        bids_response = await self.__bid_manager_gateway.get_bids(biddable_entity_ids)
        for bid_group in bids_response.found:
            if bid_group.type != campaign_type:
                continue
            if not default_bid:
                # This is incorrect, but matches our current implementation for recommendations
                default_bid = bid_group.default_bid
            entities.extend(await self.__bid_group_to_entities(bid_group))

        return entities, default_bid

    async def get_upcs_by_bid_group_id(
            self,
            biddable_entity_ids: List[str],
            campaign_type: InternalCampaignType
    ) -> List[str]:
        entities = []
        if not biddable_entity_ids:
            return entities

        bids_response = await self.__bid_manager_gateway.get_bids(biddable_entity_ids)
        for bid_group in bids_response.found:
            if bid_group.type != campaign_type:
                continue
            entities.extend([bid.id for bid in bid_group.bids])

        return entities

    async def __bid_group_to_entities(self, bid_group: BidsResponseData | None) -> List[Entity]:
        if bid_group is None:
            return []

        bid_entity_ids = await self.bind_bids_to_entity_ids(bid_group.bids)

        return [
            Entity(
                id=entity_id,
                useBaseBid=bid.bid_amount == bid_group.default_bid,
                bidAmount=bid.bid_amount,
                deleted=False,
            )
            for bid, entity_id in bid_entity_ids
        ]

    async def bind_bids_to_entity_ids(self, bids: List[Bid]) -> list[tuple[Bid, int]]:
        """
        Make sure the bids have:
            upc -> entity id in redis
            entity id -> product string in redis
            return the list of entity ids
        """
        upcs = [bid.id for bid in bids]
        entity_ids = await self.lookup.get_product_short_id_by_upc_batch(upcs)
        cached_products = await self.lookup.get_product_details_by_short_id_batch(entity_ids)
        bid_data_by_upc = {
            bid.id: BidData(bid=bid, entity_id=entity_id, product=product.model_dump_json() if product else None)
            for bid, entity_id, product in zip(bids, entity_ids, cached_products)
        }
        await self.bind_missing_entity_ids(bid_data_by_upc)
        await self.bind_missing_products(bid_data_by_upc)

        bid_entity_ids = []
        for bid in bids:
            bid_data = bid_data_by_upc.get(bid.id)
            bid_entity_ids.append((
                bid,
                bid_data.entity_id if bid_data else None,
            ))

        return bid_entity_ids

    async def bind_missing_entity_ids(self, bid_data_by_upc: dict[str, BidData]):
        """
        1. Finds missing entity ids in the bid data
        2. Generates new UPC -> entity id mapping
        3. Saves the new entity id in the bid_data_by_upc dict
        """
        upcs_missing_entity_id = [
            upc
            for upc, bid_data in bid_data_by_upc.items()
            if bid_data.entity_id is None
        ]

        if not upcs_missing_entity_id:
            return

        generated_entity_ids = await self.lookup.set_product_short_ids_by_upcs(upcs_missing_entity_id)
        for upc, entity_id in zip(upcs_missing_entity_id, generated_entity_ids):
            bid_data = bid_data_by_upc.get(upc)
            bid_data.entity_id = entity_id

    async def bind_missing_products(self, bid_data_by_upc: dict[str, BidData]):
        """
        1. Finds missing products in the bid data
        2. Fetches missing products
        3. Creates a new entity id -> product mapping
        """
        upcs_missing_cached_product = [
            (upc, bid_data.entity_id)
            for upc, bid_data in bid_data_by_upc.items()
            if bid_data.product is None
        ]
        if not upcs_missing_cached_product:
            return

        upcs_to_fetch = [upc for upc, _ in upcs_missing_cached_product]
        products_response = await self.product_gateway.get_products_by_upcs(
            upcs=upcs_to_fetch,
            advertiser_names=None,
            last_sold_within_days=None
        )
        products_by_upc = {
            product.upc: CachedProduct(**product.model_dump())
            for product in products_response.data.validProducts
        }
        products_to_cache = {
            entity_id: products_by_upc.get(upc)
            for upc, entity_id in upcs_missing_cached_product
            if upc in products_by_upc
        }
        await self.lookup.set_product_details_by_short_id_batch(products_to_cache)

    async def validate_bid(
            self,
            bid_group_id: str,
            validate_bid_request: ValidateBidRequest,
    ) -> List[BidEntityFailure]:
        validation_response = await self.__bid_manager_gateway.validate_bid(bid_group_id, validate_bid_request)
        if validation_response.valid:
            return []

        entity_errors = await self.__convert_upc_errors_to_entity_errors(validation_response.errors)
        return entity_errors

    async def __convert_upc_errors_to_entity_errors(
            self,
            errors: List[BidValidationFailure]
    ) -> List[BidEntityFailure]:
        if not errors:
            return []

        entity_errors = []
        bid_failures: List[BidFailure] = []
        for error in errors:
            if hasattr(error, "bid_failure_list"):
                bid_failures.extend(error.bid_failure_list)
            if hasattr(error, "bid_failure"):
                bid_failures.append(error.bid_failure)
            if hasattr(error, "bid_failures") and isinstance(error.bid_failures, list):
                bid_failures.extend(error.bid_failures)

        partitioned_failures = [
            (bid_failure.message.partition(" "), bid_failure.field)
            for bid_failure in bid_failures
        ]
        upcs = [
            failure[0][0]
            for failure in partitioned_failures
            if failure[0][0].isdigit()
        ]
        entity_ids = await self.redis_cache.mget(RedisKeyTypes.PRODUCT, upcs)
        entity_id_by_upc = { upc: entity_ids[index] for index, upc in enumerate(upcs) }

        for partitioned_failure in partitioned_failures:
            upc, match, rest = partitioned_failure[0]
            field = partitioned_failure[1]
            if upc.isdigit():
                entity_errors.append(BidEntityFailure(
                    field=field,
                    message=f"{entity_id_by_upc.get(upc, '')}{match}{rest}",
                    entity_id=entity_id_by_upc.get(upc, "")
                ))
            else:
                entity_errors.append(BidEntityFailure(
                    field=field,
                    message=f"{upc}{match}{rest}"
                ))

        return entity_errors


    async def validate_bid_entities(
            self,
            bid_group_ids: List[str],
            validate_bid_request: ValidateBidRequest,
            campaign_type: InternalCampaignType
    ) -> ValidatedBidIdentifiers:
        validated_bid_ids = ValidatedBidIdentifiers()
        invalid_upcs = []

        if not bid_group_ids:
            return validated_bid_ids

        for bid_group_id in bid_group_ids:
            validation_response = await self.__bid_manager_gateway.validate_bid(bid_group_id, validate_bid_request)
            #if validation_response.invalid_upcs:
                #invalid_upcs.extend(validation_response.invalid_upcs)
            validated_bid_ids.errors.extend(validation_response.errors if validation_response.errors else [])

        bids_response = await self.__bid_manager_gateway.get_bids(bid_group_ids)
        bids: List[Tuple[str, str]] = []
        for bid_group in bids_response.found:
            if bid_group.type != campaign_type:
                continue
            for bid in bid_group.bids:
                bids.append((bid_group.id, bid.id))

        bid_ids = [bid_id for bid_group_id, bid_id in bids]
        entity_ids = await self.lookup.get_product_short_id_by_upc_batch(bid_ids)
        upcs_missing_entity_id = [
            bid_id
            for (index, bid_id) in enumerate(bid_ids)
            if entity_ids[index] is None
        ]
        if upcs_missing_entity_id:
            await self.lookup.set_product_short_ids_by_upcs(upcs_missing_entity_id)
            entity_ids = await self.lookup.get_product_short_id_by_upc_batch(bid_ids)

        for index, (bid_group_id, bid_id) in enumerate(bids):
            bid_identifier = BidIdentifier(
                upc=bid_id,
                entity_id=str(entity_ids[index]),
                bid_group_id=bid_group_id,
            )
            if bid_id in invalid_upcs:
                validated_bid_ids.invalid.append(bid_identifier)
            else:
                validated_bid_ids.valid.append(bid_identifier)

        return validated_bid_ids

    async def get_valid_entries(self, activation: ActivationResponse, brand_codes: list[str]=None) -> ValidationResponse:
        bid_group_ids = activation.channel_data.get("biddableEntities", [])
        campaign_type = activation.channel_config.type
        validate_bid_request = self.build_validation_request(activation, True, brand_codes=brand_codes)
        all_entities, default_bid = await self.get_entities(bid_group_ids, campaign_type)
        errors = []
        validated_bid_ids = await self.validate_bid_entities(
            bid_group_ids,
            validate_bid_request,
            campaign_type
        )
        invalid_entity_ids = set([
            int(bid_id.entity_id)
            for bid_id in validated_bid_ids.invalid
            if bid_id.entity_id.isdigit()
        ])
        if validated_bid_ids.errors:
            errors = await self.__convert_upc_errors_to_entity_errors(validated_bid_ids.errors)
        filtered_entities = [entity for entity in all_entities if entity.id not in invalid_entity_ids]
        return ValidationResponse(
            filtered_entities=filtered_entities,
            default_bid=default_bid,
            errors=errors
        )

    async def get_suggestions(
            self,
            koddi_advertiser_id: int,
            upcs: List[str],
            type: InternalCampaignType
    ) -> SuggestionsResponse:
        return await self.__bid_manager_gateway.get_suggestions_response(
            koddi_advertiser_id,
            upcs,
            type
        )

    @staticmethod
    def build_validation_request(
            activation: ActivationResponse = None,
            validate_upcs = True,
            placement_types: List[str] | None = None,
            campaign_type: InternalCampaignType | None = None,
            brand_codes: list[str] | None = None
    ) -> ValidateBidRequest:
        validate_bid_request = ValidateBidRequest(
            bidIdsMustHaveValidEntities=validate_upcs,
            brandCodes=brand_codes
        )
        if not placement_types and not campaign_type:
            campaign_type = activation.channel_config.type
            placement_types: List[str] = activation.channel_data.get("placementType", [])
        bid_ranges_by_campaign_type = get_bid_ranges().get(campaign_type, {})
        for placement_type in placement_types:
            bid_range: ValidateBidRequest | None = bid_ranges_by_campaign_type.get(placement_type, None)
            if bid_range is None:
                logger.warning(
                    "Bid range not found for campaign type: %s, placement type: %s",
                    campaign_type, placement_type)
                continue
            BidManagerService.combine_bid_validations(validate_bid_request, bid_range)

        return validate_bid_request

    @staticmethod
    def combine_bid_validations(current_validation: ValidateBidRequest, next_validation: ValidateBidRequest):
        current_validation.minimumBidAmount = BidManagerService.__compare_values(
            current_validation.minimumBidAmount,
            next_validation.minimumBidAmount,
            max
        )
        current_validation.maximumBidAmount = BidManagerService.__compare_values(
            current_validation.maximumBidAmount,
            next_validation.maximumBidAmount,
            min
        )
        current_validation.minimumBidCount = BidManagerService.__compare_values(
            current_validation.minimumBidCount,
            next_validation.minimumBidCount,
            max
        )
        current_validation.maximumBidCount = BidManagerService.__compare_values(
            current_validation.maximumBidCount,
            next_validation.maximumBidCount,
            min
        )

    @staticmethod
    def __compare_values(
            a: int | float | None,
            b: int | float | None,
            compare_fn: Callable[[int | float, int | float], int | float]
    ) -> int | float | None:
        if a is None:
            return b
        elif b is not None:
            return compare_fn(a, b)

    async def update_entities(
            self,
            activation_response: ActivationResponseV2[ActivationResponse],
            entities_request: EntitiesRequest
    ) -> str | None:
        biddable_entities = activation_response.data.channel_data.get("biddableEntities")
        bid_group: BidsResponseData | None = None
        if biddable_entities:
            bid_group_response = await self.__bid_manager_gateway.get_bids(biddable_entities)
            if bid_group_response.found:
                bid_group = bid_group_response.found[0]

        base_bid = bid_group.default_bid if bid_group else 0
        if entities_request.baseBid is not None:
            base_bid = entities_request.baseBid

        existing_entities = await self.__bid_group_to_entities(bid_group)
        entities = self.merge_entities(
            existing_entities,
            entities_request.entities,
            base_bid
        )

        bid_group_id = await self.create_bids_from_entities(
            entities,
            activation_response.data.channel_config.type,
            base_bid
        )

        return bid_group_id

    @staticmethod
    def merge_entities(
            prev_entities: List[Entity],
            next_entities: List[Entity],
            base_bid: float
    ) -> List[Entity]:
        existing_entities_by_id = {entity.id: entity for entity in prev_entities}
        new_entities = []
        for entity in next_entities:
            existing_entity = existing_entities_by_id.get(entity.id, None)
            if entity.useBaseBid:
                entity.bidAmount = base_bid
            if existing_entity in prev_entities:
                prev_entities.remove(existing_entity)
            if entity.deleted:
                continue
            new_entities.append(entity)

        return prev_entities + new_entities