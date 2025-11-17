from fastapi import HTTPException

from app.common.context.context import logging_extra_context
from app.common.exceptions.activation_exceptions import ActivationLockedException, AdGroupNotPublishedException
from app.common.exceptions.campaign_exceptions import CampaignNotPublishedException
from app.common.exceptions.predicate_exceptions import RateLimitExceededException
from app.common.utils.context_tools import update_context
from app.common.utils.filtered_logger import get_logger


def koddi_token_fetch_failed_503(exception: BaseException) -> bool:
    return isinstance(exception, HTTPException) and exception.status_code == 503

def activation_is_locked(exception: BaseException) -> bool:
    return isinstance(exception, ActivationLockedException)

def ad_group_is_not_published(exception: BaseException) -> bool:
    return isinstance(exception, AdGroupNotPublishedException)

def campaign_is_not_published(exception: BaseException) -> bool:
    return isinstance(exception, CampaignNotPublishedException)

async def rate_limit_exceeded(exception: BaseException) -> bool:
    if isinstance(exception, RateLimitExceededException):
        update_context(logging_extra_context, client_id=exception.client_id)
        logger = get_logger(__name__)
        logger.warning("Rate limit exceeded; non-terminal",
                       extra={
                           "monitored_transaction": "RATE-LIMIT-EXCEEDED--NON-TERMINAL"})

        return True
    return False
