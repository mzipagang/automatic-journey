from enum import StrEnum

class AuthRole(StrEnum):
    ADVERTISER_API = "Advertiser API"
    REPORTING_API = "Reporting API"
    NONEXISTENT_ROLE = "Nonexistent role"
    OTHER_ROLE = "Other Role"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, AuthRole):
            return cls(value)
        return cls("Other Role")