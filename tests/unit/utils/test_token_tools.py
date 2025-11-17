from unittest import TestCase
from unittest.mock import patch, MagicMock

from app.common.utils.token_tools import parse_token_for_username
from tests.utils_for_testing.utils import encode_dict_as_jwt


class TestTokenTools(TestCase):
    def test_parse_token_for_username__kong_token__should_succeed(self):
        token = encode_dict_as_jwt({"login": "token_test@domain.invalid"})
        result = parse_token_for_username(token)
        self.assertEqual("token_test@domain.invalid", result)

    def test_parse_token_for_username__koddi_token__with_plus__should_succeed(self):
        token = encode_dict_as_jwt({"email": "koddi_email@domain.invalid+stg"})
        result = parse_token_for_username(token)
        self.assertEqual("koddi_email@domain.invalid", result)

    def test_parse_token_for_username__koddi_token__without_plus__should_succeed(self):
        token = encode_dict_as_jwt({"email": "koddi_email_noplus@domain.invalid"})
        result = parse_token_for_username(token)
        self.assertEqual("koddi_email_noplus@domain.invalid", result)

    def test_parse_token_for_username__koddi_token__plus_wrong_place__no_env_plus__should_succeed(self):
        token = encode_dict_as_jwt({"email": "plus+plus@plus.plus+.invalid"})
        result = parse_token_for_username(token)
        self.assertEqual("plus+plus@plus.plus+.invalid", result)

    def test_parse_token_for_username__koddi_token__plus_wrong_place__env_plus__should_succeed(self):
        token = encode_dict_as_jwt({"email": "plus+plus@plus.plus+.invalid+stg"})
        result = parse_token_for_username(token)
        self.assertEqual("plus+plus@plus.plus+.invalid", result)

    @patch('app.common.utils.token_tools.logger.warning')
    def test_parse_token_for_username__unknown_token__should_return_none(self, mock_warning_logger: MagicMock):
        token = encode_dict_as_jwt({"unknown": "unknown"})
        result = parse_token_for_username(token)
        self.assertIsNone(result)
        mock_warning_logger.assert_called()

    def test_parse_token_for_username__api_user_token_type__should_return_cid_at_8451(self):
        token = encode_dict_as_jwt({"login": "", "cid": "abc123"})
        result = parse_token_for_username(token)
        self.assertEqual("abc123@8451.com", result)
