import unittest

from app.common.view_models import AdGroup, Entity
from app.common.model.targets import Target


class TestAdGroupModel(unittest.TestCase):

    def test_model_dump_excludes_none_values(self):
        target = Target(type="example", id=1, values=None)

        ad_group = AdGroup(
            adGroupId = 123,
            campaignId = 456,
            name = "Test Ad Group",
            entities = [Entity(id=1, useBaseBid=True, bidAmount=1.0, deleted=False)],
            targets = [target]
        )
        dumped = ad_group.model_dump()
        self.assertNotIn('values', dumped['targets'][0])

    def test_model_dump_includes_values(self):
        target = Target(type="example", id=1, values=[1,2,3])

        ad_group = AdGroup(
            adGroupId = 123,
            campaignId = 456,
            name = "Test Ad Group",
            entities = [Entity(id=1, useBaseBid=True, bidAmount=1.0, deleted=False)],
            targets = [target]
        )
        dumped = ad_group.model_dump()
        self.assertIn('values', dumped['targets'][0])
