from unittest import TestCase
from datetime import datetime

from app.common.view_models import CampaignStatus, PacingType
from app.common.model.advertiser import CachedAdvertiser
from app.common.model.campaign_types import InternalCampaignType
from app.common.model.downstream.campaign_service import CampaignResponse
from app.common.model.shared import BudgetType, InternalBudgetType, InternalPublishStatus
from app.common.model.downstream.campaign_activation_service import (
    ContactReference, AddressReference, CASCampaign, Budget, BillingInfo as CASBillingInfo)
from app.common.model.contact import InternalContact
from app.v2.view_models import CampaignPatchRequest, Campaign, CampaignRequest
from app.v2.utils.campaign_translations import CampaignTranslation


class TestCampaignTranslation(TestCase):

    def test_build_billing_info_empty(self):
        req = CampaignRequest(
            name="X",
            budgetAmount=1,
            pacingType=PacingType.EVEN,
            billingAdditionalDetails="",
            status=CampaignStatus.DRAFT,
            startDate='2035-01-01',
            endDate='2035-01-31',
            budgetType=BudgetType.DAILY,
            accountId=1,
            advertiserIds=[1],
            billingContactId=1,
            billingAddressId=1,
        )
        bi = CampaignTranslation.build_billing_info(req)
        self.assertFalse(bi.is_po_required)
        self.assertFalse(bi.is_io_required)
        self.assertIsNone(bi.billing_purchase_order)
        self.assertIsNone(bi.billing_insertion_order)
        self.assertEqual(bi.additional_billing_details, "")

    def test_build_billing_info_with_values(self):
        req = CampaignRequest(
            name="X",
            budgetAmount=1,
            pacingType=PacingType.EVEN,
            billingPurchaseOrder="PO123",
            billingInsertionOrder="IO456",
            billingAdditionalDetails="foo",
            status=CampaignStatus.DRAFT,
            startDate='2035-01-01',
            endDate='2035-01-31',
            budgetType=BudgetType.DAILY,
            accountId=1,
            advertiserIds=[1],
            billingContactId=1,
            billingAddressId=1,
        )
        bi = CampaignTranslation.build_billing_info(req)
        self.assertTrue(bi.is_po_required)
        self.assertTrue(bi.is_io_required)
        self.assertEqual(bi.billing_purchase_order, "PO123")
        self.assertEqual(bi.billing_insertion_order, "IO456")
        self.assertEqual(bi.additional_billing_details, "foo")

    def test_prepare_update_payload(self):
        req = CampaignRequest(
            billingPurchaseOrder="PO1",
            billingAdditionalDetails="detail",
            status=CampaignStatus.DRAFT,
            name="Camp",
            budgetAmount=500,
            pacingType=PacingType.EVEN,
            startDate='2035-01-01',
            endDate='2035-01-31',
            budgetType=BudgetType.DAILY,
            accountId=1,
            advertiserIds=[1],
            billingContactId=1,
            billingAddressId=1,
        )
        billing_info = CampaignTranslation.build_billing_info(req)
        payload = CampaignTranslation.prepare_update_payload(
            campaign_request=req,
            source="src",
            short_id=99,
            background_info="bg",
            budget_type=InternalBudgetType.CUSTOM,
            is_always_on=True,
            advertisers=[CachedAdvertiser(brandId="10"), CachedAdvertiser(brandId="20")],
            contact_list=[ContactReference(id="c1"), ContactReference(id="c2")],
            internal_contacts=[InternalContact(id="5", type="n")],
            address_list=[AddressReference(id="a1", type="TYPE")],
            account_id="acct",
            start_date=datetime(2025,5,1),
            end_date=datetime(2025,5,31),
            agency_id="agency",
            is_agency_billed=False,
            billing_details=billing_info
        )
        self.assertIsInstance(payload, CampaignPatchRequest)
        self.assertEqual(payload.source, "src")
        self.assertEqual(payload.campaignId, 99)
        self.assertEqual(payload.backgroundInfo, "bg")
        self.assertEqual(payload.budgetAmount, 500)
        self.assertListEqual(payload.brandIds, ["10", "20"])
        self.assertTrue(payload.isPoRequired)
        self.assertEqual(payload.billingPurchaseOrder, "PO1")
        self.assertEqual(payload.additionalBillingDetails, "detail")
        self.assertEqual(payload.accountId, "acct")
        self.assertEqual(payload.startDate, datetime(2025,5,1))
        self.assertEqual(payload.endDate, datetime(2025,5,31))
        self.assertFalse(payload.isAgencyBilled)

    def test_build_patch_payload_draft(self):
        req = CampaignRequest(
            name="D",
            budgetAmount=100,
            pacingType=PacingType.EVEN,
            status=CampaignStatus.DRAFT,
            billingAdditionalDetails="x",
            startDate='2035-01-01',
            endDate='2035-01-31',
            budgetType=BudgetType.DAILY,
            accountId=1,
            advertiserIds=[1],
            billingContactId=1,
            billingAddressId=1,
        )
        billing_info = (True, False, "POX", None)
        campaign = Campaign(status=CampaignStatus.DRAFT, id=1, accountId=1, advertiserIds=[1])
        payload = CampaignTranslation.build_patch_payload(
            campaign=campaign,
            campaign_request=req,
            source="src",
            campaign_id=1,
            is_always_on=False,
            advertisers=[CachedAdvertiser(brandId="5")],
            contact_list=[],
            internal_contacts=[],
            address_list=[],
            account_id="acct",
            is_agency_billed=False,
            budget_type=InternalBudgetType.CUSTOM,
            start_date=datetime(2025,1,1),
            end_date=datetime(2025,1,31),
            billing_info=billing_info
        )
        self.assertEqual(payload.name, "D")
        self.assertEqual(payload.status, CampaignStatus.DRAFT)
        self.assertTrue(payload.isPoRequired)
        self.assertEqual(payload.billingPurchaseOrder, "POX")
        self.assertIsNone(payload.billingInsertionOrder)

    def test_build_patch_payload_active(self):
        req = CampaignRequest(
            name="A",
            budgetAmount=200,
            pacingType=PacingType.EVEN,
            billingAdditionalDetails="x",
            status=CampaignStatus.DRAFT,
            startDate='2035-01-01',
            endDate='2035-01-31',
            budgetType=BudgetType.DAILY,
            accountId=1,
            advertiserIds=[1],
            billingContactId=1,
            billingAddressId=1,
        )
        campaign = Campaign(
            id=2,
            name="A",
            status=CampaignStatus.ACTIVE,
            budgetAmount=200,
            budgetType=BudgetType.LIFETIME,
            pacingType="SLOW",
            accountId=1,
            advertiserIds=[],
            billingInsertionOrder=None,
            billingPurchaseOrder=None,
            billingAdditionalDetails=None,
            billingContactId=None,
            billingAddressId=None,
            isArchived=None
        )
        payload = CampaignTranslation.build_patch_payload(
            campaign=campaign,
            campaign_request=req,
            source="src",
            campaign_id=2,
            is_always_on=True,
            advertisers=[CachedAdvertiser(brandId="7")],
            contact_list=[ContactReference(id="c")],
            internal_contacts=[InternalContact(id="9", type="n")],
            address_list=[AddressReference(id="a", type="T")],
            account_id="acct2",
            is_agency_billed=True,
            budget_type=InternalBudgetType.CUSTOM,
            start_date=None,
            end_date=datetime(2025,2,28),
            billing_info=(None, None, None, None)
        )
        self.assertEqual(payload.budgetType, InternalBudgetType.CUSTOM)
        self.assertEqual(payload.endDate, datetime(2025,2,28))
        self.assertTrue(payload.isAlwaysOn)
        self.assertTrue(payload.isAgencyBilled)
        self.assertListEqual(payload.brandIds, ["7"])

    def test_contact_and_address_lists(self):
        cl = CampaignTranslation.build_contact_list("CID")
        self.assertEqual(len(cl), 3)
        self.assertIsInstance(cl[0], ContactReference)
        self.assertEqual(cl[0].type, "billing-contact")

        al = CampaignTranslation.build_address_list("CORP", "BILL")
        self.assertIsInstance(al[1], AddressReference)
        self.assertEqual(al[1].type, "ALTERNATE")

    def test_get_campaign_and_publish_status(self):
        pub = CASCampaign(id="123")
        unpub = CASCampaign(id="456")
        resp = CampaignResponse(publishedChanges=pub, unpublishedChanges=unpub, publishingStatus=InternalPublishStatus.PENDING)
        camp, status = CampaignTranslation.get_campaign_and_publish_status_from_response(resp)
        self.assertEqual(getattr(camp, "id"), "456")
        self.assertEqual(status, "PENDING")
