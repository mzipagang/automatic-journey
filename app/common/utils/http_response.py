from json import JSONDecodeError

from fastapi import HTTPException
from httpx import Response
from httpx import codes as httpx_codes

from app.common.configuration.constants import KODDI_SSO_SERVICE_JWT_PATH
from app.common.utils.filtered_logger import get_logger

logger = get_logger(__name__)


def process_koddi_token_response(response: Response) -> str:
    """Process the response from Koddi token endpoint and return the token string."""
    logger.info("Koddi token response. Code: %s", response.status_code)

    if httpx_codes.is_success(response.status_code):
        if response.content is not None:
            return str(response.content, 'utf-8')
        _log_and_raise_on_upstream_error(
            response=response,
            info="Malformed response from Koddi",
            path=KODDI_SSO_SERVICE_JWT_PATH)

    elif httpx_codes.is_server_error(response.status_code):
        _log_and_raise_on_upstream_error(
            response=response,
            info="Error fetching Koddi token",
            path=KODDI_SSO_SERVICE_JWT_PATH)

    elif httpx_codes.is_client_error(response.status_code):
        _log_and_raise_on_client_error(
            response=response,
            info="Get Koddi Token Code",
            path=KODDI_SSO_SERVICE_JWT_PATH,
            forward_client_error_response_content=False)

    logger.error("Get Koddi Token Code: %s - Response: %s", response.status_code, response.content)
    raise HTTPException(status_code=500, detail="Unexpected error fetching Reporting token")


def process_json_response(
    response: Response,
    json_has_data_field: bool = False,
    forward_client_error_response_content: bool = False
) -> Response:
    """Process a JSON HTTP response, validating structure and handling errors."""
    if httpx_codes.is_success(response.status_code):
        try:
            json_data = response.json()
        except JSONDecodeError:
            json_data = None

        if json_data is not None and (not json_has_data_field or 'data' in json_data):
            return response

        _log_and_raise_on_upstream_error(
            response=response,
            info="Malformed response",
            path=response.url.path)

    elif httpx_codes.is_server_error(response.status_code):
        _log_and_raise_on_upstream_error(
            response=response,
            info="Error service response",
            path=response.url.path)

    elif httpx_codes.is_client_error(response.status_code):
        _log_and_raise_on_client_error(
            response=response,
            info="Error client response",
            path=response.url.path,
            forward_client_error_response_content=forward_client_error_response_content)

    else:
        logger.error(
            "Upstream service error from %s. Code: %s - Response: %s",
            response.url,
            response.status_code,
            response.content)
        raise HTTPException(status_code=500, detail="Unexpected error processing JSON response")


def _log_and_raise_on_upstream_error(response: Response, info: str, path: str):
    """Log and raise an HTTPException for upstream server errors."""
    logger.error(
        "%s at %s.  Code: %s - Response: %s",
        info,
        path,
        response.status_code,
        response.content,
        extra={
            'monitored_transaction': 'HTTP-UPSTREAM-ERROR--SERVICE-ERROR-RESPONSE',
            'response': response.content,
            'response_code': response.status_code
        }
    )
    raise HTTPException(
        status_code=503,
        detail="Temporary service error.  Please try again.",
        headers={"Retry-After": "5"})


def _log_and_raise_on_client_error(
    response: Response,
    info: str,
    path: str,
    forward_client_error_response_content: bool = False
):
    """Log and raise an HTTPException for client errors."""
    logger.warning(
        "%s at %s.  Code: %s - Response: %s",
        info,
        path,
        response.status_code,
        response.content,
        extra={
            'monitored_transaction': 'HTTP-UPSTREAM-ERROR--CLIENT-ERROR-RESPONSE',
            'response': response.content,
            'response_code': response.status_code
        }
    )
    if forward_client_error_response_content:
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                detail_content = response.json()
            except (JSONDecodeError, ValueError):
                detail_content = response.text
        else:
            detail_content = response.text
        raise HTTPException(status_code=response.status_code, detail=detail_content)
    raise HTTPException(status_code=response.status_code)
