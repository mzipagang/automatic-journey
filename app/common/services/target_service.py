

from app.common.model.targets import Target, TargetTypes

from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

class TargetService:

    @staticmethod
    def get_targets():
        targets = [Target(id=1, type=TargetTypes.PLACEMENTS),
                   Target(id=2, type=TargetTypes.DIVISION),
                   Target(id=3, type=TargetTypes.HOUR)]
        return targets
