from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


def is_valid_date(date: str) -> bool:
    """
    Check if the date is valid
    Args:
        date: The date to check

    Returns: True if the date is valid, False otherwise

    """
    try:
        datetime.strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def parse_date(date: str) -> datetime:
    """
    Parse the date string to a datetime object
    Args:
        date: The date to parse

    Returns: The datetime object

    """
    if not is_valid_date(date):
        raise HTTPException(status_code=400, detail=f"Invalid date: {date}")
    # return UTC time
    return (
        datetime.strptime(date, "%Y-%m-%d")
        .replace(tzinfo=ZoneInfo("America/New_York"))
        .astimezone(timezone.utc)
    )

def is_valid_startdate(date: str) -> bool:
    """
    Check if the campaign start date is valid. Should be today or future date
    Args:
        date: The date to check
    Returns: True if the date is valid, False otherwise
    """
    logger.debug("Inside Validating is_valid_startdate function")
    try:
        camp_start = datetime.strptime(date, '%Y-%m-%d')
        time_now = datetime.now()
        return camp_start.date() >= time_now.date()
    except ValueError:
        return False

def add_years(date: datetime, years: int) -> datetime:
    is_leap_year = date.year % 4 == 0 and (date.year % 100 != 0 or date.year % 400 == 0)
    is_leap_day = is_leap_year and date.month == 2 and date.day == 29
    if is_leap_day:
        return datetime(
            year=date.year + years,
            month=3,
            day=1,
            hour=date.hour,
            minute=date.minute,
            second=date.second,
            microsecond=date.microsecond,
            tzinfo=date.tzinfo
        )
    else:
        return datetime(
            year=date.year + years,
            month=date.month,
            day=date.day,
            hour=date.hour,
            minute=date.minute,
            second=date.second,
            microsecond=date.microsecond,
            tzinfo=date.tzinfo
        )

def is_not_valid_time_frame_create_campaign_today(request) -> bool:
    """
    Check if the campaign time frame is valid for creating a campaign today.
    The start date should be today but the current time should not be between 8 PM ET and 12 AM ET (midnight).
    Returns: True if the time frame is not valid, False otherwise
    """
    est_timezone = ZoneInfo("America/New_York")

    start_date = request._json.get("startDate")
    date_now = datetime.now(est_timezone).date().strftime("%Y-%m-%d")
    if date_now == start_date:
        current_est_time = datetime.now(est_timezone).time().replace(microsecond=0)
        cutoff_lb = time(20, 0, 0)  # 8 PM ET
        cutoff_ub = time(23, 59, 59)  # 12 AM ET (midnight)
        if cutoff_lb <= current_est_time <= cutoff_ub:
            return True
    return False