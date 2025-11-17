from typing import TypeVar

from fastapi_cache import JsonCoder
from pydantic import BaseModel

T = TypeVar("T")

class PydanticCoderFactory[T]:
    @staticmethod
    def build(target_class: T):
        class PydanticCoder[T:BaseModel](JsonCoder):
            @classmethod
            def encode(cls, value: T) -> bytes:
                return JsonCoder.encode(value.model_dump())

            @classmethod
            def decode(cls, value: bytes) -> T:
                json_data = JsonCoder.decode(value)
                return target_class(**json_data)

        return PydanticCoder