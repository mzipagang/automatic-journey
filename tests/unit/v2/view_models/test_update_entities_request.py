from typing import List
from unittest import TestCase
from unittest.mock import MagicMock

from pydantic import BaseModel, ValidationError

from app.common.view_models import UpdateEntitiesRequest, Entity


class TestUpdateEntitiesRequest(TestCase):
    def test_instantiation__missing_entities(self):
        with self.assertRaises(ValidationError) as e:
            UpdateEntitiesRequest()

        self.assertIsInstance(e.exception, ValidationError)

    def test_instantiation__just_entities(self):
        entities: List[Entity] = [MagicMock(spec=Entity)]

        result = UpdateEntitiesRequest(entities=entities)

        self.assertEqual(result.entities, entities)

    def test_instantiation__entities_and_base_bid(self):
        entities: List[Entity] = [MagicMock(spec=Entity)]

        result = UpdateEntitiesRequest(entities=entities, baseBid=1.0)
        self.assertEqual(result.entities, entities)
        self.assertEqual(result.baseBid, 1.0)
