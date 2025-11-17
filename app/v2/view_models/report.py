from enum import StrEnum
from typing import List

from pydantic import BaseModel, Field

from app.common.view_models.report import ReportRequestCommon, SortOrderCommon, Filter


class MetricsV2(StrEnum):
    UNIQUE_USER_CONVERSIONS = "unique_user_conversions"
    UNIQUE_USER_IMPRESSIONS = "unique_user_impressions"
    VIEWED_CVR = "viewed_conversion_rate"
    VIEWED_AVG_UNIT_PRICE = "viewed_unit_price_avg"
    CLICK_THROUGH_RATE = "click_through_rate"
    CLICKED_CONVERSION_RATE = "clicked_conversion_rate"
    CLICKED_ORDER_VALUE_AVG = "clicked_order_value_avg"
    CLICKED_UNIT_PRICE_AVG = "clicked_unit_price_avg"
    CLICKS = "clicks"
    VIEWED_ORDER_VALUE_AVG = "viewed_order_value_avg"
    COST = "cost"
    COST_PER_CLICK = "cost_per_click"
    COST_PER_TRANSACTION = "cost_per_transaction"
    COST_PER_THOUSAND = "cost_per_thousand"
    HALO_REVENUE = "halo_revenue"
    HALO_EXPOSED_REVENUE = "halo_exposed_revenue"
    HALO_ROAS = "halo_roas"
    HALO_EXPOSED_ROAS = "halo_exposed_roas"
    HALO_TRANSACTIONS = "halo_transactions"
    HALO_EXPOSED_TRANSACTIONS = "halo_exposed_transactions"
    HALO_UNITS = "halo_units"
    HALO_EXPOSED_UNITS = "halo_exposed_units"
    IMPRESSIONS = "impressions"
    AD_GROUP_BUDGET = "ad_group_budget"
    AD_GROUP_BUDGET_TYPE = "ad_group_budget_type"
    AD_GROUP_END_DATE = "ad_group_end_date"
    AD_GROUP_START_DATE = "ad_group_start_date"
    AD_GROUP_STATUS = "ad_group_status"
    CAMPAIGN_BUDGET = "campaign_budget"
    CAMPAIGN_BUDGET_TYPE = "campaign_budget_type"
    CAMPAIGN_END_DATE = "campaign_end_date"
    CAMPAIGN_START_DATE = "campaign_start_date"
    CAMPAIGN_STATUS = "campaign_status"
    PACING = "pacing"
    WIN_RATE = "win_rate"
    HOURS_LIVE = "hours_live"
    OPPORTUNITIES = "opportunities"
    SHARE_OF_VOICE = "share_of_voice"
    TIME_LIVE = "time_live"
    # Video_carousel_parameters
    VIDEO_STARTS = "video_starts"
    VIDEO_PAUSES = "video_pauses"
    VIDEO_COMPLETES = "video_completes"
    VIDEO_TOTAL_DURATION = "video_total_duration"
    VIDEO_AVERAGE_DURATION_VIEWED = "video_average_duration_viewed"
    VIDEO_FIRST_QUARTILE_VIEWS = "video_first_quartile_views"
    VIDEO_FIRST_QUARTILE_VIEW_RATE = "video_first_quartile_view_rate"
    VIDEO_SECOND_QUARTILE_VIEWS = "video_second_quartile_views"
    VIDEO_SECOND_QUARTILE_VIEW_RATE = "video_second_quartile_view_rate"
    VIDEO_THIRD_QUARTILE_VIEWS = "video_third_quartile_views"
    VIDEO_THIRD_QUARTILE_VIEW_RATE = "video_third_quartile_view_rate"
    VIDEO_COMPLETE_VIEW_RATE = "video_complete_view_rate"
    VIDEO_VIEW_THROUGH_RATE = "video_view_through_rate"

class TOAInvalidMetricsV2(StrEnum):
    SHARE_OF_VOICE = MetricsV2.SHARE_OF_VOICE
    TIME_LIVE = MetricsV2.TIME_LIVE
    WIN_RATE = MetricsV2.WIN_RATE


class DimensionsV2(StrEnum):
    PLACEMENT = "placement"
    DIVISION_BANNER = "division_banner"
    KEYWORD = "keyword"
    AD_GROUP_ID = "ad_group_id"
    AD_GROUP_NAME = "ad_group_name"
    ADVERTISER_ID = "advertiser_id"
    ADVERTISER_NAME = "advertiser_name"
    CAMPAIGN_ID = "campaign_id"
    CAMPAIGN_NAME = "campaign_name"
    CONVERSION_SOURCE = "conversion_source"
    DAILY_DATE = "daily_date"
    ENTITY_ID = "entity_id"
    ENTITY_NAME = "entity_name"
    PURCHASED_ENTITY_ID = "purchased_entity_id"
    PURCHASED_ENTITY_NAME = "purchased_entity_name"
    HOUR = "hour"
    ACCOUNTS = "accounts"
    AD_GROUP_SHORT_ID= "ad_group_short_id"
    ADVERTISER_TYPE = "advertiser_type"
    BILLINGS = "billings"
    BRAND_NAMES = "brand_names"
    CAMPAIGN_SHORT_ID = "campaign_short_id"
    EXPERIENCE_NAME = "experience_name"
    IO_LINE_ITEM_AMOUNT = "io_line_item_amount"
    IO_LINE_ITEM_NAME = "io_line_item_name"
    IO_LINE_ITEM_NUMBER = "io_line_item_number"
    IO_NAME = "io_name"
    IO_NUMBER = "io_number"
    IO_REMAINING_AMOUNT = "io_remaining_amount"
    IO_TOTAL_AMOUNT = "io_total_amount"
    MONTH_DATE = "month_date"
    PRIMARYACCOUNTNAME = "primaryAccountName"
    PURCHASE_ORDER_NUMBER = "purchase_order_number"
    WEEK_DATE = "week_date"
    COMMODITY = "commodity"
    COMMODITY_ID = "commodity_id"
    DEPARTMENT = "department"
    DEPARTMENT_ID = "department_id"
    SUB_COMMODITY = "sub_commodity"
    SUB_COMMODITY_ID = "sub_commodity_id"
    CREATIVE_KEY = "creative_key"
    CREATIVE_NAME = "creative_name"
    SEGMENT_IDS = "segment_ids"
    ENTITY_GROUP = "entity_group"
    ENTITY_GROUP_ID = "entity_group_id"

