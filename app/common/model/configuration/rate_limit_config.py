from pydantic import BaseModel


class RateLimitConfig(BaseModel):
    enabled: bool = True
    requests_per_minute: int
    rate_limit_prefix: str
