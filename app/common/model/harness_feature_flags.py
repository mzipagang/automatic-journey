from enum import StrEnum


class HarnessFeatureFlags(StrEnum):
    DISABLE_V1 = "Onsite_Partnership_KAP_API_Disable_V1"
    """
    Usage: used to toggle the availability of KAP API V1 endpoints

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Disable_V1?activeEnvironment=dev>`_
    """

    LOCKED_ACTIVATION_FETCH_RETRY = (
        "Onsite_Partnership_KAP_API_Locked_Activation_Fetch_Retry"
    )
    """
    Usage: Used in a conditional retry to check that an activation is not locked
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Locked_Activation_Fetch_Retry?activeEnvironment=dev>`_
    """

    CHECK_CAMPAIGN_PUBLICATION_STATUS = (
        "Onsite_Partnership_KAP_API_Check_Campaign_Publication_Status"
    )
    """
    Usage: Used in a conditional execute to wait for the campaign status to settle
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Check_Campaign_Publication_Status?activeEnvironment=dev>`_
    """

    UNPUBLISHED_CAMPAIGN_FETCH_RETRY = (
        "Onsite_Partnership_KAP_API_Unpublished_Campaign_Fetch_Retry"
    )
    """
    Usage: Used in a conditional retry to wait for the campaign status to settle
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Unpublished_Campaign_Fetch_Retry?activeEnvironment=dev>`_
    """

    KODDI_TOKEN_FETCH_RETRY = "Onsite_Partnership_KAP_API_Koddi_Token_Fetch_Retry"
    """
    Usage: Used in a conditional retry to continue trying to get a koddi token if we get a 503 response
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Koddi_Token_Fetch_Retry?activeEnvironment=dev>`_
    """

    ALLOW_AUTH_FROM_API_CONSUMER = (
        "Onsite_Partnership_KAP_API_Allow_auth_from_API_Consumer"
    )
    """
    Usage: Used to toggle whether we allow authorization from API consumers
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Allow_auth_from_API_Consumer?activeEnvironment=dev>`_
    """

    SKIP_INTERNAL_IDENTITY_CHECK = (
        "Onsite_Partnership_KAP_API_Skip_internal_identity_check"
    )
    """
    Usage: Used to conditionally execute internal user validation

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Skip_internal_identity_check?activeEnvironment=dev>`_
    """

    IDENTITY_CHECK_ENABLED = "Onsite_Partnership_KAP_API_Identity_check_enabled"
    """
    Usage: Used to conditionally execute user identity check

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Identity_check_enabled?activeEnvironment=dev>`_
    """

    BACKOFF_WAIT_RATE_LIMIT_CONFIG = (
        "Onsite_Partnership_KAP_API_Backoff_Wait_Rate_Limit_Config"
    )
    """
    Usage: Used to configure back off rate limiting
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Backoff_Wait_Rate_Limit_Config?activeEnvironment=dev>`_
    """

    CID_RATE_LIMIT_CONFIG = "Onsite_Partnership_KAP_API_CID_Rate_Limit_Config"
    """
    Usage: Used with the `BACKOFF_WAIT_RATE_LIMIT_CONFIG` flag to configure rate limiting by customer id
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_CID_Rate_Limit_Config?activeEnvironment=dev>`_
    """

    UPDATE_ACTIVATION_LOCK_CONFIG = (
        "Onsite_Partnership_KAP_API_Update_Activation_Lock_Config"
    )
    """
    Usage: Configures locking on activation updates
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Update_Activation_Lock_Config?activeEnvironment=dev>`_
    """

    UPDATE_CAMPAIGN_LOCK_CONFIG = (
        "Onsite_Partnership_KAP_API_Update_Campaign_Lock_Config"
    )
    """
    Usage: Configures locking on campaign updates
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Update_Campaign_Lock_Config?activeEnvironment=dev>`_
    """

    DISABLE_MULTIPLE_BRAND_IDS = "Onsite_Partnership_KAP_API_Disable_Multiple_Brand_Ids"
    """
    Usage: Used with conditionally execute to stop usage of multi-brand campaigns
    
    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/all/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Disable_Multiple_Brand_Ids?activeEnvironment=dev>`_
    """

    ASYNC_REPORT = "Onsite_Partnership_KAP_API_Async_report"
    """
    Usage: Used to toggle between using async and sync http requests for fetching reports from Koddi

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_report?activeEnvironment=dev>`_
    """

    ASYNC_CAMPAIGN = "Onsite_Partnership_KAP_API_Async_campaign"
    """
    Usage: Used to toggle between using async and sync http requests for campaign service gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_campaign?activeEnvironment=dev>`_
    """

    ASYNC_BID_MANAGER = "Onsite_Partnership_KAP_API_Async_bid_manager"
    """
    Usage: Used to toggle between using async and sync http requests for bid manager service gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_bid_manager?activeEnvironment=dev>`_
    """

    ASYNC_ACTIVATION = "Onsite_Partnership_KAP_API_Async_activation"
    """
    Usage: Used to toggle between using async and sync http requests for activation service gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_activation?activeEnvironment=dev>`_
    """

    ASYNC_DIVISION = "Onsite_Partnership_KAP_API_Async_division"
    """
    Usage: Used to toggle between async and sync http requests for division gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_division?activeEnvironment=dev>`_
    """

    ASYNC_KEYWORD_BIDDING = "Onsite_Partnership_KAP_API_Async_keyword_bidding"
    """
    Usage: Used to toggle between async and sync http requests for keyword bidding gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_keyword_bidding?activeEnvironment=dev>`_
    """

    ASYNC_PRODUCT = "Onsite_Partnership_KAP_API_Async_product"
    """
    Usage: Used to toggle between async and sync http requests for product gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_product?activeEnvironment=dev>`_
    """

    ASYNC_ENT_CLIENT = "Onsite_Partnership_KAP_API_Async_ent_client"
    """
    Usage: Used to toggle between async and sync http requests for ent client service gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_ent_client?activeEnvironment=dev>`_
    """

    ASYNC_WORKFLOW = "Onsite_Partnership_KAP_API_Async_workflow"
    """
    Usage: Used to toggle between async and sync http requests for workflow gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_workflow?activeEnvironment=dev>`_
    """

    ASYNC_CREATIVE = "Onsite_Partnership_KAP_API_Async_creative"
    """
    Usage: Used to toggle between async and sync http requests for creative service gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_creative?activeEnvironment=dev>`_
    """

    ASYNC_KODDI_SSO = "Onsite_Partnership_KAP_API_Async_koddi_sso"
    """
    Usage: Used to toggle between async and sync http requests for koddi sso gateway

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Async_koddi_sso?activeEnvironment=dev>`_
    """

    CHECK_ADGROUP_PUBLICATION_STATUS = "Onsite_Partnership_KAP_API_Check_AdGroup_Publication_Status"
    """
    Usage: Used in a conditional execute to wait for the ad group status to settle

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Check_AdGroup_Publication_Status?activeEnvironment=dev>`_
    """

    UNPUBLISHED_ADGROUP_FETCH_RETRY = "Onsite_Partnership_KAP_API_Unpublished_AdGroup_Fetch_Retry"
    """
    Usage: Used in a conditional retry to wait for the adgroup status to settle

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_Unpublished_AdGroup_Fetch_Retry?activeEnvironment=dev>`_
    """

    KODDI_ADVERTISER_CREATION_LOCK = "Onsite_Partnership_KAP_API_KODDI_Advertiser_Creation_Lock"
    """
    Usage: Used to lock koddi advertiser creation to prevent duplicates

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_KODDI_Advertiser_Creation_Lock?activeEnvironment=dev>`_
    """
    
    INCLUDE_AD_GROUP_ERRORS = "Onsite_Partnership_KAP_API_include_ad_group_errors"
    """
    Usage: Used to toggle whether include ad group errors is be enabled

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_include_ad_group_errors?activeEnvironment=dev>`_
    """

    GOAL_DATA = "Onsite_Partnership_KAP_API_Allow_Goal_Type"
    """
    Usage: Used to toggle whether include ad group errors is be enabled

    `Harness Link <https://app.harness.io/ng/account/41qEjy6URi2XdYnozuPISA/module/cf/orgs/Media/projects/Kroger_Ad_Platform/feature-flags/Onsite_Partnership_KAP_API_include_ad_group_errors?activeEnvironment=dev>`_
    """
