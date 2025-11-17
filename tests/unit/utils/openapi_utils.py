import json

import httpx
from openapi_core import OpenAPI

from tests.unit.utils.oauth2_client import OAuth2Client


class OpenAPIUtils:
    @staticmethod
    def get_openapi_spec_from_endpoint(api_url, client_id, client_secret, token_url, scope):
        client = OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            scope=scope
        )
        try:
            response = client.request("GET", f"{api_url}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return None

    @staticmethod
    def get_openapi_spec_from_swagger(api_url, client_id, client_secret, token_url, scope):
        client = OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            scope=scope
        )
        response = client.request("GET", api_url)
        response.raise_for_status()
        content = response.text

        start_index = content.find('<div hidden id="oas">')
        if start_index == -1:
            return None

        start_index += len('<div hidden id="oas">')
        end_index = content.find('</div>', start_index)
        if end_index == -1:
            return None

        oas_content = content[start_index:end_index].strip()
        return json.loads(oas_content)

    @staticmethod
    def get_openapi_spec(api_url, swagger_url, client_id, client_secret, token_url, scope):
        spec = OpenAPIUtils.get_openapi_spec_from_endpoint(api_url, client_id, client_secret, token_url, scope)
        if spec is not None:
            return spec

        spec = OpenAPIUtils.get_openapi_spec_from_swagger(swagger_url, client_id, client_secret, token_url, scope)
        if spec is not None:
            return spec

        raise ValueError("Could not get OpenAPI schema for api url " + api_url)

    @staticmethod
    def parse_openapi_spec(openapi_spec_dict):
        return OpenAPI.from_dict(openapi_spec_dict)
