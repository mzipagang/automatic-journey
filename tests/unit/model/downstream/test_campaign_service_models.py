from unittest import TestCase

from app.common.model.campaign_types import InternalCampaignType
from app.common.model.downstream.campaign_service import CampaignResponse, CampaignSearchRequest


class TestCampaignServiceModels(TestCase):
    def test_campaign_response_model__should_instantiate(self):
        sample_data = {
            "validations": [{"path": "/some/path", "detail": ["Error 1", "Error 2"]}],
            "unpublishedChanges": None,
            "publishedChanges": None,
            "publishingMetaData": {
                "code": "PUBLISHED",
                "description": "Campaign has been published",
                "datetime": {"value": "2023-10-01T12:00:00Z", "timezone": "UTC"},
                "errorCode": 0,
                "errorMessages": [],
                "changes": None
            },
            "publishingStatus": "PUBLISHED",
            "changes": None
        }

        campaign_response = CampaignResponse(**sample_data)

        response_attributes = set(campaign_response.model_dump().keys())
        self.assertEqual(response_attributes,
                         {'validations', 'unpublishedChanges', 'publishedChanges', 'publishingMetaData',
                          'publishingStatus', 'changes'})

        self.assertIsInstance(campaign_response, CampaignResponse)
        self.assertEqual(campaign_response.validations[0].path, "/some/path")
        self.assertIsNone(campaign_response.unpublishedChanges)
        self.assertEqual(campaign_response.publishingMetaData.description, "Campaign has been published")
        self.assertEqual(campaign_response.publishingMetaData.datetime.value, "2023-10-01T12:00:00Z")
        self.assertEqual(campaign_response.publishingMetaData.datetime.timezone, "UTC")
        self.assertEqual(campaign_response.publishingMetaData.errorCode, 0)
        self.assertEqual(campaign_response.publishingMetaData.errorMessages, [])
        self.assertIsNone(campaign_response.publishingMetaData.changes)
        self.assertEqual(campaign_response.publishingMetaData.code, "PUBLISHED")
        self.assertIsNone(campaign_response.publishedChanges)

    def test_CampaignSearchRequest__serializes_campaign_types(self):
        search_request = CampaignSearchRequest(
            campaignType=[
                InternalCampaignType.PLA,
                InternalCampaignType.TOA,
                InternalCampaignType.CAROUSEL,
                InternalCampaignType.UNSUPPORTED
            ]
        )
        empty_search_request = CampaignSearchRequest(campaignType=None)

        serialized_model = search_request.model_dump(exclude_unset=True)
        serialized_empty_model = empty_search_request.model_dump(exclude_unset=True)

        self.assertIn("PLA", serialized_model.get("campaignType"))
        self.assertIn("TOA", serialized_model.get("campaignType"))
        self.assertIn("Promoted_Products_Carousel", serialized_model.get("campaignType"))
        self.assertNotIn("UNSUPPORTED", serialized_model.get("campaignType"))
        self.assertIsNone(serialized_empty_model.get("campaignType"))
