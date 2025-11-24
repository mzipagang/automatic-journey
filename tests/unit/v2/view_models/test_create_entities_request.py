from typing import List
from unittest import TestCase
from unittest.mock import MagicMock

from pydantic import ValidationError

from app.common.view_models import CreateEntitiesRequest, Entity


class TestCreateEntitiesRequest(TestCase):
    def test_instantiation__missing_base_bid(self):
        with self.assertRaises(ValidationError) as e:
            CreateEntitiesRequest(entities=MagicMock(spec=List[Entity]))
        self.assertIsInstance(e.exception, ValidationError)
    def test_instantiation(self):
        entities: List[Entity] = [MagicMock(spec=Entity)]
        create_entities_request = CreateEntitiesRequest(baseBid=1.0, entities=entities)

        self.assertEqual(create_entities_request.entities, entities)
        self.assertEqual(create_entities_request.baseBid, 1.0)
