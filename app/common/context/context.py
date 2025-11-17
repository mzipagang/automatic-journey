from contextvars import ContextVar

user_context = ContextVar("user_context", default={})
request_context = ContextVar("request_context", default={})
security_context = ContextVar("security_context", default={})
logging_extra_context = ContextVar("logging_extra_context", default={})
client_context = ContextVar("client_context", default={})
