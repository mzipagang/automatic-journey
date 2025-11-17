from unittest import TestCase

from app.common.utils.context_tools import (
    client_context,
    logging_extra_context,
    request_context,
    security_context,
    user_context,
    clear_all_context_vars,
    update_context,
)


class TestContextTools(TestCase):
    def setUp(self):
        client_context.set({})
        logging_extra_context.set({})
        request_context.set({})
        security_context.set({})
        user_context.set({})

    def test_update_context__should_succeed(self):
        update_context(logging_extra_context, new_key='new_value')
        
        self.assertEqual(logging_extra_context.get(), {'new_key': 'new_value'})

    def test_clear_all_context_vars__should_succeed(self):
        update_context(client_context, new_key='new_value')
        update_context(logging_extra_context, new_key='new_value')
        update_context(request_context, new_key='new_value')
        update_context(security_context, new_key='new_value')
        update_context(user_context, new_key='new_value')

        clear_all_context_vars()

        self.assertEqual(client_context.get(), {})
        self.assertEqual(logging_extra_context.get(), {})
        self.assertEqual(request_context.get(), {})
        self.assertEqual(security_context.get(), {})
        self.assertEqual(user_context.get(), {})
