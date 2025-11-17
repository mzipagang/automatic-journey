from pydantic import BaseModel


class LockConfig(BaseModel):
    enabled: bool = True
    lock_prefix: str
    expire_seconds: int
