from unittest import TestCase

from app.common.model.campaign_types import InternalCampaignType
from app.common.model.downstream.campaign_service import CASCampaign


class TestCampaignActivationServiceModel(TestCase):
    def test_CASCampaign_instantiation__should_succeed(self):
        campaign_data = {
            "id": "123abc",
            "goalID": "goal123",
            "shortId": "789",
            "created": "2023-10-01T12:00:00Z",
            "createdBy": "0001-22-3-asdf-asdf",
            "createdByUser": "Test User",
            "lastModified": "2023-10-02T12:00:00Z",
            "lastModifiedBy": "0001-22-3-asdf-asdf",
            "lastModifiedByClientID": "client-123",
            "lastModifiedByUser": "Test User",
            "startDate": "2023-10-01T00:00:00Z",
            "endDate": "2023-12-31T23:59:59Z",
            "backgroundInformation": "Test background information",
            "isAlwaysOn": True,
            "primaryAccount": {
                "id": "account-123",
                "brands": ["Brand A", "Brand B"],
                "billingInfo": None,
                "addresses": None,
                "contacts": None,
                "isAgencyBeingInvolved": False,
                "agency": None
            },
            "partnerAccounts": [
                {
                    "id": "partner-456",
                    "brands": ["Brand C"],
                    "billingInfo": None,
                    "addresses": None,
                    "contacts": None,
                    "isAgencyBeingInvolved": True,
                    "agency": {
                        "id": "agency-789",
                        "billingInfo": None
                    }
                }
            ],
            "name": "Test Campaign",
            "budget": {
                "amount": 10000.0,
                "type": "CPC",
                "pacingType": "STANDARD"
            },
            "additionalBillingDetails": "Test billing details",
            "notesForAccounting": "Test notes",
            "activations": ["activation1", "activation2"],
            "type": "pla",
            "source": "SOURCE_A",
            "status": "ACTIVE",
            "externalIDs": [{"id": 456, "partner": "Test Partner"}],
            "internalContacts": [{"id": "contact-123", "type": "ACCOUNT_EXECUTIVE"}],
            "clickThroughDestinations": [{
                "id": "destination-123",
                "bannerizedURL": "http://example.com",
                "name": "Test Destination",
                "divisions": [{"clickThroughUrl": "http://example.com/division1", "name": "Division 1"}]}],
            "version": 1,
            "publishingStatus": "PUBLISHED"

        }

        campaign = CASCampaign(**campaign_data)

        self.assertIsInstance(campaign, CASCampaign)
        self.assertEqual(campaign.id, "123abc")
        self.assertEqual(campaign.goalID, "goal123")
        self.assertEqual(campaign.shortId, "789")
        self.assertEqual(campaign.created, "2023-10-01T12:00:00Z")
        self.assertEqual(campaign.createdBy, "0001-22-3-asdf-asdf")
        self.assertEqual(campaign.createdByUser, "Test User")
        self.assertEqual(campaign.lastModified, "2023-10-02T12:00:00Z")
        self.assertEqual(campaign.lastModifiedBy, "0001-22-3-asdf-asdf")
        self.assertEqual(campaign.lastModifiedByClientID, "client-123")
        self.assertEqual(campaign.lastModifiedByUser, "Test User")
        self.assertEqual(campaign.startDate, "2023-10-01T00:00:00Z")
        self.assertEqual(campaign.endDate, "2023-12-31T23:59:59Z")
        self.assertEqual(campaign.backgroundInformation, "Test background information")
        self.assertTrue(campaign.isAlwaysOn)
        self.assertEqual(campaign.primaryAccount.id, "account-123")
        self.assertIn("Brand A", campaign.primaryAccount.brands)
        self.assertIn("Brand B", campaign.primaryAccount.brands)
        self.assertIsNone(campaign.primaryAccount.billingInfo)
        self.assertIsNone(campaign.primaryAccount.addresses)
        self.assertIsNone(campaign.primaryAccount.contacts)
        self.assertFalse(campaign.primaryAccount.isAgencyBeingInvolved)
        self.assertIsNone(campaign.primaryAccount.agency)
        self.assertEqual(len(campaign.partnerAccounts), 1)
        self.assertEqual(campaign.partnerAccounts[0].id, "partner-456")
        self.assertIn("Brand C", campaign.partnerAccounts[0].brands)
        self.assertIsNone(campaign.partnerAccounts[0].billingInfo)
        self.assertIsNone(campaign.partnerAccounts[0].addresses)
        self.assertIsNone(campaign.partnerAccounts[0].contacts)
        self.assertTrue(campaign.partnerAccounts[0].isAgencyBeingInvolved)
        self.assertIsNotNone(campaign.partnerAccounts[0].agency)
        self.assertEqual(campaign.partnerAccounts[0].agency.id, "agency-789")
        self.assertIsNone(campaign.partnerAccounts[0].agency.billingInfo)
        self.assertEqual(campaign.name, "Test Campaign")
        self.assertEqual(campaign.budget.amount, 10000.0)
        self.assertEqual(campaign.budget.type, "CPC")
        self.assertEqual(campaign.budget.pacingType, "STANDARD")
        self.assertEqual(campaign.additionalBillingDetails, "Test billing details")
        self.assertEqual(campaign.notesForAccounting, "Test notes")
        self.assertIn("activation1", campaign.activations)
        self.assertIn("activation2", campaign.activations)
        self.assertEqual(campaign.type, InternalCampaignType.PLA)
        self.assertEqual(campaign.source, "SOURCE_A")
        self.assertEqual(campaign.status, "ACTIVE")
        self.assertEqual(len(campaign.externalIDs), 1)
        self.assertEqual(campaign.externalIDs[0].id, 456)
        self.assertEqual(campaign.externalIDs[0].partner, "Test Partner")
        self.assertEqual(len(campaign.internalContacts), 1)
        self.assertEqual(campaign.internalContacts[0].id, "contact-123")
        self.assertEqual(campaign.internalContacts[0].type, "ACCOUNT_EXECUTIVE")
        self.assertIsNotNone(campaign.clickThroughDestinations)
        self.assertEqual(campaign.clickThroughDestinations[0].id, "destination-123")
        self.assertEqual(campaign.clickThroughDestinations[0].bannerizedURL, "http://example.com")
        self.assertEqual(campaign.clickThroughDestinations[0].name, "Test Destination")
        self.assertEqual(len(campaign.clickThroughDestinations[0].divisions), 1)
        self.assertEqual(campaign.clickThroughDestinations[0].divisions[0].clickThroughUrl, "http://example.com/division1")
        self.assertEqual(campaign.clickThroughDestinations[0].divisions[0].name, "Division 1")
        self.assertEqual(campaign.version, 1)
        self.assertEqual(campaign.publishingStatus, "PUBLISHED")

    def test_CASCampaign_parses_campaign_type_correctly(self):
        pla_campaign = CASCampaign(type="pla")
        toa_campaign = CASCampaign(type="toa")
        carousel_campaign = CASCampaign(type="Promoted_Products_Carousel")
        unsupported_campaign = CASCampaign(type="PREMIUM_PLACEMENTS")

        self.assertEqual(pla_campaign.type, InternalCampaignType.PLA)
        self.assertEqual(toa_campaign.type, InternalCampaignType.TOA)
        self.assertEqual(carousel_campaign.type, InternalCampaignType.CAROUSEL)
        self.assertEqual(unsupported_campaign.type, InternalCampaignType.UNSUPPORTED)