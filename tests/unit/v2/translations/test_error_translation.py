from typing import List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from app.common.model.downstream.bid_manager import BidEntityFailure
from app.common.model.shared import ActivationErrors, DateTimeField, ActivationWarnings
from app.common.view_models import DomainError, DomainType, ErrorDateTime
from app.v2.model.downstream.activation_service import ActivationResponse, ActivationResponseV2
from app.v2.translations.error_translation import ErrorTranslation
from app.v2.view_models import AdGroupFromActivation
from tests.utils_for_testing.auto_mock import auto_mock


class TestErrorTranslation(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_lookup = AsyncMock()
        self.error_translation = ErrorTranslation(
            lookup = self.mock_lookup,
        )

    def test_from_entity_errors__returns_none_when_no_entity_errors(self):
        ad_group = MagicMock()
        entity_errors = []

        translated_errors = self.error_translation.from_entity_errors(
            ad_group,
            entity_errors
        )

        self.assertEqual(None, translated_errors)

    @patch.object(ErrorDateTime, "now")
    def test_from_entity_errors__translates_entity_errors(
            self,
            mock_now
    ):
        entity_id = "1234"
        ad_group_id = 4321
        ad_group = MagicMock()
        ad_group.adGroupId = ad_group_id
        expected_time = ErrorDateTime(
            value="2025-09-10T17:32:18.051Z",
            timezone="UTC",
        )
        entity_errors = [
            BidEntityFailure(
                field="field name",
                message="error details",
                entity_id=entity_id
            )
        ]
        expected_translated_error = DomainError(
            domain=DomainType.AD_GROUP,
            id=ad_group_id,
            fieldName="entities",
            code="entity_errors",
            reason="Ad group entities need updates",
            datetime=expected_time,
            rootCauses=[
                DomainError(
                    domain=DomainType.ENTITY,
                    id=entity_id,
                    fieldName="field name",
                    code="entity_error",
                    reason="error details",
                    datetime=expected_time
                )
            ]
        )
        mock_now.return_value = expected_time

        translated_errors = self.error_translation.from_entity_errors(
            ad_group,
            entity_errors
        )

        self.assertEqual(expected_translated_error, translated_errors)

    async def test_activation_errors_with_short_ids(self):
        activation_ids = [f"{i}" for i in range(1,5)]
        short_ids = [i * 10 for i in range(1,5)]
        activation_errors = [
            auto_mock({"identifier": activation_id}, MagicMock())
            for activation_id in activation_ids
        ]
        expected_result = zip(activation_errors, short_ids)
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = short_ids

        result = await self.error_translation.activation_errors_with_short_ids(activation_errors)

        for expected, actual in zip(expected_result, result):
            self.assertEqual(expected, actual)

    def test_from_activation_error__translates_activation_error(self):
        short_id = 1234
        input_date = DateTimeField(
            value="2025-09-10T17:32:18.051Z",
            timezone="UTC",
        )
        expected_date = ErrorDateTime.from_date_time_field(input_date)
        activation_error = ActivationErrors(
            code="activation_error",
            reason="error details",
            datetime=input_date,
            field_name="budgetAmount",
            identifier="4321"
        )
        expected_error = DomainError(
            domain=DomainType.AD_GROUP,
            id=short_id,
            fieldName="budgetAmount",
            code="activation_error",
            reason="error details",
            datetime=expected_date
        )

        translated_error = self.error_translation.from_activation_error(activation_error, short_id)

        self.assertEqual(expected_error, translated_error)

    def test_from_activation_error__translates_activation_warning(self):
        short_id = 1234
        input_date = DateTimeField(
            value="2025-09-10T17:32:18.051Z",
            timezone="UTC",
        )
        expected_date = ErrorDateTime.from_date_time_field(input_date)
        activation_warning = ActivationWarnings(
            code="activation_warning",
            reason="warning details",
            datetime=input_date,
            field_name="budgetAmount",
            identifier="4321"
        )
        expected_warning = DomainError(
            domain=DomainType.AD_GROUP,
            id=short_id,
            fieldName="budgetAmount",
            code="activation_warning",
            reason="warning details",
            datetime=expected_date
        )

        translated_warning = self.error_translation.from_activation_error(activation_warning, short_id)

        self.assertEqual(expected_warning, translated_warning)

    @patch.object(ErrorDateTime, "now")
    async def test_errors_from_ad_groups_info__translates_ad_group_errors(self, mock_now):
        ad_group_id=1234
        entity_id="4567"
        ad_groups_info = [AdGroupFromActivation(
            adGroup=auto_mock({"adGroupId": ad_group_id}, MagicMock()),
            entityErrors=[
                BidEntityFailure(
                    field="field name",
                    message="error details",
                    entity_id=entity_id
                )
            ]
        )]
        input_date = DateTimeField(
            value="2025-09-10T17:32:18.051Z",
            timezone="UTC",
        )
        expected_date = ErrorDateTime.from_date_time_field(input_date)
        activations_response = auto_mock({
            "errors": [
                ActivationErrors(
                    code="activation_error",
                    reason="error details",
                    datetime=input_date,
                    field_name="budgetAmount",
                    identifier="4321"
                ).__dict__
            ]
        }, MagicMock(spec=ActivationResponseV2[List[ActivationResponse]]))
        mock_now.return_value = expected_date
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = [ad_group_id]
        expected_errors = [
            DomainError(
                domain=DomainType.AD_GROUP,
                id=ad_group_id,
                fieldName="entities",
                code="entity_errors",
                reason="Ad group entities need updates",
                datetime=expected_date,
                rootCauses=[
                    DomainError(
                        domain=DomainType.ENTITY,
                        id=entity_id,
                        fieldName="field name",
                        code="entity_error",
                        reason="error details",
                        datetime=expected_date
                    )
                ]
            ),
            DomainError(
                domain=DomainType.AD_GROUP,
                id=ad_group_id,
                fieldName="budgetAmount",
                code="activation_error",
                reason="error details",
                datetime=expected_date
            )
        ]

        translated_errors = await self.error_translation.errors_from_ad_groups_info(ad_groups_info, activations_response)

        self.assertEqual(expected_errors, translated_errors)

    @patch.object(ErrorDateTime, "now")
    async def test_warnings_from_ad_groups_info__translates_ad_group_warnings(
            self,
            mock_now
    ):
        ad_group_id = 1234
        entity_id = "4567"
        ad_groups_info = [AdGroupFromActivation(
            adGroup=auto_mock({"adGroupId": ad_group_id}, MagicMock()),
            entityErrors=[
                BidEntityFailure(
                    field="field name",
                    message="error details",
                    entity_id=entity_id
                )
            ]
        )]
        input_date = DateTimeField(
            value="2025-09-10T17:32:18.051Z",
            timezone="UTC",
        )
        expected_date = ErrorDateTime.from_date_time_field(input_date)
        activations_response = auto_mock({
            "warnings": [
                ActivationErrors(
                    code="activation_warning",
                    reason="warning details",
                    datetime=input_date,
                    field_name="budgetAmount",
                    identifier="4321"
                ).__dict__
            ]
        }, MagicMock(spec=ActivationResponseV2[List[ActivationResponse]]))
        mock_now.return_value = expected_date
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = [ad_group_id]
        expected_warnings = [
            DomainError(
                domain=DomainType.AD_GROUP,
                id=ad_group_id,
                fieldName="budgetAmount",
                code="activation_warning",
                reason="warning details",
                datetime=expected_date
            )
        ]

        translated_warnings = await self.error_translation.warnings_from_ad_groups_info(
            ad_groups_info,
            activations_response
        )

        self.assertEqual(expected_warnings, translated_warnings)