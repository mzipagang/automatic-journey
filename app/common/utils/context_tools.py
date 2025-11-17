from contextvars import ContextVar
from typing import List

from app.common.context.context import logging_extra_context, security_context, client_context, user_context, \
    request_context


def update_context(context_var: ContextVar, **kwargs):
    context_var.set({**context_var.get(), **kwargs})


def clear_all_context_vars():
    context_vars: List[ContextVar] = [
        client_context,
        logging_extra_context,
        request_context,
        security_context,
        user_context
    ]

    for context_var in context_vars:
        context_var.set(dict())
