from copy import deepcopy
from datetime import datetime

from app.common.view_models import SingleResponse, AdGroup, ListResponse
from app.v2.view_models import Campaign
from app.common.model.shared import EntityMeta, PublishStatus, Meta, Page

CAMPAIGN = Campaign(id=1,
                  name='Test Campaign',
                  status='DRAFT',
                  campaignType='PLA',
                  startDate='2021-01-01',
                  endDate=None,
                  budgetAmount=1000.0,
                  budgetType='DAILY',
                  pacingType='EVEN',
                  accountId=1,
                  advertiserIds=[1, 2],
                  billingInsertionOrder='IO-001',
                  billingPurchaseOrder='PO-001',
                  billingAdditionalDetails='',
                  billingContactId=1,
                  billingAddressId=None,
                  adGroups=None,
                  isArchived=False)

CAMPAIGN_SINGLE_RESPONSE = SingleResponse[Campaign](
    data=CAMPAIGN,
    meta=EntityMeta(success=True, message=None, code=None, publishStatus=PublishStatus.PUBLISHED))

CAMPAIGN_LIST_RESPONSE = ListResponse[Campaign](
    data=[CAMPAIGN],
    meta=Meta(page=Page(offset=0, size=10, hasMore=False)))

CAMPAIGN_SINGLE_RESPONSE_WITH_AD_GROUPS = deepcopy(CAMPAIGN_SINGLE_RESPONSE)
CAMPAIGN_SINGLE_RESPONSE_WITH_AD_GROUPS.data.adGroups = [
    AdGroup(adGroupId=1,
            campaignId=1,
            name='Test AdGroup',
            startDate=CAMPAIGN_SINGLE_RESPONSE.data.startDate,
            endDate=datetime.now().strftime('%Y-%m-%d'),
            budgetType='DAILY',
            budgetAmount=1000.0,
            status='DRAFT',
            baseBid=1.0,
            entities=[],
            targets=[],
            keywordBidModifiers=[])]
