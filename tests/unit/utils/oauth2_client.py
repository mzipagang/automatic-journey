import httpx


class OAuth2Client:
    def __init__(self, client_id, client_secret, token_url, scope, *args, **kwargs):
        self.client = httpx.Client(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.scope = scope
        self.token = self._get_oauth2_token()

    def _get_oauth2_token(self):
        response = httpx.post(self.token_url, data={
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        })
        response.raise_for_status()
        return response.json().get("access_token")

    def request(self, method, url, *args, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        return self.client.request(method, url, headers=headers, *args, **kwargs)

    def close(self):
        self.client.close()
