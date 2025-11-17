from logging import Logger, getLogger

from app.common.logging_filters.extra_context_filter import ExtraContextFilter
from app.common.logging_filters.username_filter import UsernameFilter


def get_logger(name: str) -> Logger:
    logger = getLogger(name)
    logger.addFilter(UsernameFilter())
    logger.addFilter(ExtraContextFilter())
    return logger
