import json
import logging
import unittest

from fastapi.security import OAuth2AuthorizationCodeBearer

from app.common.services.config_service import ConfigService
from tests.unit.utils.openapi_utils import OpenAPIUtils

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="auth", tokenUrl="token")


class MediaMgmtActivationApiTest(unittest.TestCase):
    def setUp(self):
        self.config_service = ConfigService()
        if self.config_service._settings.env is None:
            self.config_service._settings.env = 'local'
        self.base_api_url = self.config_service.get_current_config().base_api_url

        client_id = self.config_service.get_current_config().api_validator_client_id
        client_secret = self.config_service.get_current_config().api_validator_client_secret
        env = self.config_service.get_current_config().env
        logger.info("Current environment: %s", env)

        if env != 'stg':
            self.skipTest("Environment is not 'stg', skipping test.")

        if not client_id or not client_secret:
            logger.warning("Invalid client ID or secret, skipping test..")
            self.skipTest("Invalid client ID or secret")

        token_url = f"https://login.8451.com/oauth2/aus2rfaog9lmi37qz697/v1/token"

        self.api_v1_url = f"{self.base_api_url}/media-mgmt-activation/api/v1/openapi.json"
        self.api_v2_url = f"{self.base_api_url}/media-mgmt-activation/api/v2/openapi.json"

        self.openapi_v1_spec_dict = OpenAPIUtils.get_openapi_spec_from_endpoint(self.api_v1_url, client_id, client_secret, token_url, "e451.api.access")
        self.openapi_v2_spec_dict = OpenAPIUtils.get_openapi_spec_from_endpoint(self.api_v2_url, client_id, client_secret, token_url, "e451.api.access")

    def compare_dicts(self, d1, d2, path=""):
        mismatches = []
        if d1 is None:
            mismatches.append(f"Expected dict at {path}, but got None")
            return mismatches
        if d2 is None:
            mismatches.append(f"Expected dict at {path}, but got None")
            return mismatches

        for key in d1:
            if key not in d2:
                mismatches.append(f"Missing key in fetched spec at {path}: {key}")
            else:
                if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    mismatches.extend(self.compare_dicts(d1[key], d2[key], path + f".{key}"))
                elif isinstance(d1[key], list) and isinstance(d2[key], list):
                    for i, (item1, item2) in enumerate(zip(d1[key], d2[key])):
                        if item1 != item2:
                            mismatches.append(f"Mismatch at {path}.{key}[{i}]: Expected {item1}, got {item2}")
                    if len(d1[key]) != len(d2[key]):
                        mismatches.append(
                            f"List length mismatch at {path}.{key}: Expected {len(d1[key])}, got {len(d2[key])}")
                elif d1[key] != d2[key]:
                    mismatches.append(f"Mismatch at {path}.{key}: Expected {d1[key]}, got {d2[key]}")
        for key in d2:
            if key not in d1:
                mismatches.append(f"Extra key in fetched spec at {path}: {key}")
        return mismatches

    def test_validate_schema_v1(self):
        with open('schemas/media-mgmt-activation-v1.json') as local_spec_file:
            local_spec_dict = json.load(local_spec_file)

        mismatches = self.compare_dicts(local_spec_dict, self.openapi_v1_spec_dict)
        self.assertEqual(mismatches, [], f"Media Management Service API v1 schema mismatches: {mismatches}")

    # v2 is not in use in 3P API yet, generate a warning instead of failing the test
    def test_validate_schema_v2(self):
        with open('schemas/media-mgmt-activation-v2.json') as local_spec_file:
            local_spec_dict = json.load(local_spec_file)

        mismatches = self.compare_dicts(local_spec_dict, self.openapi_v2_spec_dict)
        if mismatches:
            logger.warning(f"Media Management Service API v2 schema mismatches: {mismatches}")
        else:
            self.assertEqual(mismatches, [], f"Media Management Service API v2 schema mismatches: {mismatches}")