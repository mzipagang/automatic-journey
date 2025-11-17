from logging import Filter

from app.common.context.context import logging_extra_context


class ExtraContextFilter(Filter):
    def filter(self, record):
        extra_context = logging_extra_context.get()
        for key, value in extra_context.items():
            setattr(record, key, value)
        return True
