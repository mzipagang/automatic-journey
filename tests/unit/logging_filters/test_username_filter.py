from unittest import TestCase
from logging import LogRecord
from app.common.logging_filters.username_filter import UsernameFilter


class TestUsernameFilter(TestCase):

    def test_filter__should_add_username_to_record(self):
        # Arrange

        from app.common.context.context import user_context
        user_context.set({'username': 'test_user@email.invalid'})
        record = LogRecord('name', 1, 'pathname', 1, 'message', None, None)
        sut = UsernameFilter()

        result = sut.filter(record)

        self.assertTrue(result)
        self.assertEqual('test_user@email.invalid', record.usr['name'])

    def test_filter__no_username_in_context__should_add_as_Unset(self):
        from app.common.context.context import user_context
        user_context.set({})
        record = LogRecord('name', 1, 'pathname', 1, 'message', None, None)
        sut = UsernameFilter()

        result = sut.filter(record)

        self.assertTrue(result)
        self.assertEqual('Unset', record.usr['name'])

    def test_filter__user_context_var_is_not_dict__name_should_equal_Unset(self):
        from app.common.context.context import user_context
        user_context.set('not a dict')
        record = LogRecord('name', 1, 'pathname', 1, 'message', None, None)
        sut = UsernameFilter()

        sut.filter(record)

        self.assertTrue(hasattr(record, 'usr'))
        self.assertEqual({'name': 'Unset'}, record.usr)
