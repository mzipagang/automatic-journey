from typing import TypeVar, Callable, List, Tuple, Any

from fastapi import HTTPException
from httpx import Response
from httpx import codes

from app.common.services.http_client_service import _log_and_raise_on_client_error, _log_and_raise_on_upstream_error
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

T = TypeVar('T')
U = TypeVar('U')

class ResponseHandler:
    handlers: List[Tuple[
        Callable[[Response, U], bool],
        Callable[[Response, U], T]
    ]]
    default_handler: Callable[[Response, U], T]

    def __init__(self):
        self.handlers = []
        self.default_handler = self.unhandled_response

    def handle_response(self, response: Response, extra: U) -> T:
        handler = next((
            handler
            for predicate, handler in self.handlers
            if predicate(response, extra)
        ), None)

        if handler is None and self.default_handler is not None:
            return self.default_handler(response, extra)
        if handler is None:
            return self.unhandled_response(response, extra)

        return handler(response, extra)

    @staticmethod
    def unhandled_response(response: Response, extra: U) -> T:
        default_error(response, extra)

class ResponseHandlerBuilder:
    def __init__(self):
        self.response_handler = ResponseHandler()

    def handle_condition(
            self,
            predicate: Callable[[Response, U], bool],
            handler: Callable[[Response, U], T]
    ):
        self.response_handler.handlers.append((
            predicate,
            handler
        ))
        return self

    def handle_status(
            self,
            status_code: int,
            handler: Callable[[Response, U], T]
    ):
        return self.handle_condition(
            lambda response, _: response.status_code == status_code,
            handler
        )

    def handle_default(
            self,
            handler: Callable[[Response, U], T]
    ):
        self.response_handler.default_handler = handler
        return self

    def handle_success(
            self,
            handler: Callable[[Response, U], T]
    ):
        return self.handle_condition(
            lambda response, _: codes.is_success(response.status_code),
            handler
        )

    def handle_client_error(
            self,
            handler: Callable[[Response, U], T]
    ):
        return self.handle_condition(
            lambda response, _: codes.is_client_error(response.status_code),
            handler
        )

    def handle_server_error(
            self,
            handler: Callable[[Response, U], T]
    ):
        return self.handle_condition(
            lambda response, _: codes.is_server_error(response.status_code),
            handler
        )

    def handle_data(
            self,
            model: type,
    ):
        return self.handle_success(
            lambda response, _: model(**response.json())
        )

    def append_handler(
            self,
            extra_handler: ResponseHandler
    ):
        self.response_handler.handlers.extend(extra_handler.handlers)
        self.response_handler.default_handler = extra_handler.default_handler
        return self

    def build(self) -> ResponseHandler:
        return self.response_handler


def default_client_error(response: Response, extra: U):
    _log_and_raise_on_client_error(
        response=response,
        info="Error client response",
        path=response.url.path,
        forward_client_error_response_content=True)


def default_server_error(response: Response, extra: U):
    _log_and_raise_on_upstream_error(
        response=response,
        info="Error service response",
        path=response.url.path)

def default_error(response: Response, extra: U):
    logger.error(
        "Upstream service error from %s. Code: %s - Response: %s",
        response.url,
        response.status_code,
        response.content)
    raise HTTPException(status_code=500, detail="Unexpected error processing response")

DefaultResponseHandler = ResponseHandlerBuilder()\
    .handle_client_error(default_client_error) \
    .handle_server_error(default_server_error) \
    .handle_default(default_error) \
    .build()
