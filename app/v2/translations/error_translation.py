from typing import List, Tuple, Iterable

from fastapi import Depends

from app.common.model.downstream.bid_manager import BidEntityFailure
from app.common.model.shared import ActivationErrors, ActivationWarnings
from app.common.services.lookup_service import LookupService
from app.common.view_models import DomainError, DomainType, ErrorDateTime
from app.v2.model.downstream.activation_service import ActivationResponseV2, ActivationResponse
from app.v2.view_models import AdGroupV2, AdGroupFromActivation


class ErrorTranslation:
    lookup: LookupService

    def __init__(
            self,
            lookup: LookupService = Depends(LookupService),
    ):
        self.lookup = lookup

    @staticmethod
    def from_entity_errors(
            ad_group: AdGroupV2,
            entity_errors: List[BidEntityFailure]
    ) -> DomainError | None:
        if not entity_errors:
            return None
        entity_domain_errors = [
            DomainError(
                domain=DomainType.ENTITY,
                id=entity_error.entity_id,
                fieldName=entity_error.field,
                code="entity_error",
                reason=entity_error.message,
                datetime=ErrorDateTime.now()
            )
            for entity_error in entity_errors
        ]
        return DomainError(
            domain=DomainType.AD_GROUP,
            id=ad_group.adGroupId,
            fieldName="entities",
            code="entity_errors",
            reason="Ad group entities need updates",
            datetime=ErrorDateTime.now(),
            rootCauses=entity_domain_errors
        )

    async def activation_errors_with_short_ids(
            self,
            activation_errors: List[ActivationErrors | ActivationWarnings],
    ) -> Iterable[Tuple[ActivationErrors | ActivationWarnings, int | None]]:
        long_ids = [error.identifier for error in activation_errors]
        short_ids = await self.lookup.get_adgroup_short_id_by_long_id_batch(long_ids)
        return zip(activation_errors, short_ids)

    @staticmethod
    def from_activation_error(
            activation_error: ActivationErrors | ActivationWarnings,
            short_id: int | None
    ) -> DomainError:
        return DomainError(
            domain=DomainType.AD_GROUP,
            id=short_id,
            fieldName=activation_error.field_name,
            code=activation_error.code,
            reason=activation_error.reason,
            datetime=ErrorDateTime.from_date_time_field(activation_error.datetime),
        )

    async def errors_from_ad_groups_info(
            self,
            ad_groups_info: List[AdGroupFromActivation[AdGroupV2]],
            activations_response: ActivationResponseV2[List[ActivationResponse]]
    ) -> List[DomainError]:
        errors = []

        # Extend errors with entity errors
        errors.extend([
            self.from_entity_errors(
                ad_group_info.adGroup,
                ad_group_info.entityErrors
            )
            for ad_group_info in ad_groups_info
            if ad_group_info.entityErrors
        ])

        activation_errors_with_short_ids = await self.activation_errors_with_short_ids(
            activations_response.errors
        )
        # Extend errors with activation service errors
        errors.extend([
            self.from_activation_error(activation_error, short_id)
            for activation_error, short_id in activation_errors_with_short_ids
        ])

        return errors

    async def warnings_from_ad_groups_info(
            self,
            ad_groups_info: List[AdGroupFromActivation],
            activations_response: ActivationResponseV2[List[ActivationResponse]]
    ) -> List[DomainError]:
        warnings = []
        activation_warnings_with_short_ids = await self.activation_errors_with_short_ids(
            activations_response.warnings
        )
        warnings.extend([
            self.from_activation_error(activation_warning, short_id)
            for activation_warning, short_id in activation_warnings_with_short_ids
        ])

        return warnings
