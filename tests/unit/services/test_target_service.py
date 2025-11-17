import unittest

from app.common.model.targets import TargetTypes, Target
from app.common.services.target_service import TargetService


class TestTargetService(unittest.TestCase):
    def setUp(self):
        self.target_service = TargetService()

    def test_get_targets_returns_list(self):
        targets = self.target_service.get_targets()
        self.assertIsInstance(targets, list)

    def test_get_targets_list_contains_target_objects(self):
        targets = self.target_service.get_targets()
        for target in targets:
            self.assertIsInstance(target, Target)

    def test_get_targets_returns_correct_attributes(self):
        targets = self.target_service.get_targets()
        expected = [
            {"id": 1, "type": TargetTypes.PLACEMENTS},
            {"id": 2, "type": TargetTypes.DIVISION},
            {"id": 3, "type": TargetTypes.HOUR}
        ]
        for target, expected_target in zip(targets, expected):
            self.assertEqual(target.id, expected_target["id"])
            self.assertEqual(target.type, expected_target["type"])