class TOAInvalidDimensionsV2(StrEnum):
    KEYWORD = DimensionsV2.KEYWORD

class CarrouselInvalidDimensionsV2(StrEnum):
    KEYWORD = DimensionsV2.KEYWORD

class SortFieldV2(BaseModel):
    field: MetricsV2 | DimensionsV2 = Field(title="field", description="The field to sort by")
    order: SortOrderCommon = Field(
        title="order", description="The order to sort by. ASC or DESC"
    )

class FilterV2(Filter):
    field: MetricsV2 | DimensionsV2 = Field(title="field", description="The field to filter by")


class ReportRequestV2(ReportRequestCommon):
    metrics: List[MetricsV2] = Field(
        title="metrics", description="The metrics to aggregate"
    )
    dimensions: List[DimensionsV2] = Field(
        title="dimensions", description="The dimensions to group by"
    )
    sort: List[SortFieldV2] = Field(title="sort", description="The sort order")
    filters: List[FilterV2] = Field(title="filters", description="The filters to apply")


class MetricsV1(StrEnum):
    CLICK_THROUGH_RATE = "click_through_rate"
    CLICKED_CONVERSION_RATE = "clicked_conversion_rate"
    CLICKED_ORDER_VALUE_AVG = "clicked_order_value_avg"
    CLICKED_UNIT_PRICE_AVG = "clicked_unit_price_avg"
    CLICKS = "clicks"
    VIEWED_ORDER_VALUE_AVG = "viewed_order_value_avg"
    COST = "cost"
    COST_PER_CLICK = "cost_per_click"
    COST_PER_TRANSACTION = "cost_per_transaction"
    COST_PER_THOUSAND = "cost_per_thousand"
    HALO_REVENUE = "halo_revenue"
    HALO_EXPOSED_REVENUE = "halo_exposed_revenue"
    HALO_ROAS = "halo_roas"
    HALO_EXPOSED_ROAS = "halo_exposed_roas"
    HALO_TRANSACTIONS = "halo_transactions"
    HALO_EXPOSED_TRANSACTIONS = "halo_exposed_transactions"
    HALO_UNITS = "halo_units"
    HALO_EXPOSED_UNITS = "halo_exposed_units"
    IMPRESSIONS = "impressions"
    AD_GROUP_BUDGET = "ad_group_budget"
    AD_GROUP_BUDGET_TYPE = "ad_group_budget_type"
    AD_GROUP_END_DATE = "ad_group_end_date"
    AD_GROUP_START_DATE = "ad_group_start_date"
    AD_GROUP_STATUS = "ad_group_status"
    CAMPAIGN_BUDGET = "campaign_budget"
    CAMPAIGN_BUDGET_TYPE = "campaign_budget_type"
    CAMPAIGN_END_DATE = "campaign_end_date"
    CAMPAIGN_START_DATE = "campaign_start_date"
    CAMPAIGN_STATUS = "campaign_status"
    PACING = "pacing"
    WIN_RATE = "win_rate"
    HOURS_LIVE = "hours_live"

class DimensionsV1(StrEnum):
    PLACEMENT = "placement"
    DIVISION_BANNER = "division_banner"
    KEYWORD = "keyword"
    AD_GROUP_ID = "ad_group_id"
    AD_GROUP_NAME = "ad_group_name"
    ADVERTISER_ID = "advertiser_id"
    ADVERTISER_NAME = "advertiser_name"
    CAMPAIGN_ID = "campaign_id"
    CAMPAIGN_NAME = "campaign_name"
    CONVERSION_SOURCE = "conversion_source"
    DAILY_DATE = "daily_date"
    ENTITY_ID = "entity_id"
    ENTITY_NAME = "entity_name"
    PURCHASED_ENTITY_ID = "purchased_entity_id"
    PURCHASED_ENTITY_NAME = "purchased_entity_name"
    HOUR = "hour"

class CarrouselInvalidDimensionsV1(StrEnum):
    KEYWORD = DimensionsV1.KEYWORD


class SortFieldV1(BaseModel):
    field: MetricsV1 | DimensionsV1 = Field(title="field", description="The field to sort by")
    order: SortOrderCommon = Field(
        title="order", description="The order to sort by. ASC or DESC"
    )

class FilterV1(Filter):
    field: MetricsV1 | DimensionsV1 = Field(title="field", description="The field to filter by")


class ReportRequestV1(ReportRequestCommon):
    metrics: List[MetricsV1] = Field(
        title="metrics", description="The metrics to aggregate"
    )
    dimensions: List[DimensionsV1] = Field(
        title="dimensions", description="The dimensions to group by"
    )
    sort: List[SortFieldV1] = Field(title="sort", description="The sort order")
    filters: List[FilterV1] = Field(title="filters", description="The filters to apply")
