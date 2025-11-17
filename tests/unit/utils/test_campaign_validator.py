from unittest import TestCase, IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.common.model.advertiser import AdvertiserType
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.model.redis import CachedAddress, CachedContact
from app.v2.utils.campaign_validator import (
    validate_dates_with_budget,
    validate_multiple_brand_ids,
    from_upstream_campaign_validations,
    CampaignValidator,
)
from app.common.model.downstream.campaign_service import Validations
from app.common.model.shared import BudgetType, UpstreamValidationWarning
from app.common.view_models import AdGroupStatus
from app.common.model.downstream.campaign_activation_service import AddressReference, ContactReference


class TestValidationFunctions(IsolatedAsyncioTestCase):

    async def test_validate_dates_with_budget_no_errors(self):
        start = datetime(2025, 1, 1)
        # end date within two years
        end = start + timedelta(days=365 * 2 - 1)
        # DAILY budget: should not require end_date
        await validate_dates_with_budget(start, end, BudgetType.DAILY)
        # LIFETIME budget with explicit end_date: OK
        await validate_dates_with_budget(start, end, BudgetType.LIFETIME)

    async def test_validate_dates_with_budget_end_date_too_far(self):
        start = datetime(2025, 1, 1)
        # exactly two years ahead should fail
        end = start.replace(year=start.year + 2)
        with self.assertRaises(HTTPException) as ctx:
            await validate_dates_with_budget(start, end, BudgetType.DAILY)
        self.assertEqual(ctx.exception.detail, "Campaign end date must be within 2 years after start date")

    async def test_validate_dates_with_budget_lifetime_missing_end(self):
        start = datetime(2025, 1, 1)
        with self.assertRaises(HTTPException) as ctx:
            await validate_dates_with_budget(start, None, BudgetType.LIFETIME)
        self.assertEqual(ctx.exception.detail, "End date must be provided for lifetime campaigns")

    def test_validate_multiple_brand_ids_single(self):
        class Dummy:
            brandIds = ["A"]
        # no exception for one brand
        validate_multiple_brand_ids(Dummy())

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag')
    def test_validate_multiple_brand_ids_multiple(
            self,
            mock_fetch_multivariate_flag: MagicMock,
            mock_is_harness_flag_on: MagicMock):
        class Dummy:
            brandIds = ["A", "B"]
        with self.assertRaises(HTTPException) as ctx:
            validate_multiple_brand_ids(Dummy())
        self.assertEqual(ctx.exception.detail, "Multi-brand campaigns are not yet supported")
        mock_fetch_multivariate_flag.assert_not_called()
        mock_is_harness_flag_on.assert_called_once_with(
            HarnessFeatureFlags.DISABLE_MULTIPLE_BRAND_IDS, 'default')

    def test_from_upstream_campaign_validations(self):
        upstream = Validations(detail=["foo"], path="/bar")
        warning = from_upstream_campaign_validations(upstream)
        self.assertIsInstance(warning, UpstreamValidationWarning)
        self.assertEqual(warning.detail, ["foo"])
        self.assertEqual(warning.path, "/bar")


class DummyAdGroup:
    def __init__(self, status, endDate):
        self.status = status
        self.endDate = endDate  # string in ISO format or None


class TestCampaignValidator(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # set up a validator whose services we can control
        self.addr_svc = AsyncMock()
        self.contact_svc = AsyncMock()
        self.account_svc = MagicMock()
        self.adv_svc = MagicMock()

        self.validator = CampaignValidator(
            account_service=self.account_svc,
            advertiser_service=self.adv_svc,
            address_service=self.addr_svc,
            contact_service=self.contact_svc,
        )

    async def test__related_adgroups_have_valid_enddate_all_valid(self):
        # two active groups both ending before ref date
        ref = datetime(2025, 6, 1, tzinfo=timezone.utc)
        ag1 = DummyAdGroup(AdGroupStatus.ACTIVE, "2025-05-01")
        ag2 = DummyAdGroup(AdGroupStatus.ENDED, None)
        ok = await self.validator._related_adgroups_have_valid_enddate( [ag1, ag2], ref)
        self.assertTrue(ok)

    async def test__related_adgroups_have_valid_enddate_invalid_null_and_active(self):
        # active with no endDate → invalid
        ref = datetime(2025, 6, 1, tzinfo=timezone.utc)
        ag = DummyAdGroup(AdGroupStatus.ACTIVE, None)
        ok = await self.validator._related_adgroups_have_valid_enddate([ag], ref)
        self.assertFalse(ok)

    async def test__related_adgroups_have_valid_enddate_invalid_future_enddate(self):
        # ended after ref date → invalid
        ref = datetime(2025, 6, 1, tzinfo=timezone.utc)
        ag = DummyAdGroup(AdGroupStatus.ACTIVE, "2025-07-01")
        ok = await self.validator._related_adgroups_have_valid_enddate([ag], ref)
        self.assertFalse(ok)

    async def test_validate_billing_info_no_agency_contact_is_agency(self):
        # agency_id None but contact.type is agency → error
        addr = CachedAddress(id="A1", addressType=AdvertiserType.AGENCY)
        contact = CachedContact(id="C1", contactType=AdvertiserType.AGENCY)
        with self.assertRaises(HTTPException) as ctx:
            await self.validator.validate_billing_info(addr, contact, account_id="acct")
        self.assertIn("Billing contact belongs to an agency", ctx.exception.detail)

    async def test_validate_billing_info_agency_flow_success(self):
        # agency_id provided, address.type agency, contact validated → agency billing
        addr = CachedAddress(id="A1", addressType=AdvertiserType.AGENCY)
        contact = CachedContact(id="C2", contactType=AdvertiserType.AGENCY)
        self.addr_svc.get_corporate_address_by_internal_account_id.return_value = "CORP"
        self.contact_svc.validate_address_on_agency_involved_campaign.return_value = True

        result = await self.validator.validate_billing_info(
            addr, contact, account_id="acct", agency_id="agency"
        )
        self.assertTrue(result["is_agency_billed"])
        self.assertEqual(result["billing_contact_id"], "C2")
        self.assertEqual(result["billing_address_id"], "A1")
        self.assertEqual(result["corporate_address_id"], "CORP")

    async def test_validate_billing_info_agency_flow_contact_not_valid(self):
        # agency_id provided, address.type agency but contact invalid → error
        addr = CachedAddress(id="A1", addressType=AdvertiserType.AGENCY)
        contact = CachedContact(id="C3", contactType=AdvertiserType.AGENCY)
        self.contact_svc.validate_address_on_agency_involved_campaign.return_value = False
        self.addr_svc.get_corporate_address_by_internal_account_id.return_value = "CORP"
        with self.assertRaises(HTTPException) as ctx:
            await self.validator.validate_billing_info(
                addr, contact, account_id="acct", agency_id="agency"
            )
        self.assertIn("contact does not", ctx.exception.detail)
