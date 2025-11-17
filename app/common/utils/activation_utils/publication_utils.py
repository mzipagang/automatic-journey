from app.common.gateways.creative_service_gateway import CreativeServiceGateway
from app.common.utils import filtered_logger
from app.common.view_models import AdGroupStatus
from app.v2.model.downstream.activation_service import ActivationResponseV2, ActivationResponse

logger = filtered_logger.get_logger(__name__)

class ActivationPublicationUtils:
    __creative_service_gateway: CreativeServiceGateway

    def __init__(self, creative_service_gateway: CreativeServiceGateway):
        self.__creative_service_gateway = creative_service_gateway

    async def activation_is_publishable(
            self,
            activation_response: ActivationResponseV2[ActivationResponse],
            ad_group_current_status=None,
            ad_group_requested_status=None
    ) -> bool:
        if activation_response.warnings or activation_response.errors:
            logger.warning("Activation %s has validation warnings.  Publication cannot be attempted. %s",
                           activation_response.data.id, activation_response.warnings)
            return False

        activation = activation_response.data
        if ActivationPublicationUtils.__publication_is_required(
            current_status=ad_group_current_status,
            requested_status=ad_group_requested_status):
            logger.info(
                "Adgroup status is %s and the request status is %s: "
                "platform activation service will handle transition.",
                ad_group_current_status,
                ad_group_requested_status)
            return False

        if activation.is_video_carousel_activation():
            if not activation.has_creative_group_entities_ids():
                return False
            if not await self.__creative_service_gateway.creative_group_is_ready(
                    activation.channel_data.get("creativeGroupEntities")[0]):
                return False

        return activation_response.data.metadata.approved

    @staticmethod
    def __publication_is_required(current_status: AdGroupStatus, requested_status: AdGroupStatus):
        if requested_status is None or current_status is None:
            return False

        return current_status in [AdGroupStatus.ACTIVE, AdGroupStatus.PAUSED] \
                    and requested_status in [AdGroupStatus.PAUSED, AdGroupStatus.ACTIVE] \
                    and current_status != requested_status
