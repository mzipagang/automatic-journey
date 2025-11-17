from logging import LogRecord
from unittest import TestCase

from app.common.context.context import logging_extra_context


class TestExtraContextFilter(TestCase):
    def setUp(self):
        logging_extra_context.set({'extra_name': 'test', 'other_name': 'other_test'})

    def test_filter__should_add_extra_context_to_record(self):
        from app.common.logging_filters.extra_context_filter import ExtraContextFilter

        record: LogRecord = LogRecord(name='test', level=1, pathname='test', lineno=1, msg='test', args=None, exc_info=None)
        the_filter = ExtraContextFilter()

        result = the_filter.filter(record)

        self.assertTrue(result)
        self.assertEqual('test', record.extra_name)
        self.assertEqual('other_test', record.other_name)
