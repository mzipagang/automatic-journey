from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from unittest import TestCase

from pydantic.fields import Callable

from app.common.cache.key_builders import get_advertisers_upstream_key_builder, account_by_internal_id_key_builder, \
    get_addresses_by_account__upstream_key_builder
from app.common.context.context import request_context, user_context


class TestKeyBuilders(TestCase):

    def setUp(self):
        user_context.set({})
        request_context.set({})

    def test_get_contacts_by_id_upstream_key_builder__should_reflect_params_and_path(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/contacts/1", "params": {"id": 1, "offset": 2, "size": 123}},
            user_context_object={"username": "test_user@test.invalid"},
            expected_key=':/contacts/1:id-1--offset-2--size-123:test_user@test.invalid:get_advertisers_upstream',
            method_under_test=get_advertisers_upstream_key_builder,)

    def test_get_contacts_by_id_upstream_key_builder__non_ordered_param_dict__should_order_in_key(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/contacts/1", "params": {"size": 123, "offset": 2, "id": 1}},
            user_context_object={"username": "test_user123@123.123.invalid"},
            expected_key=':/contacts/1:id-1--offset-2--size-123:test_user123@123.123.invalid:get_advertisers_upstream',
            method_under_test=get_advertisers_upstream_key_builder,)

    def test_get_contacts_by_id_upstream_key_builder__no_params__should_reflect_path(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/contacts/1", "params": {}},
            user_context_object={"username": "no_param_user@test.invalid"},
            expected_key=':/contacts/1::no_param_user@test.invalid:get_advertisers_upstream',
            method_under_test=get_advertisers_upstream_key_builder)

    def test_account_by_internal_id_key_builder__should_reflect_params_and_path(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/account/123", "params": {"id": 123, "offset": 2, "size": 123}},
            user_context_object={"username": "get_account_internal@tld.invalid"},
            expected_key=':/account/123:id-123--offset-2--size-123'
                         ':get_account_internal@tld.invalid:account_by_internal_id',
            method_under_test=account_by_internal_id_key_builder)

    def test_account_by_internal_id_key_builder__non_ordered_param_dict__should_order_in_key(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/account/123", "params": {"size": 123, "offset": 2, "id": 123}},
            user_context_object={"username": "get_account_internal@tld.invalid"},
            expected_key=':/account/123:id-123--offset-2--size-123'
                         ':get_account_internal@tld.invalid:account_by_internal_id',
            method_under_test=account_by_internal_id_key_builder)

    def test_account_by_internal_id_key_builder__no_params__should_reflect_path(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/account/123", "params": {}},
            user_context_object={"username": "get_account_internal@tld.invalid"},
            expected_key=':/account/123::get_account_internal@tld.invalid:account_by_internal_id',
            method_under_test=account_by_internal_id_key_builder)

    def test_get_addresses_by_account__upstream_key_builder__should_reflect_params_and_path(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/addresses", "params": {"id": 123, "offset": 2, "size": 123}},
            user_context_object={"username": "abc@123.invalid"},
            expected_key=':/addresses:id-123--offset-2--size-123:abc@123.invalid:get_addresses_by_account__upstream',
            method_under_test=get_addresses_by_account__upstream_key_builder)

    def test_get_addresses_by_account__upstream_key_builder__non_ordered_param_dict__should_order_in_key(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/addresses", "params": {"size": 123, "offset": 2, "id": 123}},
            user_context_object={"username": "abc@123.invalid"},
            expected_key=':/addresses:id-123--offset-2--size-123:abc@123.invalid:get_addresses_by_account__upstream',
            method_under_test=get_addresses_by_account__upstream_key_builder)

    def test_get_addresses_by_account__upstream_key_builder__no_params__should_reflect_path(self):
        self.__key_builder_assertions(
            request_context_object={"path": "/addresses", "params": {}},
            user_context_object={"username": "abc@123.invalid"},
            expected_key=':/addresses::abc@123.invalid:get_addresses_by_account__upstream',
            method_under_test=get_addresses_by_account__upstream_key_builder)




    @patch('logging.Logger.error')
    def test_get_contacts_by_id_upstream_key_builder__username_not_in_context_var__should_throw(
            self, mock_error_logger: MagicMock):
        user_context.set({})
        with self.assertRaises(HTTPException) as context:
            get_advertisers_upstream_key_builder(
                func=None,
                namespace="",
                request=None,
                response=None
            )

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("C-K-G_ERROR.  Please retry.", context.exception.detail)

        mock_error_logger.assert_called_once_with(
            "User context is empty during cache key generation",
            extra={
                "tracked_error_transaction": "cache_key_generation__empty_user_context",
                "error_context": {
                    "key_builder_name": "get_advertisers_upstream_key_builder",
                    "user_context": {}
                }
            }
        )

    @patch('logging.Logger.error')
    def test_get_contacts_by_id_upstream_key_builder__user_context_empty_dict__should_throw(
            self, mock_error_logger: MagicMock):
        user_context.set({})
        with self.assertRaises(HTTPException) as context:
            get_advertisers_upstream_key_builder(
                func=None,
                namespace="",
                request=None,
                response=None
            )

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("C-K-G_ERROR.  Please retry.", context.exception.detail)
        mock_error_logger.assert_called_once_with(
            "User context is empty during cache key generation",
            extra={
                "tracked_error_transaction": "cache_key_generation__empty_user_context",
                "error_context": {
                    "key_builder_name": "get_advertisers_upstream_key_builder",
                    "user_context": {},
                }
            })

    @patch('logging.Logger.error')
    def test_get_contacts_by_id_upstream_key_builder__user_context_is_None__should_throw(
            self,
            mock_error_logger: MagicMock):
        user_context.set(None)
        with self.assertRaises(HTTPException) as context:
            get_advertisers_upstream_key_builder(
                func=None,
                namespace="",
                request=None,
                response=None
            )

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("C-K-G_ERROR.  Please retry.", context.exception.detail)
        mock_error_logger.assert_called_once_with(
            "User context is empty during cache key generation",
            extra={
                "tracked_error_transaction": "cache_key_generation__empty_user_context",
                "error_context": {
                    "key_builder_name": "get_advertisers_upstream_key_builder",
                    "user_context": None,
                }
            })

    @patch('logging.Logger.error')
    def test_get_contacts_by_id_upstream_key_builder__username_is_None__should_throw(
            self, mock_error_logger: MagicMock):
        user_context.set({"username": None})
        with self.assertRaises(HTTPException) as context:
            get_advertisers_upstream_key_builder(
                func=None,
                namespace="",
                request=None,
                response=None
            )

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("C-K-G_ERROR.  Please retry.", context.exception.detail)
        mock_error_logger.assert_called_once_with(
            "Username is empty during cache key generation",
            extra={
                "tracked_error_transaction": "cache_key_generation__empty_username",
                "error_context": {
                    "key_builder_name": "get_advertisers_upstream_key_builder",
                    "user_context": {"username": None}
                }
            }
        )

    @patch('logging.Logger.error')
    def test_get_contacts_by_id_upstream_key_builder__username_is_empty_string__should_throw(
            self, mock_error_logger: MagicMock):
        user_context.set({"username": ""})

        with self.assertRaises(HTTPException) as context:
            get_advertisers_upstream_key_builder(
                func=None,
                namespace="",
                request=None,
                response=None
            )

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("C-K-G_ERROR.  Please retry.", context.exception.detail)

        mock_error_logger.assert_called_once_with(
            "Username is empty during cache key generation",
            extra={
                "tracked_error_transaction": "cache_key_generation__empty_username",
                "error_context": {
                    "key_builder_name": "get_advertisers_upstream_key_builder",
                    "user_context": {"username": ""}
                }
            }
        )

    def __key_builder_assertions(
            self,
            request_context_object: dict,
            user_context_object: dict,
            expected_key: str, method_under_test: Callable):
        request_context.set(request_context_object)
        user_context.set(user_context_object)

        result = method_under_test(
            func=None,
            namespace="",
            request=None,
            response=None
        )

        self.assertEqual(expected_key, result)
