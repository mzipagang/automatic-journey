from pydantic import BaseModel


class RetryConfig(BaseModel):
    enabled: bool = True
    pause_seconds: int
    max_retries: int
    expire_seconds: int = 60
