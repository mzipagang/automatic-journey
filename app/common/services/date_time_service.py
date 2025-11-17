from datetime import datetime


class DateTimeService:

    # TODO: Figure out how to test this functionality when it's a method inside of date_utils.py
    # pylint: disable=W0511
    @staticmethod
    def get_current_date_time() -> datetime:
        return datetime.now()
