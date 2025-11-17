from unittest import TestCase

from app.common.exceptions import ActivationLockedException
from app.common.retry.predicates import activation_is_locked


class TestActivationIsLocked(TestCase):
    def test_activation_is_locked__matching_exception__should_return_true(self):
        result = activation_is_locked(ActivationLockedException())
        self.assertTrue(result)

    def test_activation_is_locked__non_matching_exception__should_return_false(self):
        result = activation_is_locked(Exception())
        self.assertFalse(result)