from typing import Set, Dict, Optional, TypeVar, List

from pydantic import BaseModel

from app.common.view_models.report import Dimensions


class UniqueReportIds(BaseModel):
    ad_group_ids: Set[int] = set()
    advertiser_ids: Set[int] = set()
    campaign_ids: Set[int] = set()
    upcs: Set[str] = set()

class ExternalIdByKoddiId(BaseModel):
    """
    For each dictionary,
    Koddi id is the key
    and value is the external id
    """
    ad_group: Dict[int, int] = {}
    advertiser: Dict[int, int] = {}
    campaign: Dict[int, int] = {}
    upc: Dict[str, int] = {}

T = TypeVar('T')
class IdGroup[T](BaseModel):
    koddi_id: int
    long_id: Optional[str] = None
    short_id: Optional[int] = None
    data: Optional[T] = None

class MissingLookupWarning(BaseModel):
    dimension: Dimensions
    ids: List[str | int]