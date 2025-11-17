import unittest
from unittest.mock import patch, MagicMock
from tests.unit.utils.oauth2_client import OAuth2Client


class TestOauth2Client(unittest.TestCase):
    def setUp(self):
        patcher = patch('tests.unit.utils.oauth2_client.httpx.post')
        self.addCleanup(patcher.stop)
        self.mock_post = patcher.start()

        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'test_token'}
        mock_response.raise_for_status = MagicMock()
        self.mock_post.return_value = mock_response

        self.client = OAuth2Client(
            client_id='test_client_id',
            client_secret='test_client_secret',
            token_url="https://test.com/token",
            scope='e451.api.access'
        )

    def test_get_oauth2_token(self):
        token = self.client.token
        self.assertEqual(token, 'test_token')
        self.mock_post.assert_called_once_with(
            "https://test.com/token",
            data={
                'grant_type': 'client_credentials',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'scope': 'e451.api.access'
            }
        )

    @patch('tests.unit.utils.oauth2_client.httpx.Client.request')
    def test_request(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = self.client.request('GET', 'https://test.com')

        mock_request.assert_called_once_with(
            'GET', 'https://test.com',
            headers={'Authorization': 'Bearer test_token'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response, mock_response)
