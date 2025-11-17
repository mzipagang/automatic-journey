from pydantic import BaseModel


class CacheConfig(BaseModel):
    enabled: bool = True
    ttl: int = 0
