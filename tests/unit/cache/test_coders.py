import unittest

from app.common.cache.coders import PydanticCoderFactory
from app.common.model.downstream.ent_client_service import EntClientServiceMeta
from app.common.model.redis import CachedRedisAdvertiser
from app.common.model.shared import ListDataResponse


class TestCoders(unittest.TestCase):
    def setUp(self):
        self.coder = PydanticCoderFactory.build(
            ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta]
        )
        pass

    def test_pydantic_coder_factory__returns_coder(self):
        coder = PydanticCoderFactory.build(
            ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta]
        )

        self.assertTrue(hasattr(coder, "encode"))
        self.assertTrue(hasattr(coder, "decode"))

    def test_pydantic_coder__encodes_and_decodes_model(self):
        mock_data = ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta](
            data=[
                CachedRedisAdvertiser(
                    brandId='brand1',
                    displayName="Brand One",
                    salesforceId="SF1",
                    client=None
                )
            ],
            meta=EntClientServiceMeta()
        )

        encoded_data = self.coder.encode(mock_data)
        decoded_data = self.coder.decode(encoded_data)

        self.assertIsInstance(encoded_data, bytes)
        self.assertIsInstance(
            decoded_data,
            ListDataResponse
        )
        self.assertIsInstance(decoded_data.data[0], CachedRedisAdvertiser)
        self.assertEqual(mock_data, decoded_data)
