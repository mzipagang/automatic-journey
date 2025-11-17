from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

CONSUMER_HEADER_NAME = 'X-Consumer-Username'


def get_consumer_source(consumer: str) -> str:
    sandbox_name_suffix = " API Sandbox Consumer"
    name_suffix = " API Consumer"
    # TODO: Examine whether type suggestions would allow None without None being in signature.
    # pylint: disable=W0511
    #  Possibly re: Python 3.11 update?
    if consumer is None:
        logger.warning(
            "%s is not set in the headers, defaulting to API_PARTNER__NO_CONSUMER",
            CONSUMER_HEADER_NAME,
            extra={
                "monitored_transaction": "GET-CONSUMER-SOURCE-DEFAULT",
                "consumer": consumer,
                "default_used": "API_PARTNER__NO_CONSUMER"
            })
        source = "API_PARTNER__NO_CONSUMER"
    elif consumer in (f'Pacvue{sandbox_name_suffix}', f'Pacvue{name_suffix}'):
        source = "API_PARTNER_PACVUE"
    elif consumer in (f'Skai{sandbox_name_suffix}', f'Skai{name_suffix}'):
        source = "API_PARTNER_SKAI"
    elif consumer in (f'CommerceIQ{sandbox_name_suffix}', f'CommerceIQ{name_suffix}'):
        source = "API_PARTNER_CIQ"
    elif consumer in (f'Pepsi{sandbox_name_suffix}', f'Pepsi{name_suffix}'):
        source = "API_PARTNER_PEPSI"
    elif consumer in (f'Flywheel{sandbox_name_suffix}', f'Flywheel{name_suffix}'):
        source = "API_PARTNER_FLYWHEEL"
    else:
        logger.warning(
            "%s does not match a known entity, defaulting to PARTNER_API__UNRECOGNIZED_CONSUMER",
            CONSUMER_HEADER_NAME,
            extra={
                "monitored_transaction": "GET-CONSUMER-SOURCE-DEFAULT",
                "consumer": consumer,
                "default_used": "API_PARTNER__UNRECOGNIZED_CONSUMER"
            })
        source = "API_PARTNER__UNRECOGNIZED_CONSUMER"
    return source
