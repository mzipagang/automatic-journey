
from httpx import Client, Limits, Response

from app.common.services.config_service import Config, ConfigService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class HttpConnectionService:
    _http_client: Client
    __config: Config

    _self = None

    def __new__(cls):
        cls.__config = ConfigService().get_current_config()
        if cls._self is None:
            cls._self = super().__new__(cls)
            cls._self._http_client = Client(
                event_hooks={
                    'response': [HttpConnectionService.__log_response]},
                limits=Limits(
                    max_keepalive_connections=100,
                    max_connections=100,
                    keepalive_expiry=cls.__config.http_client_timeout_seconds))
        return cls._self

    def get_http_client(self):
        return self._http_client

    def close(self):
        self._http_client.close()

    @staticmethod
    def __log_response(response: Response):
        if response.is_success:
            return
        request = response.request
        logger.info('My HTTP Request: %s %s', request.method, request.url)

        response_body = response.read()
        duration = response.elapsed.total_seconds()
        extra = {
            "downstream_duration": duration,
            "downstream_url": response.url,
        }
        logger.info(
            'My HTTP Response: %d %s %s',
            response.status_code, response.url,
            response_body,
            extra=extra
        )
