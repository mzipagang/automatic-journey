from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class AdGroupApiErrorMap:
    ERROR_MAP = {
        'activation is locked while publishing': 'Ad Group is locked while publishing'
    }

    @staticmethod
    def get_error_message(error_message):
        if error_message in AdGroupApiErrorMap.ERROR_MAP:
            return AdGroupApiErrorMap.ERROR_MAP.get(error_message, 'Unknown error')
        logger.critical('Error message not found in error map: %s', error_message)
        return None
