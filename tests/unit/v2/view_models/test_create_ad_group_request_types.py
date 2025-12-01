from typing import List
from unittest import TestCase
from unittest.mock import MagicMock

from app.common.model.targets import TargetAdgroupRequest
from app.common.view_models import Entity, AdGroupStatus
from app.v2.view_models import CreateAdGroupLegacyRequestV2, AdGroupV2Request, CreateAdGroupRequest


class TestCreateAdGroupRequestTypes(TestCase):
    __common_attributes =  {
        "campaignId": 1,
        "name": "name",
        "startDate": "2020-01-01",
        "budgetAmount": 10.23,
        "status": AdGroupStatus.DRAFT,
        "targets": [TargetAdgroupRequest(
            type=1,
            values=[1, 2],
        )],
    }

    def test_legacy_init(self):
        subject: CreateAdGroupLegacyRequestV2 = CreateAdGroupLegacyRequestV2(
            requestType="legacy",
            baseBid=1.23,
            entities=[MagicMock(spec=Entity)],
            **self.__common_attributes)

        self.assertEqual(subject.requestType, "legacy")
        self.assertEqual(subject.baseBid, 1.23)
        self.assertIsInstance(subject, AdGroupV2Request)

    def test_updated_init(self):
        subject: CreateAdGroupRequest = CreateAdGroupRequest(
            requestType="updated",
            **self.__common_attributes)

        self.assertEqual(subject.requestType, "updated")
        self.assertIsInstance(subject, AdGroupV2Request)
