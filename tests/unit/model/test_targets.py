import unittest

import pytest

from app.common.model.targets import TargetAdgroupRequest, Target


class TestTargetAdGroupRequest(unittest.TestCase):
    def test_TargetAdgroupRequest__can_be_hashed(self):
        target1 = TargetAdgroupRequest(type=3, values=[1, 2])
        target2 = TargetAdgroupRequest(type=3, values=[4, 5])

        target1_hash = hash(target1)
        target2_hash = hash(target2)

        self.assertIsNotNone(target1_hash)
        self.assertIsNotNone(target2_hash)
        self.assertNotEqual(target1_hash, target2_hash)

    def __assert_values_invalid(self, values):
        expected_exception = None
        try:
            TargetAdgroupRequest(type=3, values=values)
            self.assertTrue(False, "Should have raised an exception")
        except ValueError as e:
            expected_exception = e

        self.assertIsNotNone(expected_exception)

    def test_TargetAdgroupRequest__throws_when_values_is_not_a_list(self):
        self.__assert_values_invalid("Bad values")

    def test_TargetAdgroupRequest__throws_when_there_are_less_than_2_values(self):
        self.__assert_values_invalid([1])

    def test_TargetAdgroupRequest__throws_when_there_are_more_than_2_values(self):
        self.__assert_values_invalid([1, 2, 3])

    def test_TargetAdgroupRequest__throws_when_values_are_the_same(self):
        self.__assert_values_invalid([1, 1])

    def test_TargetAdgroupRequest__parses_ints_when_values_are_strings(self):
        target = TargetAdgroupRequest(type=3, values=["1", "2"])

        self.assertEqual([1, 2], target.values)

    def test_TargetAdgroupRequest__throws_when_values_are_floats(self):
        self.__assert_values_invalid([1.5, 2.5])

class TestTargetModel(unittest.TestCase):
    def test_model_dump_excludes_none_values(self):
            target = Target(type="example", id=1, values=None)

            dumped = target.model_dump()
            self.assertNotIn('values', dumped)

       

    def test_model_dump_includes_values(self):
            target = Target(type="example", id=1, values=[1, 2, 3])

            dumped = target.model_dump()
            self.assertIn('values', dumped)

