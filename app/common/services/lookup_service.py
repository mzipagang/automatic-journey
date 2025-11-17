import json
from typing import Dict, List

from fastapi import Depends

from app.common.model.downstream.location_groups import DivisionBannerItem
from app.common.database.async_client import AsyncRedisClientService, RedisKeyTypes
from app.common.model.division import DivisionServiceResponse
from app.common.model.redis import (
    CachedAddress,
    CachedContact,
    CachedPlacement,
    CachedDivision,
    CachedRedisAdvertiser,
    CachedProduct
)
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

class LookupService:
    redis_cache: AsyncRedisClientService

    def __init__(self, redis_cache: AsyncRedisClientService = Depends(AsyncRedisClientService)):
        self.redis_cache = redis_cache

    @staticmethod
    def _str_to_model(
            serialized_json: str | None,
            model: type,
            key: str
    ) -> type | None:
        if serialized_json is None or serialized_json == "null":
            return None
        try:
            json_data = json.loads(serialized_json)
            return model(**json_data)
        except json.decoder.JSONDecodeError:
            logger.error("Invalid json stored at %s", key)
            return None
        except ValueError as error:
            logger.error(
                "Value error converting json stored at %s for model %s: %s",
                key,
                model.__name__,
                str(error)
            )
            return None
        except Exception as error:
            logger.error(
                "Unexpected error converting json stored at %s for model %s: %s",
                key,
                model.__name__,
                str(error)
            )
            return None

    # ---------------------------CAMPAIGNS GET OPERATIONS----------------------------
    async def get_campaign_short_id_by_long_id_batch(
            self,
            campaign_ids: List[str]) -> List[int | None]:
        """
        Given a list of long campaign ids, return all the incremental short ids like
        [short_id, None, short_id] None for all the long ids not found
        """
        cached_campaigns_ids = await self.redis_cache.mget(RedisKeyTypes.CAMPAIGN, campaign_ids)
        return cached_campaigns_ids

    async def get_campaign_short_id_by_long_id(self, long_campaign_id: str) -> int | None:
        """
        Given a long campaign, return its short incremental id
        """
        short_campaign_id = await self.redis_cache.get(RedisKeyTypes.CAMPAIGN, long_campaign_id)
        return short_campaign_id

    async def get_campaign_long_id_by_short_id_batch(self, short_ids: List[str]) -> List[str | None]:
        """
        Given a list of short campaign (not incremental) ids, return all long campaign ids
        saved like [long_id, None, long_id] None for all the short ids not found
        """
        long_campaigns_ids = await self.redis_cache.mget(RedisKeyTypes.CAMPAIGN, short_ids)
        return long_campaigns_ids

    async def get_campaign_long_id_by_short_id(self, short_campaign_id: int) -> str | None:
        """
        Return the long campaign id given the incremental short id.
        """
        return await self.redis_cache.get(RedisKeyTypes.CAMPAIGN, short_campaign_id)

    async def get_campaign_long_id_by_internal_short_id(self, short_campaign_id: int) -> str | None:
        """
        Return the long campaign id given the short campaign (not incremental) id.
        """
        return await self.redis_cache.get(RedisKeyTypes.CAMPAIGN, short_campaign_id)

    async def get_campaign_long_id_by_short_adgroup_id(self, short_adgroup_id: int) -> str | None:
        """
        Return the long campaign id given the short adgroup id.
        """
        campaign_key = f"{RedisKeyTypes.CAMPAIGN}:{short_adgroup_id}"
        return await self.redis_cache.get(RedisKeyTypes.AD_GROUP, campaign_key)

    async def get_campaign_key_exists(self, key: str) -> bool:
        """
        Return whether key exists for campaign or not.
        """
        return await self.redis_cache.exists(RedisKeyTypes.CAMPAIGN, key)

    async def get_koddi_campaign_id_by_short_id_batch(self, short_ids: List[str]) -> List[str | None]:
        """
        Given a list of short campaign ids, return all the koddi campaign ids.
        """
        koddi_keys = [f'KODDI:{short_id}' for short_id in short_ids]
        koddi_campaigns_ids = await self.redis_cache.mget(RedisKeyTypes.CAMPAIGN, koddi_keys)
        return koddi_campaigns_ids

    async def get_campaign_long_id_by_koddi_id_batch(self, koddi_ids: List[int]) -> List[str | None]:
        """
        Given a list of koddi campaign ids, return all the long campaign ids.
        """
        return await self.redis_cache.mget(RedisKeyTypes.CAMPAIGN_KODDI, koddi_ids)

    # --------------------------- END CAMPAIGNS GET OPERATIONS----------------------------

    # ---------------------------CONTACT GET OPERATIONS----------------------------
    async def get_contact_short_id_by_long_id(self, long_contact_id: str) -> int | None:
        """
        Given a long contact id, return its short incremental id
        """
        short_contact_id = await self.redis_cache.get(RedisKeyTypes.CONTACT, long_contact_id)
        return short_contact_id

    async def get_contact_short_id_by_long_id_batch(self, long_contact_ids: List[str]) -> List[int | None]:
        """
        Given a long contact id, return its short incremental id
        """
        short_contact_ids = await self.redis_cache.mget(RedisKeyTypes.CONTACT, long_contact_ids)
        return short_contact_ids

    async def get_contact_details_by_short_id(self, short_contact_id: int) -> CachedContact | None:
        """
        Given a short incremental contact id, return its info
        """
        contact_details = await self.redis_cache.get(RedisKeyTypes.CONTACT, short_contact_id)
        return self._str_to_model(
            contact_details,
            CachedContact,
            f"{RedisKeyTypes.CONTACT}:{short_contact_id}"
        )

    async def get_contact_details_by_short_id_batch(self, short_ids: List[int]) -> List[CachedContact | None] | None:
        """
        Given an incremental short id list, return the contact details.
        """
        contact_details_batch = await self.redis_cache.mget(RedisKeyTypes.CONTACT, short_ids)
        if contact_details_batch is not None:
            return [self._str_to_model(contact, CachedContact,f"{RedisKeyTypes.CONTACT}:{short_id}")
                for contact, short_id in zip(contact_details_batch, short_ids)]

    # --------------------------- END CONTACT GET OPERATIONS----------------------------

    # ---------------------------ADDRESS GET OPERATIONS----------------------------
    async def get_address_short_id_by_long_id(self, long_address_id: str) -> int | None:
        """
        Given a long address id, return its short incremental id
        """
        short_address_id = await self.redis_cache.get(RedisKeyTypes.ADDRESS, long_address_id)
        return short_address_id

    async def get_address_short_id_by_long_id_batch(self, long_address_ids: List[str]) -> List[int | None]:
        """
        Given long address ids, return their short incremental ids
        """
        short_address_ids = await self.redis_cache.mget(RedisKeyTypes.ADDRESS, long_address_ids)
        return short_address_ids

    async def get_address_details_by_short_id(self, short_id: int) -> CachedAddress | None:
        """
        Given an incremental short address id, return its data
        """
        address_data = await self.redis_cache.get(RedisKeyTypes.ADDRESS, short_id)
        return self._str_to_model(
            address_data,
            CachedAddress,
            f"{RedisKeyTypes.ADDRESS}:{short_id}"
        )

    async def get_address_long_id_by_account_long_id(self, long_account_id: str) -> str | None:
        """
        Given a long account id, return the associated long address id.
        """
        long_address_id = await self.redis_cache.get(RedisKeyTypes.ADDRESS, long_account_id)
        return long_address_id

    # --------------------------- END ADDRESS GET OPERATIONS----------------------------

    # --------------------------- ACCOUNTS GET OPERATIONS----------------------------

    async def get_account_short_id_by_long_id(self, long_account_id: str) -> int | None:
        """
        Given a long account client id, return its short incremental id
        """
        short_account_id = await self.redis_cache.get(RedisKeyTypes.ACCOUNT, long_account_id)
        return short_account_id

    async def get_account_long_id_by_short_id(self, short_account_id: int) -> str | None:
        """
        Given an incremental short account id, return its long client id
        """
        long_account_id = await self.redis_cache.get(RedisKeyTypes.ACCOUNT, short_account_id)
        return long_account_id

    async def get_account_short_id_by_long_id_batch(self, long_account_ids: List[str]) -> List[int | None]:
        """
        Given a long account client id, return its short incremental id
        """
        short_account_ids = await self.redis_cache.mget(RedisKeyTypes.ACCOUNT, long_account_ids)
        return short_account_ids

    # --------------------------- END ACCOUNTS GET OPERATIONS----------------------------

    # --------------------------- ADGROUP GET OPERATIONS---------------------------------

    async def get_adgroup_short_id_by_long_id(self, long_activation_id: str) -> int | None:
        """
        Given a long ad group (activation id), return its short incremental id
        """
        short_activation_id = await self.redis_cache.get(RedisKeyTypes.AD_GROUP, long_activation_id)
        return short_activation_id

    async def get_adgroup_long_id_by_short_id(self, short_id: int) -> str | None:
        """
        Given short incremental id, return its long ad group (activation id)
        """
        long_activation_id = await self.redis_cache.get(RedisKeyTypes.AD_GROUP, short_id)
        return long_activation_id

    async def get_adgroup_short_id_by_long_id_batch(self, long_ids: list[str]) -> list[int | None]:
        """
        Given a list of long ad group ids, return the short ad group ids
        """
        short_ad_group_ids = await self.redis_cache.mget(RedisKeyTypes.AD_GROUP, long_ids)

        return [
            int(short_id) if short_id and short_id.isdigit() else None
            for short_id in short_ad_group_ids
        ]

    async def get_adgroup_long_id_by_short_id_batch(self, short_ids: list[str]) -> list[str | None]:
        """
        Given a list of long ad group ids, return the short ad group ids
        """
        long_ad_group_ids = await self.redis_cache.mget(RedisKeyTypes.AD_GROUP, short_ids)
        return long_ad_group_ids

    async def get_adgroup_long_id_by_koddi_id_batch(self, koddi_ids: List[int]) -> List[str | None]:
        """
        Given a list of koddi ad group ids, return the long ad group ids.
        """
        return await self.redis_cache.mget(
            RedisKeyTypes.AD_GROUP_KODDI,
            koddi_ids,
        )

    # --------------------------- END ADGROUP GET OPERATIONS----------------------------

    # --------------------------- PRODUCT GET OPERATIONS---------------------------------
    async def get_product_short_id_by_upc(self, upc: str) -> int | None:
        """
        Given a product UPC, return its incremental short id.
        """
        short_product_id = await self.redis_cache.get(RedisKeyTypes.PRODUCT, upc)
        return short_product_id

    async def get_product_details_by_short_id(self, short_id: int) -> CachedProduct | None:
        """
        Given an incremental short id, return the product details.
        """
        product_details = await self.redis_cache.get(RedisKeyTypes.PRODUCT, short_id)
        return self._str_to_model(
            product_details,
            CachedProduct,
            f"{RedisKeyTypes.PRODUCT}:{short_id}"
        )

    async def get_product_details_by_short_id_batch(self, short_ids: List[int]) -> List[CachedProduct | None]:
        """
        Given an incremental short id list, return the products details.
        """
        product_details_batch = await self.redis_cache.mget(RedisKeyTypes.PRODUCT, short_ids)
        return [self._str_to_model(product, CachedProduct, f"{RedisKeyTypes.PRODUCT}:{short_id}")
                for product, short_id in zip(product_details_batch, short_ids)]

    async def get_product_short_id_by_upc_batch(self, upcs: List[str]) -> List[int | None]:
        """
        Given a list of product upc, return their incremental short ids.
        """
        short_product_id_batch = await self.redis_cache.mget(RedisKeyTypes.PRODUCT, upcs)
        return short_product_id_batch

    async def get_product_upcs_by_short_id_batch(self, short_ids: List[int]) -> List[str | None]:
        products = await self.get_product_details_by_short_id_batch(short_ids)
        upcs = []
        for product in products:
            if product is None:
                upcs.append(None)
                continue
            upcs.append(product.upc)

        return upcs

    # --------------------------- END PRODUCT GET OPERATIONS----------------------------

    # --------------------------- ADVERTISER GET OPERATIONS---------------------------------

    async def get_advertiser_short_id_by_long_id(self, long_brand_id: str) -> int | None:
        """
        Given a long advertiser brand id, return its short incremental id.
        """
        short_advertiser_id = await self.redis_cache.get(RedisKeyTypes.ADVERTISER, long_brand_id)
        return short_advertiser_id

    async def get_advertiser_short_id_by_long_id_batch(self, long_brand_ids: list[str]) -> list[int | None]:
        """
        Given a long advertiser brand id list, return its short incremental id list.
        """
        short_advertiser_ids = await self.redis_cache.mget(RedisKeyTypes.ADVERTISER, long_brand_ids)
        return short_advertiser_ids

    async def get_advertiser_details_by_short_id(self, short_id: int) -> CachedRedisAdvertiser | None:
        """
        Given a short incremental advertiser id, return its info.
        """
        data = await self.redis_cache.get(RedisKeyTypes.ADVERTISER, short_id)
        return self._str_to_model(
            data,
            CachedRedisAdvertiser,
            f"{RedisKeyTypes.ADVERTISER}:{short_id}"
        )

    async def get_advertiser_details_by_short_ids(self, short_ids: List[int]) -> List[CachedRedisAdvertiser | None]:
        """
        Given a short incremental advertiser id, return its info.
        """
        data = await self.redis_cache.mget(RedisKeyTypes.ADVERTISER, short_ids)
        return [
            self._str_to_model(
                details,
                CachedRedisAdvertiser,
                f"{RedisKeyTypes.ADVERTISER}:{short_id}"
            ) if details is not None else None
            for details, short_id in zip(data, short_ids)
        ]

    async def get_koddi_advertiser_short_id_by_long_id(self, long_brand_id: str) -> str | None:
        """
        Given a long advertiser brand id, return it short koddi brand id.
        """
        short_advertiser_id = await self.redis_cache.get(RedisKeyTypes.KODDI_ADVERTISER, long_brand_id)
        return short_advertiser_id

    async def get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id(
            self,
            long_brand_id: str,
            long_agency_id: str
    ) -> int | None:
        """
        Given a long advertiser brand id and long agency id, return its short koddi brand id.
        """
        koddi_key = f"{long_brand_id}:{long_agency_id}"
        short_advertiser_id = await self.redis_cache.get(RedisKeyTypes.KODDI_ADVERTISER, koddi_key)
        return short_advertiser_id

    # --------------------------- END ADVERTISER GET OPERATIONS----------------------------

    # --------------------------- DIVISION GET OPERATIONS---------------------------------
    async def get_division_short_id_by_banner_code_and_division_number(
            self,
            banner_code: str,
            division_number: str
    ) -> int | None:
        """
        Given a banner code and division number, return its short id.
        """
        division_key = f"{banner_code}:{division_number}"
        division_id = await self.redis_cache.get(RedisKeyTypes.DIVISION, division_key)
        return division_id

    async def get_division_details_by_short_id(self, short_id: str) -> CachedDivision | None:
        """
        Given a division incremental short id, returns its data.
        """
        division_info = await self.redis_cache.get(RedisKeyTypes.DIVISION, short_id)
        return self._str_to_model(
            division_info,
            CachedDivision,
            f"{RedisKeyTypes.DIVISION}:{short_id}"
        )

    async def get_division_details_by_short_id_batch(self, short_ids: list[int]) -> list[CachedDivision | None]:
        """
        Given a division incremental short id, returns its data.
        """
        division_info = await self.redis_cache.mget(RedisKeyTypes.DIVISION, short_ids)
        return [
            self._str_to_model(
                division,
                CachedDivision,
                f"{RedisKeyTypes.DIVISION}:{short_id}"
            )
            for short_id, division in zip(short_ids, division_info)
        ]

    async def get_division_short_ids_by_division_items(
            self,
            division_items: List[DivisionBannerItem]
    ) -> List[int | None]:
        """
        Given a list of division items, return their short ids.
        """
        division_keys = [f"{item.bannerCode}:{item.divisionNumber}" for item in division_items]
        raw_division_ids = await self.redis_cache.mget(RedisKeyTypes.DIVISION, division_keys)

        return [
            int(division_id) if division_id is not None and division_id.isdigit() else None
            for division_id in raw_division_ids
        ]


    # --------------------------- END DIVISION GET OPERATIONS----------------------------

    # --------------------------- PLACEMENT GET OPERATIONS----------------------------
    async def get_placement_details_by_short_id(self, short_id: int) -> CachedPlacement | None:
        """
        Given a short incremental placement id, return its info.
        """
        placement_info = await self.redis_cache.get(RedisKeyTypes.PLACEMENT, short_id)
        return self._str_to_model(
            placement_info,
            CachedPlacement,
            f"{RedisKeyTypes.PLACEMENT}:{short_id}"
        )

    async def get_placement_short_id_by_id_and_name(self, placement_id: str, placement_name: str) -> int | None:
        """
        Given a placement id and name, return its incremental short id.
        """
        placement_key = f"{placement_id}:{placement_name}"
        short_id = await self.redis_cache.get(RedisKeyTypes.PLACEMENT, placement_key)
        return short_id

    async def get_placement_short_id_by_name(self, placement_name: str) -> int | None:
        """
        Given a placement name, return the incremental short id.
        """
        short_id = await self.redis_cache.get(RedisKeyTypes.PLACEMENT, placement_name)
        return short_id

    async def get_placement_short_ids_by_names(self, placement_names: List[str]) -> List[int | None]:
        """
        Given placement names, return a list of their short ids.
        """
        str_short_ids = await self.redis_cache.mget(RedisKeyTypes.PLACEMENT, placement_names)

        return [
            int(str_short_id) if str_short_id is not None and str_short_id.isdigit() else None
            for str_short_id in str_short_ids
        ]

    # --------------------------- END PLACEMENT GET OPERATIONS----------------------------

    # --------------------------- CAMPAIGN SET OPERATIONS----------------------------

    async def set_campaign_short_id_by_long_id_batch(self, short_id_by_long_id: Dict[str, int]) -> None:
        """
        Given a dictionary of short ids by long ids, save campaign lookups in redis
        NOTE: This should only be used to set campaign long and short ids that come from the campaign service
        """
        if not short_id_by_long_id:
            return

        keys = {
            f"{RedisKeyTypes.CAMPAIGN}:{long_id}": short_id
            for long_id, short_id in short_id_by_long_id.items()
        }
        await self.redis_cache.mset(keys)

    async def set_campaign_long_id_by_short_id_batch(self, keys_with_values: Dict) -> None:
        """
        Given a dictionary of short campaign ids not incremental, and it's corresponding
        long campaign id, store them in redis
        structure:
            {"CAMPAIGN:short_id": long_id}
        """
        await self.redis_cache.cache_internal_id_batch(keys_with_values)

    async def set_campaign_long_id_by_koddi_id(self, koddi_campaign_id: str, matching_campaign_id: str) -> None:
        """
        Save campaign long id where it's external partner(KODDI) id is the same koddi id
        """
        koddi_key = f'KODDI:{koddi_campaign_id}'
        await self.redis_cache.set(RedisKeyTypes.CAMPAIGN, koddi_key, matching_campaign_id)

    async def set_campaign_long_id_by_koddi_id_batch(self, long_id_by_koddi_id: Dict[int, str]) -> None:
        """
        Save campaign long id where it's external partner(KODDI) id is the same koddi id batch
        """
        if not long_id_by_koddi_id:
            return

        keys = {
            f"{RedisKeyTypes.CAMPAIGN_KODDI}:{koddi_id}": long_id
            for koddi_id, long_id in long_id_by_koddi_id.items()
        }

        await self.redis_cache.mset(keys)

    async def set_campaign_long_id_by_short_adgroup_id(self, short_adgroup_id: int, long_campaign_id: str) -> None:
        """
        Save campaign long id with the short adgroup id
        """
        campaign_key = f"{RedisKeyTypes.CAMPAIGN}:{short_adgroup_id}"
        await self.redis_cache.set(RedisKeyTypes.AD_GROUP, campaign_key, long_campaign_id)

    async def set_koddi_campaign_id_by_short_id_batch(self, dict_koddi_campaign_ids: Dict) -> None:
        """
        Given a list of koddi campaign ids, assign a new incremental short id.
        """
        if not dict_koddi_campaign_ids:
            return

        koddi_keys_and_values = {
            f'{RedisKeyTypes.CAMPAIGN}:KODDI:{short_id}': koddi_id
            for short_id, koddi_id in dict_koddi_campaign_ids.items()
        }
        await self.redis_cache.mset(koddi_keys_and_values)

    # --------------------------- END CAMPAIGN SET OPERATIONS----------------------------

    # --------------------------- ADDRESS SET OPERATIONS----------------------------

    async def set_address_short_id_by_long_id(self, long_address_id: str) -> int:
        """
        Given a long address id, assign incremental short id.
        """
        return await self.redis_cache.assign_numeric_id(RedisKeyTypes.ADDRESS, long_address_id)

    async def set_address_details_by_short_id(self, short_id: int, address_info: CachedAddress) -> None:
        """
        Given a short incr address id, save the address info.
        """
        await self.redis_cache.set(RedisKeyTypes.ADDRESS, short_id, address_info.model_dump_json())

    async def set_address_long_id_by_account_long_id(self, long_address_id: str, long_account_id: str) -> None:
        """
        Save the long address id by the long account id.
        """
        await self.redis_cache.set(RedisKeyTypes.ADDRESS, long_account_id, long_address_id)

    async def set_address_details_by_short_id_batch(
            self,
            address_details_by_short_id: dict[int, CachedAddress]
    ) -> None:
        """
        Given a dict of short ids and address details, set the address details for each short id.
        """
        if not address_details_by_short_id:
            return
        keys = {
            f"{RedisKeyTypes.ADDRESS}:{short_id}": address_detail.model_dump_json()
            for short_id, address_detail in address_details_by_short_id.items()
        }
        return await self.redis_cache.mset(keys)
    # --------------------------- END ADDRESS SET OPERATIONS----------------------------


    # --------------------------- ACCOUNT SET OPERATIONS----------------------------
    async def set_account_short_id_by_long_id(self, long_account_id: str) -> int:
        """
        Given a long client id, assign incremental short id.
        """
        return await self.redis_cache.assign_numeric_id(RedisKeyTypes.ACCOUNT, long_account_id)

    async def set_account_long_id_by_short_id(self, short_id: int, long_account_id: str) -> None:
        """
        Given a short incr account id, save the clientId.
        """
        await self.redis_cache.set(RedisKeyTypes.ACCOUNT, short_id, long_account_id)

    async def set_account_short_ids_by_long_ids(self, account_client_ids: List[str]) -> List[int]:
        """
        Given a list of client ids, assign incremental short ids.
        """
        return await self.redis_cache.assign_numeric_id_batch(RedisKeyTypes.ACCOUNT, account_client_ids)

    async def set_account_short_id_by_long_id_batch(self, short_id_by_long_id: Dict[str, int]) -> None:
        """
        Given a dictionary of short account ids by long account ids,
        save the account lookups in redis.
        """
        if not short_id_by_long_id:
            return

        keys = {
            f"{RedisKeyTypes.ACCOUNT}:{long_id}": short_id
            for long_id, short_id in short_id_by_long_id.items()
        }
        await self.redis_cache.mset(keys)

    async def set_account_long_id_by_short_id_batch(self, long_ids_by_short_ids: Dict[str, int]) -> None:
        """
        Given a dictionary of short account ids by long account ids,
        save the account lookups in redis.
        """
        if not long_ids_by_short_ids:
            return

        keys = {
            f"{RedisKeyTypes.ACCOUNT}:{short_id}": long_id
            for long_id, short_id in long_ids_by_short_ids.items()
        }
        await self.redis_cache.mset(keys)
    #--------------------------- END ACCOUNT SET OPERATIONS----------------------------

    # --------------------------- ADGROUP SET OPERATIONS----------------------------
    async def set_adgroup_short_id_by_long_id_batch(self, short_id_by_long_id: Dict[str, int]) -> None:
        """
        Given a dictionary of short ad group ids by long ad group ids,
        save the ad group look ups in redis.
        NOTE: this should only be used to set short and long ids that are returned from the activation service!
        """
        if not short_id_by_long_id:
            return

        keys = {
            f"{RedisKeyTypes.AD_GROUP}:{long_id}": short_id
            for long_id, short_id in short_id_by_long_id.items()
        }
        await self.redis_cache.mset(keys)

    async def set_adgroup_long_id_by_short_id_batch(self, long_id_by_short_id: Dict[int, str]) -> None:
        """
        Given a dictionary of long ad group ids by short ad group ids,
        save the ad group look ups in redis.
        NOTE: this should only be used to set long and short ids that are returned from the activation service!
        """
        if not long_id_by_short_id:
            return

        keys = {
            f"{RedisKeyTypes.AD_GROUP}:{short_id}": long_id
            for short_id, long_id in long_id_by_short_id.items()
        }
        await self.redis_cache.mset(keys)

    async def set_adgroup_long_id_by_koddi_id(self, koddi_ad_group_id: str, long_activation_id: str) -> None:
        """
        Save ad group long (activation id) id by koddi ad group id.
        """
        await self.redis_cache.set(RedisKeyTypes.AD_GROUP, f'KODDI:{koddi_ad_group_id}', long_activation_id)

    async def set_adgroup_long_id_by_koddi_id_batch(self, long_id_by_koddi_id: Dict[int, str]) -> None:
        """
        Given a dictionary of long ad group ids by koddi ad group ids,
        save the ad group koddi lookups in redis.
        """
        if not long_id_by_koddi_id:
            return

        keys = {
            f"{RedisKeyTypes.AD_GROUP_KODDI}:{koddi_id}": long_id
            for koddi_id, long_id in long_id_by_koddi_id.items()
        }
        await self.redis_cache.mset(keys)

    # --------------------------- END ADGROUP SET OPERATIONS----------------------------

    # --------------------------- PRODUCT SET OPERATIONS----------------------------
    async def set_product_short_id_by_upc(self, upc: str) -> int:
        """
        Given a product upc, assign incremental short id.
        """
        return await self.redis_cache.assign_numeric_id(RedisKeyTypes.PRODUCT, upc)

    async def set_product_short_ids_by_upcs(self, upcs: List[str]) -> List[int]:
        """
        Given a list of product upcs, assign incremental short ids.
        """
        return await self.redis_cache.assign_numeric_id_batch(RedisKeyTypes.PRODUCT, upcs)

    async def set_product_details_by_short_id(self, short_id: int, product_details: CachedProduct) -> int:
        """
        Given an incremental short id, set the product details.
        """
        return await self.redis_cache.set(RedisKeyTypes.PRODUCT, short_id, product_details.model_dump_json())

    async def set_product_details_by_short_id_batch(
            self,
            product_details_by_short_id: dict[int, CachedProduct]
    ) -> None:
        """
        Given a dict of short ids and product details, set the product details for each short id.
        """
        if not product_details_by_short_id:
            return
        keys = {
            f"{RedisKeyTypes.PRODUCT}:{short_id}": product_detail.model_dump_json()
            for short_id, product_detail in product_details_by_short_id.items()
        }
        return await self.redis_cache.mset(keys)
    # --------------------------- END PRODUCT SET OPERATIONS----------------------------

    # --------------------------- ADVERTISER SET OPERATIONS----------------------------
    async def set_advertiser_short_id_by_long_id(self, long_brand_id: str) -> int:
        """
        Given long brand id, assign incremental short id for advertiser.
        """
        return await self.redis_cache.assign_numeric_id(RedisKeyTypes.ADVERTISER, long_brand_id)

    async def set_advertiser_short_id_by_long_id_batch(self, long_brand_ids: List[str]) -> List[int]:
        """
        Given long brand id, assign incremental short id for advertiser.
        """
        return await self.redis_cache.assign_numeric_id_batch(RedisKeyTypes.ADVERTISER, long_brand_ids)

    async def set_advertiser_details_by_short_id(
            self,
            short_id: int,
            advertiser_details: CachedRedisAdvertiser
    ) -> None:
        """
        Given an incremental short id, set the advertiser details.
        """
        await self.redis_cache.set(RedisKeyTypes.ADVERTISER, short_id, advertiser_details.model_dump_json())

    async def set_advertiser_details_by_short_id_batch(
            self,
            advertiser_details_by_short_id: dict[int, CachedRedisAdvertiser]
    ) -> None:
        """
        Given a dict of short ids and product details, set the product details for each short id.
        """
        if not advertiser_details_by_short_id:
            return
        keys = {
            f"{RedisKeyTypes.ADVERTISER}:{short_id}": advertiser_detail.model_dump_json()
            for short_id, advertiser_detail in advertiser_details_by_short_id.items()
        }
        return await self.redis_cache.mset(keys)

    async def set_koddi_advertiser_short_id_by_long_id(self, long_brand_id: str, koddi_short_id: str) -> None:
        """
        Save the koddi advertiser short id by long brand id.
        """
        await self.redis_cache.set(RedisKeyTypes.KODDI_ADVERTISER, long_brand_id, koddi_short_id)

    async def set_koddi_advertiser_short_id_by_long_id_and_agency_id(
            self,
            long_brand_id: str,
            agency_id: str,
            koddi_short_id: int
    ) -> None:
        """
        Save the koddi advertiser short id by long brand id and long agency id.
        """
        await self.redis_cache.set(RedisKeyTypes.KODDI_ADVERTISER, f'{long_brand_id}:{agency_id}', koddi_short_id)

    async def set_koddi_advertiser_short_id_batch(self, koddi_id_by_brands_ids: dict[str: str]) -> None:
        """
        Save the koddi advertiser short id by internal brand id or agency id +internal brand id
        """
        if not koddi_id_by_brands_ids:
            return

        keys = {
            f"{RedisKeyTypes.KODDI_ADVERTISER}:{key}": koddi_id
            for key, koddi_id in koddi_id_by_brands_ids.items()
        }
        await self.redis_cache.mset(keys)

    # --------------------------- END ADVERTISER SET OPERATIONS----------------------------

    # --------------------------- CONTACT SET OPERATIONS----------------------------
    async def set_contact_short_id_by_long_id(self, contact_long_id: str) -> int:
        """
        Given long contact id, assign incremental short id.
        """
        return await self.redis_cache.assign_numeric_id(RedisKeyTypes.CONTACT, contact_long_id)

    async def set_contact_short_id_by_long_id_batch(self, contact_long_ids: list[str]) -> list[int]:
        """
        Given long contact ids, assign incremental short ids.
        """
        return await self.redis_cache.assign_numeric_id_batch(RedisKeyTypes.CONTACT, contact_long_ids)

    async def set_contact_details_by_short_contact_id(self, short_id: int, details: str) -> None:
        """
        Given short incremental contact id, save its details.
        """
        await self.redis_cache.set(RedisKeyTypes.CONTACT, short_id, details)

    async def set_contact_details_by_short_id_batch(
            self,
            contact_details_by_short_id: dict[int, CachedContact]
    ) -> None:
        """
        Given a dict of short ids and contact details, set the contact details for each short id.
        """
        if not contact_details_by_short_id:
            return
        keys = {
            f"{RedisKeyTypes.CONTACT}:{short_id}": contact_detail.model_dump_json()
            for short_id, contact_detail in contact_details_by_short_id.items()
        }
        return await self.redis_cache.mset(keys)
    # --------------------------- END CONTACT SET OPERATIONS----------------------------

    # --------------------------- DIVISION SET OPERATIONS---------------------------------
    async def set_division_short_id_by_banner_code_and_division_number(
            self,
            banner_code: str,
            division_number: str
    ) -> int:
        """
        Given a banner code and division number, assign its incremental id.
        """
        division_key = f"{banner_code}:{division_number}"
        division_id = await self.redis_cache.assign_numeric_id(RedisKeyTypes.DIVISION, division_key)
        return division_id

    async def set_division_details_by_short_id(self, short_id: str, details: CachedDivision) -> None:
        """
        Given a short incremental division id save its details.
        """
        await self.redis_cache.set(RedisKeyTypes.DIVISION, short_id, details.model_dump_json())

    async def set_division_short_id_by_banner_code_and_division_number_batch(
            self,
            division_keys: List[str]
    ) -> List[int]:
        """
        Given a list division keys: {bannerCode:divisionNumber}, assign incremental short ids.
        """
        return await self.redis_cache.assign_numeric_id_batch(RedisKeyTypes.DIVISION, division_keys)

    async def set_division_data_by_short_id_batch(
            self,
            divisions: dict[str, DivisionServiceResponse]
    ):
        """
        Given a list of division short ids, set their data.
        """
        if not divisions:
            return

        keys = {
            f"{RedisKeyTypes.DIVISION}:{key}": division_data.model_dump_json()
            for key, division_data in divisions.items()
        }
        await self.redis_cache.mset(keys)

    # --------------------------- END DIVISION SET OPERATIONS----------------------------

    # --------------------------- PLACEMENT SET OPERATIONS----------------------------
    async def set_placement_short_id_by_id_and_name(self, placement_id: str, placement_name: str) -> int:
        """
        Given a placement id and name, assign its incremental id.
        """
        placement_key = f"{placement_id}:{placement_name}"
        placement_short_id = await self.redis_cache.assign_numeric_id(RedisKeyTypes.PLACEMENT, placement_key)
        return placement_short_id

    async def set_placement_details_by_short_id(self, short_id: int, details: CachedPlacement) -> None:
        """
        Given a placement incremental short id , save its details.
        """
        await self.redis_cache.set(RedisKeyTypes.PLACEMENT, short_id, details.model_dump_json())

    async def set_placement_short_id_by_name(self, placement_name: str, short_id: int) -> None:
        """
        Given a placement name save its incremental short id.
        """
        await self.redis_cache.set(RedisKeyTypes.PLACEMENT, placement_name, short_id)
    # --------------------------- END PLACEMENT SET OPERATIONS----------------------------
