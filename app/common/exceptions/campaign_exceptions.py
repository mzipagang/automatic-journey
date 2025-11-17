class CampaignNotPublishedException(BaseException):
    def __init__(self, campaign_id):
        super().__init__(f"Campaign with ID {campaign_id} is not yet published.")
        self.campaign_id = campaign_id
