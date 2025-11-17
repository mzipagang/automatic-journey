from fastapi import HTTPException
from httpx import Response
from httpx import codes as httpx_codes

from app.common.configuration.constants import KODDI_SSO_SERVICE_JWT_PATH
from app.common.utils.filtered_logger import get_logger

logger = get_logger(__name__)


def process_koddi_token_response(response: Response) -> str:
    """Process the response from Koddi token endpoint and return the token string.
    
    Args:
        response: The HTTP response from the Koddi token endpoint
        
    Returns:
        The token string from the response content
        
    Raises:
        HTTPException: If the response indicates an error
    """
    logger.info("Koddi token response. Code: %s", response.status_code)

    if httpx_codes.is_success(response.status_code):
        if response.content is not None:
            return str(response.content, 'utf-8')
        logger.error(
            "Malformed response from Koddi at %s. Code: %s - Response: %s",
            KODDI_SSO_SERVICE_JWT_PATH,
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

    elif httpx_codes.is_server_error(response.status_code):
        logger.error(
            "Error fetching Koddi token at %s. Code: %s - Response: %s",
            KODDI_SSO_SERVICE_JWT_PATH,
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

    elif httpx_codes.is_client_error(response.status_code):
        logger.error("Get Koddi Token Code: %s - Response: %s", response.status_code, response.content)
        raise HTTPException(status_code=response.status_code)

    logger.error("Get Koddi Token Code: %s - Response: %s", response.status_code, response.content)
    raise HTTPException(status_code=500, detail="Unexpected error fetching Reporting token")

