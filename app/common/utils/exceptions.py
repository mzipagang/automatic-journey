from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from httpx import TransportError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.context.context import logging_extra_context
from app.common.exceptions import ActivationLockedException
from app.common.exceptions.campaign_exceptions import CampaignNotPublishedException
from app.common.exceptions import RateLimitExceededException
from app.common.utils import filtered_logger
from app.common.utils.context_tools import update_context

logger = filtered_logger.get_logger(__name__)


class CustomHTTPExceptionRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        return create_custom_route_handler(original_route_handler)

def create_custom_route_handler(original_route_handler: Callable[[Request], Coroutine[Any, Any, Response]]):
    async def custom_route_handler(request: Request) -> Response:
        try:
            return await original_route_handler(request)
        except StarletteHTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"msg": str(exc.detail)}
            if exc.status_code in range(400, 499):
                logger.warning(detail)
            else:
                logger.exception(detail)
            return JSONResponse(
                status_code=exc.status_code,
                content=jsonable_encoder(
                    {
                        "detail": [detail]
                    }
                ),
            )
        except TransportError:
            detail = "Network Error Occured, Please retry!"
            logger.exception(detail)
            return JSONResponse(
                status_code=504,
                content=jsonable_encoder(
                    {"detail": [{"msg": detail}]}
                ),
            )
        except RequestValidationError as exc:
            return handle_validation_exception(request, exc)
        except RateLimitExceededException as exc:
            update_context(logging_extra_context, client_id=exc.client_id)
            logger.exception("Rate limit exceeded; terminal: %s", exc,
                             extra={
                                 "monitored_transaction": "RATE-LIMIT-EXCEEDED--TERMINAL"})
            return JSONResponse(
                status_code=429,
                content=jsonable_encoder(
                    {"detail": [{"msg": "Rate limit exceeded"}]}
                ),
            )
        except ActivationLockedException as exc:
            logger.exception("Activation is locked: %s", exc)
            return JSONResponse(
                status_code=409,
                content=jsonable_encoder(
                    {"detail": [{"msg": "Activation remains locked.  Please contact support."}]}
                ),
            )
        except CampaignNotPublishedException as exc:
            update_context(logging_extra_context, campaign_id=exc.campaign_id)
            logger.exception("Campaign is not published: %s", exc.campaign_id)
            return JSONResponse(
                status_code=409,
                content=jsonable_encoder(
                    {"detail": [{"msg": "Campaign remains unpublished.  Please re-FETCH or contact support."}]}
                ),
            )
        except Exception as exc:
            logger.exception("An uncaught exception thrown: %s", exc)
            raise exc

    return custom_route_handler

class BaseResponseException(Exception):
    """Base Exception for Internal APIs."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message
        logger.warning(message)


class EmptyResponseException(BaseResponseException):
    """Raised when an Internal API is returning Empty Response."""

class ErrorResponseException(BaseResponseException):
    """Raised when an Internal API is returning Error Response."""

def handle_validation_exception(request: Request, validation_error: RequestValidationError):
    errors = validation_error.errors()
    converted_errors = list(map(convert_validation_error, errors))
    logger.debug("Validation exception for request: %s %s", request.method, request.url)
    logger.exception("A request validation exception occured: %s", converted_errors)
    return JSONResponse(
        status_code=400,
        content={"errors": converted_errors}
    )

def convert_validation_error(error):
    current_time = datetime.now(timezone.utc).isoformat()
    reason = generate_error_reason_from_validation_error(error)

    return {
        "reason": reason,
        "datetime": {
            "value": current_time,
            "timezone": "UTC"
        }
    }

def generate_error_reason_from_validation_error(error):
    location = error['loc'][1:]
    json_location = ""
    for path_part in location:
        if isinstance(path_part, int):
            json_location += f"[{path_part}]"
        else:
            json_location += f".{path_part}"

    msg = error['msg']
    return f"{json_location}: {msg}"
