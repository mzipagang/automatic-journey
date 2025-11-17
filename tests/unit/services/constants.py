from app.common.model.product import Product
from app.common.model.shared import (
    BudgetType,
    EntityMeta,
    PublishStatus,
    UpstreamValidationWarning,
    Warnings,
)
from app.common.model.targets import TargetAdgroupRequest
from app.common.services.config_service import Config
from app.common.view_models import AdGroup, Entity
from app.common.view_models.report import Pagination, SortOrderCommon
from app.v2.view_models import AdGroupStatus, AdGroupUpdateRequest, Campaign
from app.v2.view_models.report import MetricsV1, ReportRequestV1, SortFieldV1, DimensionsV1
from app.v2.view_models import AdGroupRequest
from app.v2.view_models.report import MetricsV2, ReportRequestV2, SortFieldV2, DimensionsV2

FETCHED_PLA_RECOMMENDATIONS = {
    "data": {
        "pla_bid_range": {
            "minimum_value": 0.3,
            "maximum_value": 0.5,
        },
        "found": [
            {
                "bidReferenceId": "1234",
                "type": "pla",
                "pla_recommendations": [
                    {
                        "id": "0001200017023",
                        "name": "Amp Energy Organic Pineapple & Coconut Drink",
                        "department": "Beverages",
                        "commodity": "Energy Drinks",
                        "price": 0,
                        "use_base_bid": False,
                        "bid_amount": 0.3,
                        "suggested_bid": {
                            "minimum_value": None,
                            "maximum_value": None
                        },
                        "sub_commodity": "Caffeinated Energy Drinks"
                    }
                ],
                "pla_bid_range": {
                    "minimum_value": 0.3,
                    "maximum_value": 0.4
                },
                "default_bid": 0.3
            }
        ],
        "notFound": []
    },
    "meta": {
        "page": {
            "total_size": 1
        }
    }
}


NON_PLA_RECOMMENDATIONS = {
    'data': {
        'type': 'toa',
        'pla_recommendations': [
            {
                'id': '0001200017023',
                'name': 'Amp Energy Organic Pineapple & Coconut Drink',
                'department': 'Beverages',
                'commodity': 'Energy Drinks',
                'price': 0,
                'use_base_bid': False,
                'bid_amount': 0.3,
                'suggested_bid': {
                    'minimum_value': None,
                    'maximum_value': None
                },
                'sub_commodity': 'Caffeinated Energy Drinks'
            },
        ],
        'pla_bid_range': {
            'minimum_value': 0.30000001192092896,
            'maximum_value': 0.4000000059604645
        },
        'toa_recommendations': None,
        'default_bid': 0.3
    },
    'meta': {
        'page': {
            'total_size': 1
        }
    }
}

AD_GROUP = {
    "campaignId": 131,
    "name": "Test Ad Group",
    "startDate": "2024-05-20",
    "endDate": "2024-06-20",
    "budgetType": "Monthly",
    "budgetAmount": 250,
    "status": "DRAFT",
    "baseBid": 2.50,
    "entities": [],
    "targets": []
}

AD_GROUP_REQUEST = AdGroupRequest(
    campaignId=131,
    name="Test Ad Group",
    startDate="2024-05-20",
    endDate="2024-06-20",
    budgetAmount=250,
    status=AdGroupStatus.DRAFT,
    baseBid=2.50,
    entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
    targets=[TargetAdgroupRequest(type=1, values=[1, 2])]
)

AD_GROUP_UPDATE_REQUEST = AdGroupUpdateRequest(
    name="Test Ad Group",
    startDate="2024-07-03",
    endDate="2024-10-25",
    budgetAmount=250,
    status=AdGroupStatus.ACTIVE,
    targets=[TargetAdgroupRequest(type=1, values=[1, 2])]
)

CAROUSEL_AD_GROUP_UPDATE_REQUEST_WITH_PLACEMENT = AdGroupUpdateRequest(
    name="Test Ad Group",
    budgetAmount=250,
    status=AdGroupStatus.ACTIVE,
    targets=[TargetAdgroupRequest(type=1, values=[1, 2])]
)

CAROUSEL_AD_GROUP_UPDATE_REQUEST_WITH_DAYPARTING = AdGroupUpdateRequest(
    name="Test Ad Group",
    budgetAmount=250,
    status=AdGroupStatus.ACTIVE,
    targets=[TargetAdgroupRequest(type=3, values=[1, 2])]
)

SIMPLE_AD_GROUP_UPDATE_REQUEST = AdGroupUpdateRequest(
    name="Updated Test Ad Group"
)

STATUS_ACTIVE_AD_GROUP_UPDATE_REQUEST = AdGroupUpdateRequest(
    status=AdGroupStatus.ACTIVE
)
UPDATED_AD_GROUP_RESPONSE_DICT = {
    "data": {
        "adGroupId": 31,
        "baseBid": 2.5,
        "budgetAmount": 250,
        "budgetType": "MONTHLY",
        "campaignId": 32,
        "endDate": "2024-06-20",
        "entities": [
            {
                "bidAmount": 0.3,
                "deleted": False,
                "id": 1,
                "useBaseBid": False
            },
            {
                "bidAmount": 0.3,
                "deleted": False,
                "id": 3,
                "useBaseBid": False
            }
        ],
        "isArchived": False,
        "keywordBidModifiers": [],
        "name": "Test Ad Group",
        "startDate": "2024-05-20",
        "status": "ACTIVE",
        "targets": [
            {
                "id": 4,
                "type": "1",
                "values": None
            },
            {
                "id": 5,
                "type": "2",
                "values": None
            },
            {
                "id": 6,
                "type": "2",
                "values": None
            },
            {
                "id": 7,
                "type": "2",
                "values": None
            },
            {
                "id": 8,
                "type": "2",
                "values": None
            },
            {
                "id": 9,
                "type": "2",
                "values": None
            },
            {
                "id": 10,
                "type": "2",
                "values": None
            },
            {
                "id": 11,
                "type": "2",
                "values": None
            },
            {
                "id": 12,
                "type": "2",
                "values": None
            },
            {
                "id": 13,
                "type": "2",
                "values": None
            },
            {
                "id": 14,
                "type": "2",
                "values": None
            },
            {
                "id": 15,
                "type": "2",
                "values": None
            },
            {
                "id": 16,
                "type": "2",
                "values": None
            },
            {
                "id": 17,
                "type": "2",
                "values": None
            },
            {
                "id": 18,
                "type": "2",
                "values": None
            },
            {
                "id": 19,
                "type": "2",
                "values": None
            },
            {
                "id": 20,
                "type": "2",
                "values": None
            },
            {
                "id": 21,
                "type": "2",
                "values": None
            },
            {
                "id": 22,
                "type": "2",
                "values": None
            },
            {
                "id": 23,
                "type": "2",
                "values": None
            },
            {
                "id": 24,
                "type": "2",
                "values": None
            },
            {
                "id": 25,
                "type": "2",
                "values": None
            },
            {
                "id": 26,
                "type": "2",
                "values": None
            },
            {
                "id": 27,
                "type": "2",
                "values": None
            },
            {
                "id": 28,
                "type": "2",
                "values": None
            },
            {
                "id": 29,
                "type": "2",
                "values": None
            },
            {
                "id": 30,
                "type": "2",
                "values": None
            }
        ]
    },
    "meta": {
        "code": None,
        "message": None,
        "publishStatus": "PENDING",
        "success": True,
        "warnings": {
            "validation": []
        },
        "errors": []
    }
}
SIMPLE_AD_GROUP = AdGroup(
    adGroupId=123,
    campaignId=131,
    name="Test Ad Group",
    startDate="2024-05-20",
    endDate="2024-06-20",
    budgetType=BudgetType.MONTHLY,
    budgetAmount=250,
    status="DRAFT",
    baseBid=2.50,
    entities=[],
    targets=[],
    keywordBidModifiers=[]
)

CAMPAIGN = Campaign(
    adGroups=[],
    id=131,
    name="Test Campaign",
    status="DRAFT",
    startDate="2024-05-20",
    endDate="2024-06-20",
    budgetAmount=250,
    budgetType="Monthly",
    pacingType="Even",
    accountId=1,
    advertiserIds=[1],
    billingInsertionOrder="",
    billingPurchaseOrder="",
    billingAdditionalDetails="",
    billingContactId=1,
    billingAddressId=1
)
SIMPLE_CONFIG = Config(
    base_koddi_url="http://koddi.invalid",
    base_api_url="http://api.invalid",
    product_id="abcdefg12345",
    pte_target_id="12345"
)

FETCHED_PRODUCT_PRICES_RESPONSE_JSON = {
    "data": {
        "productPrices": [
            {
                "productId": "0001200017023",
                "price": {
                    "average": 2.698436724565757,
                    "min": 1.99,
                    "max": 3.29,
                    "mode": 2.69
                }
            },
            {
                "productId": "0001200001643",
                "price": {
                    "average": 2.6883792544570544,
                    "min": 2.19,
                    "max": 2.69,
                    "mode": 2.69
                }
            },
            {
                "productId": "0001200012635",
                "price": {
                    "average": 1.99,
                    "min": 1.99,
                    "max": 1.99,
                    "mode": 1.99
                }
            }
        ],
        "noPriceProducts": [
            "0001200001756"
        ]
    }
}

FETCHED_PRODUCT_BIDS_RESPONSE_JSON = {
    "data": {
        "suggestions": [
            {
                "id": "0001200017023",
                "bid_information": {
                    "lowest_bid": 1.0,
                    "highest_bid": 10.0
                }
            },
            {
                "id": "0001200001643",
                "bid_information": {
                    "lowest_bid": 2.0,
                    "highest_bid": 9.0
                }
            },
            {
                "id": "0001200012635",
                "bid_information": {
                    "lowest_bid": 3.0,
                    "highest_bid": 8.0
                }
            }
        ]
    }
}

FETCHED_RAW_PRODUCTS_RESPONSE_JSON = {
    "data": [
        {
            "upc": "0001200017023",
            "description": "Amp Energy Organic Pineapple & Coconut Drink",
            "price": 0,
            "brand": "Amp Energy",
            "taxonomy": {
                "department": {
                    "id": "4",
                    "name": "Beverages"
                },
                "commodity": {
                    "id": "4011",
                    "name": "Energy Drinks"
                },
                "subCommodity": {
                    "id": "401100001",
                    "name": "Caffeinated Energy Drinks"
                }
            },
            "isValid": True
        },
        {
            "upc": "0001200001643",
            "description": "Mountain Dew® Amp® Original Energy Drink",
            "price": 0,
            "brand": "Amp Energy",
            "taxonomy": {
                "department": {
                    "id": "4",
                    "name": "Beverages"
                },
                "commodity": {
                    "id": "4011",
                    "name": "Energy Drinks"
                },
                "subCommodity": {
                    "id": "401100001",
                    "name": "Caffeinated Energy Drinks"
                }
            },
            "isValid": True
        },
        {
            "upc": "0001200012635",
            "description": "Mountain Dew Amp Cherry Blast Energy Drink",
            "price": 0,
            "brand": "Amp Energy",
            "taxonomy": {
                "department": {
                    "id": "4",
                    "name": "Beverages"
                },
                "commodity": {
                    "id": "4011",
                    "name": "Energy Drinks"
                },
                "subCommodity": {
                    "id": "401100001",
                    "name": "Caffeinated Energy Drinks"
                }
            },
            "isValid": True
        },
        {
            "upc": "0001200001756",
            "description": "Amp Energy Original Citrus Flavored Energy Drink",
            "price": 0,
            "brand": "Amp Energy",
            "taxonomy": {
                "department": {
                    "id": "4",
                    "name": "Beverages"
                },
                "commodity": {
                    "id": "4011",
                    "name": "Energy Drinks"
                },
                "subCommodity": {
                    "id": "401100001",
                    "name": "Caffeinated Energy Drinks"
                }
            },
            "isValid": True
        }
    ],
    "meta": {
        "page": {
            "totalCount": 4,
            "offset": 0,
            "size": 10
        }
    }
}

TEST_PRODUCTS = [
    Product(
        id=0,
        upc='0001200017023',
        name='Amp Energy Organic Pineapple & Coconut Drink',
        packshot='https://www.kroger.com/product/images/medium/front/0001200017023',
        price=2.698436724565757,
        maxSuggestedBid=1.0,
        minSuggestedBid=0.5,
        brand='Amp Energy',
        category='Energy Drinks',
        subcategory='Caffeinated Energy Drinks',
        available=True

    ),
    Product(
        id=1,
        upc='0001200001643',
        name='Mountain Dew® Amp® Original Energy Drink',
        packshot='https://www.kroger.com/product/images/medium/front/0001200001643',
        price=2.6883792544570544,
        maxSuggestedBid=0.8,
        minSuggestedBid=0.3,
        brand='Amp Energy',
        category='Energy Drinks',
        subcategory='Caffeinated Energy Drinks',
        available=True
    ),
    Product(
        id=2,
        upc='0001200012635',
        name='Mountain Dew Amp Cherry Blast Energy Drink',
        packshot='https://www.kroger.com/product/images/medium/front/0001200012635',
        price=1.99,
        maxSuggestedBid=0.0,
        minSuggestedBid=0.0,
        brand='Amp Energy',
        category='Energy Drinks',
        subcategory='Caffeinated Energy Drinks',
        available=True
    ),
    Product(
        id=3,
        upc='0001200001756',
        name='Amp Energy Original Citrus Flavored Energy Drink',
        packshot='https://www.kroger.com/product/images/medium/front/0001200001756',
        price=0.0,
        maxSuggestedBid=0.0,
        minSuggestedBid=0.0,
        brand='Amp Energy',
        category='Energy Drinks',
        subcategory='Caffeinated Energy Drinks',
        available=True
    )
]

CAMPAIGNS_SINGLE_RESPONSE = {
    "data": {
        "publishedChanges": {
            "activations": ["66954c00baa2da50653861f4"],
            "additionalBillingDetails": None,
            "backgroundInformation": "API Campaign ID: 14979",
            "budget": {"amount": 200001, "pacingType": "EVEN", "type": "MONTHLY"},
            "clickThroughDestinations": [],
            "created": "2024-07-15T16:16:02.828Z",
            "createdBy": "bef01383-36ae-4eb8-a531-aae013e4d3df",
            "createdByUser": "Venkata Anne",
            "endDate": "2024-10-25T04:00:00Z",
            "externalIDs": [
                {"id": 452817, "partner": "KODDI_ADVERTISER_ID"},
                {"id": 1315921, "partner": "KODDI_CAMPAIGN_ID"},
            ],
            "id": "66954b42071fd2c0734ee09e",
            "internalContacts": [
                {"id": "0054V00000FbmVwQAJ", "type": "ACCOUNT_EXECUTIVE"},
                {"id": "0053A00000EB3wgQAD", "type": "PRIMARY_ACCOUNT_MANAGER"},
            ],
            "isAlwaysOn": False,
            "lastModified": "2024-08-06T19:13:13.876Z",
            "lastModifiedBy": "bef01383-36ae-4eb8-a531-aae013e4d3df",
            "lastModifiedByUser": "Venkata Anne",
            "name": "Test Campaign",
            "notesForAccounting": None,
            "partnerAccounts": [],
            "primaryAccount": {
                "addresses": [
                    {"id": "a064V00000pNkuDQAS", "type": "CORPORATE"},
                    {"id": "a064V00000XLQeOQAX", "type": "ALTERNATE"},
                ],
                "agency": {
                    "billingInfo": {
                        "budgetShare": 0,
                        "ioLastModified": "0001-01-01T00:00:00Z",
                        "ioLastModifiedBy": "",
                        "ioLineItemId": 0,
                        "ioLineItemLastModified": "0001-01-01T00:00:00Z",
                        "ioLineItemLastModifiedBy": "",
                        "ioNumber": "",
                        "ioNumberId": 0,
                        "isBeingBilled": False,
                        "isIORequired": False,
                        "isPORequired": False,
                        "poLastModified": "0001-01-01T00:00:00Z",
                        "poLastModifiedBy": "",
                        "poNumber": "",
                    },
                    "id": "00000000-0000-0000-0000-000000000000",
                },
                "billingInfo": {
                    "budgetShare": 100,
                    "ioLastModified": "0001-01-01T00:00:00Z",
                    "ioLastModifiedBy": "",
                    "ioLineItemId": 0,
                    "ioLineItemLastModified": "0001-01-01T00:00:00Z",
                    "ioLineItemLastModifiedBy": "",
                    "ioNumber": "",
                    "ioNumberId": 0,
                    "isBeingBilled": True,
                    "isIORequired": False,
                    "isPORequired": False,
                    "poLastModified": "0001-01-01T00:00:00Z",
                    "poLastModifiedBy": "",
                    "poNumber": "",
                },
                "brands": ["89389c53-4b53-4838-8f61-02222c3e425c"],
                "contacts": [
                    {"id": "0034V00002khcwaQAA", "type": "billing-contact"},
                    {"id": "0034V00002khcwaQAA", "type": "creative-contact"},
                    {"id": "0034V00002khcwaQAA", "type": "primary-client-contact"},
                ],
                "id": "75e9ae8f-e1e1-458b-8bad-fc71d2ed8ffe",
                "isAgencyBeingInvolved": False,
            },
            "shortId": "14979",
            "source": "MEDIA_ACTIVATION_PLATFORM",
            "startDate": "2024-07-15T04:00:00Z",
            "status": "ACTIVE",
            "type": "PLA",
            "version": 20,
        },
        "publishingStatus": "IN_PROGRESS",
    },
    "meta": {"page": {"hasMore": False, "offset": 0, "size": 30, "totalCount": 1, "totalPages": 1}},
}

FETCHED_RAW_CAMPAIGNS_PAGINATED_RESPONSE = {
    "data": [
        {
            "activations": ["664ce8f143bf95e60a0e783e"],
            "additionalBillingDetails": None,
            "backgroundInformation": None,
            "budget": {
                "amount": 10000,
                "pacingType": "EVEN",
                "type": "MONTHLY"
            },
            "created": "2024-05-21T20:16:20.03Z",
            "startDate": "2024-05-21T20:16:21.413Z",
            "endDate": "2024-06-30T04:00:00Z",
            "id": "664d01148c5c748238432d82",
            "name": "Pepsi Campaign",
            "status": "DRAFT",
            "type": "PLA",
            "primaryAccount": {
                "id": "3b5c15a3-008e-4591-82be-26e06b913733",
                "isAgencyBeingInvolved": False,
                "brands": [
                    "0a849f1f-f866-4cfe-ad2a-f48f8daf9de2"
                ],
                "billingInfo": {
                    "poNumber": ""
                },
                "contacts": [
                    {
                        "id": "0033000001tUxExAAK",
                        "type": "primary-client-contact"
                    },
                    {
                        "id": "0034V000050EdgcQAC",
                        "type": "billing-contact"
                    },
                    {
                        "id": "0034V00004xnz4yQAA",
                        "type": "creative-contact"
                    }
                ],
                "addresses": [
                    {
                        "id": "a064V00000XnG1WQAV",
                        "type": "CORPORATE"
                    },
                    {
                        "id": "a064V00000XnG1WQAV",
                        "type": "ALTERNATE"
                    }
                ]
            }
        },
        {
            "activations": ["664ce8f143bf95e60a0e783e"],
            "additionalBillingDetails": None,
            "backgroundInformation": None,
            "budget": {
                "amount": 222,
                "pacingType": "EVEN",
                "type": "DAILY"
            },
            "created": "2024-05-21T18:21:59.503Z",
            "startDate": "2024-05-21T18:21:59.736Z",
            "endDate": None,
            "id": "664ce64764590b33acafb5d4",
            "name": "dcda",
            "status": "DRAFT",
            "type": "PLA",
            "primaryAccount": {
                "id": "3b5c15a3-008e-4591-82be-26e06b913733",
                "isAgencyBeingInvolved": False,
                "brands": [
                    "0a849f1f-f866-4cfe-ad2a-f48f8daf9de2"
                ],
                "billingInfo": {
                    "poNumber": ""
                },
                "contacts": [
                    {
                        "id": "0033000001tUxExAAK",
                        "type": "primary-client-contact"
                    },
                    {
                        "id": "0034V000050EdgcQAC",
                        "type": "billing-contact"
                    },
                    {
                        "id": "0034V00004xnz4yQAA",
                        "type": "creative-contact"
                    }
                ],
                "addresses": [
                    {
                        "id": "a064V00000XnG1WQAV",
                        "type": "CORPORATE"
                    },
                    {
                        "id": "a064V00000XnG1WQAV",
                        "type": "ALTERNATE"
                    }
                ],
            }
        },
        {
            "activations": ["664ce8f143bf95e60a0e783e"],
            "additionalBillingDetails": None,
            "backgroundInformation": None,
            "budget": {
                "amount": 222,
                "pacingType": "EVEN",
                "type": "DAILY"
            },
            "created": "2024-05-21T18:21:59.503Z",
            "startDate": "2024-05-21T18:21:59.736Z",
            "endDate": None,
            "id": "664ce64764590b33acafb5d5",
            "name": "dcda",
            "status": "DRAFT",
            "type": "PLA",
            "primaryAccount": {
                "id": "3b5c15a3-008e-4591-82be-26e06b913733",
                "isAgencyBeingInvolved": False,
                "brands": [
                    "wrongbrand"
                ],
                "billingInfo": {
                    "poNumber": ""
                },
                "contacts": [
                    {
                        "id": "0033000001tUxExAAK",
                        "type": "primary-client-contact"
                    },
                    {
                        "id": "0034V000050EdgcQAC",
                        "type": "billing-contact"
                    },
                    {
                        "id": "0034V00004xnz4yQAA",
                        "type": "creative-contact"
                    }
                ],
                "addresses": [
                    {
                        "id": "a064V00000XnG1WQAV",
                        "type": "CORPORATE"
                    },
                    {
                        "id": "a064V00000XnG1WQAV",
                        "type": "ALTERNATE"
                    }
                ],
            }

        }
    ],
    "meta": {
        "page": {
            "hasMore": False,
            "offset": 0,
            "size": 3,
            "totalCount": 3,
            "totalPages": 1
        }
    }
}

DIVISION_BANNERS_RESPONSE_JSON = {
    "id": "1c4bd227-424c-42e0-b0cd-2cb56b45bbe5",
    "categories": [
        {
            "type": "division-banner",
            "items": [
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "011"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "014"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "016"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "018"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "021"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "024"
                },
                {
                    "bannerCode": "JAYC",
                    "divisionNumber": "024"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "025"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "026"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "029"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "034"
                },
                {
                    "bannerCode": "KROGER",
                    "divisionNumber": "035"
                },
                {
                    "bannerCode": "HART",
                    "divisionNumber": "097"
                },
                {
                    "bannerCode": "MARIANOS",
                    "divisionNumber": "531"
                },
                {
                    "bannerCode": "METRO MARKET",
                    "divisionNumber": "534"
                },
                {
                    "bannerCode": "PICK N SAVE",
                    "divisionNumber": "534"
                },
                {
                    "bannerCode": "BAKERS",
                    "divisionNumber": "615"
                },
                {
                    "bannerCode": "DILLONS",
                    "divisionNumber": "615"
                },
                {
                    "bannerCode": "GERBES",
                    "divisionNumber": "615"
                },
                {
                    "bannerCode": "CITYMARKET",
                    "divisionNumber": "620"
                },
                {
                    "bannerCode": "KINGSOOPERS",
                    "divisionNumber": "620"
                },
                {
                    "bannerCode": "FRYS",
                    "divisionNumber": "660"
                },
                {
                    "bannerCode": "FRED",
                    "divisionNumber": "701"
                },
                {
                    "bannerCode": "RALPHS",
                    "divisionNumber": "703"
                },
                {
                    "bannerCode": "QFC",
                    "divisionNumber": "705"
                },
                {
                    "bannerCode": "SMITHS",
                    "divisionNumber": "706"
                }
            ]
        }
    ]
}

CHANNEL_CONFIG_RESPONSE_JSON = {
    "id": "649203c18832c81dea03a7f9",
    "version": 1,
    "key": "PLA-1",
    "name": "Product Listing Ad",
    "description": "Product Listing Ads appear in the search results and other personalized carousels on Kroger.com and the mobile app. Boost your SKUs and coupons to increase engagement and drive sales.",
    "channelOfferings": [
        "ssonsite"
    ],
    "active": True,
    "createdAt": "2023-06-20T19:53:37.287+00:00",
    "createdBy": "ssonsite@8451.com",
    "modifiedAt": None,
    "modifiedBy": None,
    "shortName": "PLA",
    "inFlightDisabled": [
        "placementType",
        "budgetType",
        "startDate"
    ],
    "fieldDisabled": [
        "budgetType"
    ],
    "fields": [
        {
            "id": "name",
            "type": "string",
            "displayName": "Ad Group Name",
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Enter ad group name",
                    "value": True
                },
                {
                    "type": "regex",
                    "message": "Enter a name that includes letters, numbers, spaces, or the following characters: .,&( )_-+=|:;\"",
                    "value": "^[A-Za-z0-9\\.\\s&\\(\\)_\\-\\+=\\|:;,]+$"
                },
                {
                    "type": "regex",
                    "message": "Enter a name that is fewer than 255 characters",
                    "value": "^.{0,255}$"
                }
            ]
        },
        {
            "id": "budgetType",
            "type": "singleselect",
            "displayName": "Budget Type",
            "description": None,
            "options": [
                {
                    "value": "Daily",
                    "description": None,
                    "disable": False,
                    "dependentFields": None
                },
                {
                    "value": "Weekly",
                    "description": None,
                    "disable": False,
                    "dependentFields": None
                },
                {
                    "value": "Monthly",
                    "description": None,
                    "disable": False,
                    "dependentFields": None
                },
                {
                    "value": "Custom",
                    "description": None,
                    "disable": False,
                    "dependentFields": None
                }
            ],
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Select ad group budget type",
                    "value": True
                },
                {
                    "type": "enum",
                    "message": "Budget Type must be 'Daily', 'Weekly', 'Monthly', or 'Custom'",
                    "value": [
                        "Daily",
                        "Weekly",
                        "Monthly",
                        "Custom"
                    ]
                },
                {
                    "targetRequired": True,
                    "type": "conditional_dynamic",
                    "message": "Activation Budget Type must match the campaign Budget Type.",
                    "value": "EQUAL_TO",
                    "target": "campaignBudgetType"
                },
                {
                    "type": "value_requires",
                    "message": "If custom is used, an endDate must be provided.",
                    "value": "Custom",
                    "target": "endDate"
                }
            ]
        },
        {
            "id": "budgetAmount",
            "type": "currency",
            "displayName": "Budget Amount",
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Enter ad group budget",
                    "value": True
                },
                {
                    "type": "regex",
                    "message": "Enter a numeric ad group budget",
                    "value": "\\d{0,1000}(\\.\\d{1,2})?"
                },
                {
                    "targetRequired": True,
                    "type": "conditional_dynamic",
                    "message": "Enter an ad group budget that is less than or equal to the remaining campaign budget",
                    "value": "LESSER_THAN_OR_EQUAL_TO",
                    "target": "remainingBudgetAmount"
                }
            ]
        },
        {
            "id": "startDate",
            "type": "date",
            "displayName": "Start Date",
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Select or enter start date",
                    "value": True
                },
                {
                    "type": "regex",
                    "message": "Select or enter a start date that is in MM/DD/YYYY format",
                    "value": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                },
                {
                    "targetRequired": True,
                    "type": "conditional_dynamic",
                    "message": "Select or enter a start date that is after or the same as the campaign start date",
                    "value": "GREATER_THAN_OR_EQUAL_TO",
                    "target": "minStartDate"
                }
            ]
        },
        {
            "id": "endDate",
            "type": "date",
            "displayName": "End Date",
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Select or enter end date",
                    "value": False
                },
                {
                    "type": "regex",
                    "message": "Select or enter an end date that is in MM/DD/YYYY format",
                    "value": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                },
                {
                    "targetRequired": True,
                    "type": "conditional_native",
                    "message": "Select or enter an end date that is equal to or past the selected start date",
                    "value": "GREATER_THAN_OR_EQUAL_TO",
                    "target": "startDate"
                },
                {
                    "targetRequired": False,
                    "type": "conditional_dynamic",
                    "message": "Select or enter an end date that is before or the same as the campaign end date",
                    "value": "LESSER_THAN_OR_EQUAL_TO",
                    "target": "maxEndDate"
                }
            ],
            "overrides": [
                {
                    "conditions": [
                        {
                            "fieldName": "alwaysOn",
                            "value": True
                        }
                    ],
                    "value": None
                }
            ]
        },
        {
            "id": "alwaysOn",
            "type": "boolean",
            "displayName": "Always On",
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Always On is required",
                    "value": True
                }
            ]
        },
        {
            "id": "biddableEntities",
            "type": "arrayEntity",
            "entity": "biddableEntity",
            "displayName": None,
            "description": None,
            "options": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Select biddable entities",
                    "value": True
                }
            ]
        },
        {
            "id": "divisionBanners",
            "type": "arrayEntity",
            "entity": "divisionBanner",
            "displayName": None,
            "description": None,
            "options": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Select division banners",
                    "value": True
                }
            ]
        },
        {
            "id": "creativeTag",
            "type": "string",
            "displayName": "Creative Tag",
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "",
                    "value": False
                }
            ]
        },
        {
            "id": "placementType",
            "type": "multiselect",
            "displayName": "Placement Type(s)",
            "description": None,
            "options": [
                {
                    "value": "Search & Browse",
                    "description": None,
                    "disable": False,
                    "dependentFields": None
                },
                {
                    "value": "Basket Builder",
                    "description": None,
                    "disable": False,
                    "dependentFields": None
                },
                {
                    "value": "Savings",
                    "description": None,
                    "disable": False,
                    "dependentFields": None
                }
            ],
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Select placement type",
                    "value": True
                },
                {
                    "type": "enum",
                    "message": "Field must contain [Search & Browse, Basket Builder, Savings]",
                    "value": [
                        "Search & Browse",
                        "Basket Builder",
                        "Savings"
                    ]
                }
            ],
            "overrides": None
        },
        {
            "id": "dayPartingStart",
            "type": "integer",
            "displayName": None,
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Day parting start is optional",
                    "value": False
                },
                {
                    "type": "regex",
                    "message": "Day parting start must be a positive integer",
                    "value": "^[0-9]+$"
                }
            ]
        },
        {
            "id": "dayPartingEnd",
            "type": "integer",
            "displayName": None,
            "description": None,
            "defaultValue": None,
            "validationRules": [
                {
                    "type": "required",
                    "message": "Day parting end is optional",
                    "value": False
                },
                {
                    "type": "regex",
                    "message": "Day parting end must be a positive integer",
                    "value": "^[0-9]+$"
                }
            ]
        }
    ],
    "entities": [
        {
            "name": "promotedProduct",
            "fields": [
                {
                    "name": "upc",
                    "type": "string",
                    "defaultValue": None,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "upc is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "UPC must be 12 digits",
                            "value": "^\\d{12}$"
                        }
                    ]
                }
            ]
        },
        {
            "name": "divisionBanner",
            "fields": [
                {
                    "name": "Division Number",
                    "type": "string",
                    "defaultValue": None,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "Division Number is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "Division Number must be 3 digits",
                            "value": "^\\d{3}$"
                        }
                    ]
                },
                {
                    "name": "Banner Code",
                    "type": "string",
                    "defaultValue": None,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "Banner Code is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "Banner Code must be alphanumeric",
                            "value": "^[A-Za-z0-9]+$"
                        }
                    ]
                }
            ]
        },
        {
            "name": "targetSubcommodity",
            "fields": [
                {
                    "name": "code",
                    "type": "string",
                    "defaultValue": None,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "code is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "Code must be in format of <2 digits>_<3 digits>_<5_digits>",
                            "value": "^\\d{2}_\\d{3}_\\d{5}$"
                        }
                    ]
                },
                {
                    "name": "name",
                    "type": "string",
                    "defaultValue": None,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "name is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "Name must be alphanumeric",
                            "value": "^[A-Za-z0-9]+$"
                        }
                    ]
                }
            ]
        },
        {
            "name": "biddableEntity",
            "fields": [
                {
                    "name": "upc",
                    "type": "string",
                    "defaultValue": None,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "upc is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "UPC must be 12 digits",
                            "value": "^\\d{12}$"
                        }
                    ]
                },
                {
                    "name": "name",
                    "type": "string",
                    "defaultValue": None,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "name is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "Name must be alphanumeric",
                            "value": "^[A-Za-z0-9]+$"
                        }
                    ]
                },
                {
                    "name": "useBaseBid",
                    "type": "boolean",
                    "defaultValue": True,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "useBaseBid is required",
                            "value": True
                        }
                    ]
                },
                {
                    "name": "amount",
                    "type": "currency",
                    "defaultValue": 0,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "amount is required",
                            "value": True
                        },
                        {
                            "type": "regex",
                            "message": "Amount must be a numeric value",
                            "value": "\\d{0,1000}(\\.\\d{1,2})?"
                        }
                    ]
                },
                {
                    "name": "deleted",
                    "type": "boolean",
                    "defaultValue": False,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "deleted is required",
                            "value": True
                        }
                    ]
                }
            ]
        }
    ],
    "compatibleChannels": [
        "PLA-1"
    ],
    "deliveryPartner": "koddi",
    "internals": []
}

SIMPLE_ACTIVATION_JSON = {
    "data": {
        "id": "67e571f9b86dba22f2507593",
        "channel_config": {"type": "PLA", "version": "1"},
        "campaign_id": "67e571b718da06d6c8f123f6",
        "status": "Active",
        "metadata": {
            "created_at": "2025-03-27T15:42:49.490000",
            "created_by": "S-1-324640241-946581667-4084971071-1246649997-2318539443-2696700096",
            "created_by_user_id": "S-1-324640241-946581667-4084971071-1246649997-2318539443-2696700096",
            "created_by_user_name": "Venkata Anne",
            "created_by_user_email": "v662058@8451.com",
            "created_by_client_id": "0oa9a0gc86MTUb52M697",
            "last_modified": "2025-03-27T15:46:13.498000",
            "last_modified_by_user_id": "S-1-324640241-946581667-4084971071-1246649997-2318539443-2696700096",
            "last_modified_by_user_name": "Venkata Anne",
            "last_modified_by_user_email": "v662058@8451.com",
            "last_modified_by_client_id": "0oa9a0gc86MTUb52M697",
            "last_publish_result": "SUCCESS",
            "last_published": "2025-03-27T15:46:13.302000",
            "last_published_by_user_id": "S-1-324640241-946581667-4084971071-1246649997-2318539443-2696700096",
            "last_published_by_user_name": "Venkata Anne",
            "last_published_by_user_email": "v662058@8451.com",
            "last_published_by_client_id": "0oa9a0gc86MTUb52M697",
            "last_published_fields": [],
            "last_publish_system_errors": [],
            "last_publish_field_errors": [],
            "deleted": False,
            "approved": True,
            "externalIDs": {"KODDI": "1336716"},
            "short_id": "161031",
            "is_locked": False,
            "potential_status": None,
            "is_archived": False,
            "discarded": False,
        },
        "channel_data": {
            "name": "VA-AG-UI-167292-1",
            "budgetType": "Monthly",
            "placementType": ["Search & Browse", "Basket Builder", "Savings"],
            "startDate": "2025-03-27",
            "endDate": "2025-12-31",
            "alwaysOn": False,
            "biddableEntities": ["5feedde8-3186-4527-b6fe-659edee00872"],
            "budgetAmount": 100,
            "divisionBanners": ["2c00bdca-2462-46db-8fa3-9937745cc642"],
            "keywordBidModifierGroup": None,
        },
        "published_data": {
            "name": "VA-AG-UI-167292-1",
            "budgetType": "Monthly",
            "placementType": ["Search & Browse", "Basket Builder", "Savings"],
            "startDate": "2025-03-27",
            "endDate": "2025-12-31",
            "alwaysOn": False,
            "biddableEntities": ["5feedde8-3186-4527-b6fe-659edee00872"],
            "budgetAmount": 100,
            "divisionBanners": ["2c00bdca-2462-46db-8fa3-9937745cc642"],
            "keywordBidModifierGroup": None,
        },
        "unpublished_data": {},
    },
    "errors": [],
    "warnings": [],
    "meta": None,
    "included": {
        "configuration": [
            {
                "id": "67e571f9b86dba22f2507593",
                "editability_by_field": {
                    "name": True,
                    "alwaysOn": True,
                    "startDate": False,
                    "endDate": True,
                    "budgetAmount": True,
                    "budgetType": False,
                    "divisionBanners": True,
                    "dayPartingStart": True,
                    "dayPartingEnd": True,
                    "placementType": False,
                    "keywordBidModifierGroup": True,
                    "biddableEntities": True,
                },
            }
        ],
        "configuration_by_activation": {
            "67e571f9b86dba22f2507593": {
                "name": {"is_editable": True},
                "alwaysOn": {"is_editable": True},
                "startDate": {"is_editable": False},
                "endDate": {"is_editable": True},
                "budgetAmount": {"is_editable": True},
                "budgetType": {"is_editable": False},
                "divisionBanners": {"is_editable": True},
                "dayPartingStart": {"is_editable": True},
                "dayPartingEnd": {"is_editable": True},
                "placementType": {"is_editable": False},
                "keywordBidModifierGroup": {"is_editable": True},
                "biddableEntities": {
                    "is_editable": True,
                    "min_bid_amount": 0.6,
                    "max_bid_amount": 50.0,
                },
            }
        },
    },
}

UPDATED_ACTIVATION_RESPONSE_JSON = {
    "data": {
        "id": "66856b3cca58d4533268b7dd",
        "channel_config": {"type": "PLA", "version": "1"},
        "campaign_id": "66856b2106f1aee40806b3d7",
        "status": "Active",
        "metadata": {
            "created_at": "2024-07-03T15:16:12.406000",
            "created_by": "a63a0879-0dac-41c6-bb1d-7e2df7064e83",
            "last_modified": "2024-07-03T16:59:27.747000",
            "deleted": False,
            "approved": True,
            "externalIDs": {},
            "short_id": "11782",
            "is_locked": False,
            "last_publish_result": None,
            "last_published": None,
            "last_published_fields": [],
            "last_publish_system_errors": [],
            "last_publish_field_errors": [],
            "potential_status": None,
        },
        "channel_data": {
            "name": "Test Ad Group",
            "startDate": "2024-05-20",
            "endDate": "2024-06-20",
            "alwaysOn": False,
            "budgetType": "Monthly",
            "budgetAmount": 250,
            "biddableEntities": ["8e7b3a06-1d64-4cd8-b23d-c4c1580b0bce"],
            "divisionBanners": ["d481f4be-eb5e-4b15-b2c8-ec0f12f27f95"],
            "placementType": ["Search & Browse"],
        },
        "published_data": {},
        "unpublished_data": {
            "name": "asdfasdf23123",
            "startDate": "2024-07-04",
            "endDate": "2024-10-25",
            "alwaysOn": False,
            "budgetType": "Monthly",
            "budgetAmount": 20,
            "biddableEntities": ["8e7b3a06-1d64-4cd8-b23d-c4c1580b0bce"],
            "divisionBanners": ["d481f4be-eb5e-4b15-b2c8-ec0f12f27f95"],
            "placementType": ["Search & Browse"],
        },
    },
    "errors": [],
    "warnings": [],
    "meta": None,
    "included": {
        "configuration": [
            {
                "id": "67e571f9b86dba22f2507593",
                "editability_by_field": {
                    "name": True,
                    "alwaysOn": True,
                    "startDate": False,
                    "endDate": True,
                    "budgetAmount": True,
                    "budgetType": False,
                    "divisionBanners": True,
                    "dayPartingStart": True,
                    "dayPartingEnd": True,
                    "placementType": False,
                    "keywordBidModifierGroup": True,
                    "biddableEntities": True,
                },
            }
        ],
        "configuration_by_activation": {
            "67e571f9b86dba22f2507593": {
                "name": {"is_editable": True},
                "alwaysOn": {"is_editable": True},
                "startDate": {"is_editable": False},
                "endDate": {"is_editable": True},
                "budgetAmount": {"is_editable": True},
                "budgetType": {"is_editable": False},
                "divisionBanners": {"is_editable": True},
                "dayPartingStart": {"is_editable": True},
                "dayPartingEnd": {"is_editable": True},
                "placementType": {"is_editable": False},
                "keywordBidModifierGroup": {"is_editable": True},
                "biddableEntities": {
                    "is_editable": True,
                    "min_bid_amount": 0.6,
                    "max_bid_amount": 50.0,
                },
            }
        },
    },
}

CAROUSEL_ACTIVATION_RESPONSE_JSON = {
    "data": {
        "id": "66856b3cca58d4533268b7dd",
        "channel_config": {"type": "Promoted_Products_Carousel", "version": "1"},
        "campaign_id": "66856b2106f1aee40806b3d7",
        "status": "Active",
        "metadata": {
            "created_at": "2024-07-03T15:16:12.406000",
            "created_by": "a63a0879-0dac-41c6-bb1d-7e2df7064e83",
            "last_modified": "2024-07-03T16:59:27.747000",
            "deleted": False,
            "approved": True,
            "externalIDs": {},
            "short_id": "11782",
            "is_locked": False,
            "last_publish_result": None,
            "last_published": None,
            "last_published_fields": [],
            "last_publish_system_errors": [],
            "last_publish_field_errors": [],
            "potential_status": None,
        },
        "channel_data": {
            "name": "Test Ad Group",
            "startDate": "2024-05-20",
            "endDate": "2024-06-20",
            "alwaysOn": False,
            "budgetType": "Monthly",
            "budgetAmount": 250,
            "biddableEntities": ["8e7b3a06-1d64-4cd8-b23d-c4c1580b0bce"],
            "divisionBanners": ["d481f4be-eb5e-4b15-b2c8-ec0f12f27f95"],
            "placementType": ["Search & Browse PPC"],
        },
        "published_data": {},
        "unpublished_data": {
            "name": "asdfasdf23123",
            "startDate": "2024-07-04",
            "endDate": "2024-10-25",
            "alwaysOn": False,
            "budgetType": "Monthly",
            "budgetAmount": 20,
            "biddableEntities": ["8e7b3a06-1d64-4cd8-b23d-c4c1580b0bce"],
            "divisionBanners": ["d481f4be-eb5e-4b15-b2c8-ec0f12f27f95"],
            "placementType": ["Search & Browse"],
        },
    },
    "errors": [],
    "warnings": [],
    "meta": None,
    "included": {
        "configuration": [
            {
                "id": "67e571f9b86dba22f2507593",
                "editability_by_field": {
                    "name": True,
                    "alwaysOn": True,
                    "startDate": False,
                    "endDate": True,
                    "budgetAmount": True,
                    "budgetType": False,
                    "divisionBanners": True,
                    "dayPartingStart": True,
                    "dayPartingEnd": True,
                    "placementType": False,
                    "keywordBidModifierGroup": True,
                    "biddableEntities": True,
                },
            }
        ],
        "configuration_by_activation": {
            "67e571f9b86dba22f2507593": {
                "name": {"is_editable": True},
                "alwaysOn": {"is_editable": True},
                "startDate": {"is_editable": False},
                "endDate": {"is_editable": True},
                "budgetAmount": {"is_editable": True},
                "budgetType": {"is_editable": False},
                "divisionBanners": {"is_editable": True},
                "dayPartingStart": {"is_editable": True},
                "dayPartingEnd": {"is_editable": True},
                "placementType": {"is_editable": False},
                "keywordBidModifierGroup": {"is_editable": True},
                "biddableEntities": {
                    "is_editable": True,
                    "min_bid_amount": 0.6,
                    "max_bid_amount": 50.0,
                },
            }
        },
    },
}

DEFAULT_CONTACTS_RESPONSE_JSON = {
    "data": [
        {
            "contactId": "0054V00000E8ondQAB",
            "firstName": "Jeff",
            "lastName": "Mayrose",
            "emailAddress": "jeffrey.mayrose@8451.com.invalid",
            "worksFor": {
                "displayName": None,
                "clientId": "0013000000c438LAAQ",
                "type": None
            },
            "address": {
                "addressLines": [
                    ""
                ],
                "cityTown": "",
                "stateProvince": "",
                "postalCode": "",
                "countryCode": ""
            },
            "role": "LMC Account Owner",
            "roleType": {
                "type": "PRIMARY_LOYALTY_MARKETING_CONSULTANT",
                "displayName": "Primary Loyalty Marketing Consultant",
                "groupTypes": [
                    "MARKETING_CONSULTANT"
                ]
            },
            "networkIdentifier": "j204570@8451.com"
        },
        {
            "contactId": "0053A00000DejINQAZ",
            "firstName": "Suzanne",
            "lastName": "Brawley",
            "emailAddress": "suzie.brawley@8451.com.invalid",
            "worksFor": {
                "displayName": None,
                "clientId": "0013000000c438LAAQ",
                "type": None
            },
            "address": {
                "addressLines": [
                    ""
                ],
                "cityTown": "",
                "stateProvince": "",
                "postalCode": "",
                "countryCode": ""
            },
            "role": "Primary Account Manager",
            "roleType": {
                "type": "PRIMARY_ACCOUNT_MANAGER",
                "displayName": "Primary Account Manager",
                "groupTypes": [
                    "ACCOUNT_MANAGER"
                ]
            },
            "networkIdentifier": "s250409@8451.com"
        },
        {
            "contactId": "0054V00000HRztWQAT",
            "firstName": "Sara",
            "lastName": "Putman",
            "emailAddress": "sara.putman@8451.com.invalid",
            "worksFor": {
                "displayName": None,
                "clientId": "0013000000c438LAAQ",
                "type": None
            },
            "address": {
                "addressLines": [
                    ""
                ],
                "cityTown": "",
                "stateProvince": "",
                "postalCode": "",
                "countryCode": ""
            },
            "role": "Account Executive",
            "roleType": {
                "type": "ACCOUNT_EXECUTIVE",
                "displayName": "Account Executive",
                "groupTypes": [
                    "ACCOUNT_EXECUTIVE"
                ]
            },
            "networkIdentifier": "s551231@8451.com"
        },
        {
            "contactId": "0054V00000GBaUwQAL",
            "firstName": "William",
            "lastName": "Brabender",
            "emailAddress": "will.brabender@8451.com.invalid",
            "worksFor": {
                "displayName": None,
                "clientId": "0013000000c438LAAQ",
                "type": None
            },
            "address": {
                "addressLines": [
                    ""
                ],
                "cityTown": "",
                "stateProvince": "",
                "postalCode": "",
                "countryCode": ""
            },
            "role": "Primary Media Account Manager",
            "roleType": {
                "type": "PRIMARY_MEDIA_ACCOUNT_MANAGER",
                "displayName": "Primary Media Account Manager",
                "groupTypes": [
                    "ACCOUNT_MANAGER"
                ]
            },
            "networkIdentifier": "w264517@8451.com"
        }
    ],
    "meta": {
        "page": {
            "totalCount": 4,
            "offset": 0,
            "size": 4
        },
        "auth": {
            "displayName": "Robert Fuller",
            "internalUser": True,
            "personId": "2b3b7fa4-f0de-4498-99aa-1718f1128c4a",
            "worksFor": {
                "displayName": "84.51°",
                "clientId": "5e1f20b4-29a2-4d2c-8ede-eeb369c83585",
                "type": "INTERNAL"
            }
        },
        "allAccountsAccess": True,
        "internalUser": True
    }
}

FETCH_ADDRESSES_RESPONSE_JSON = {
    'data': {'clientId': 'ad88e6f7-0ae4-4e77-9087-167e5f31b3db', 'displayName': 'Coca Cola Co',
             'salesforceId': '0013000000c2m78AAA', 'companyType': 'CPG', 'segment': 'Grocery', 'poRequiredBcc': True,
             'poRequiredKpm': True, 'pricingType': 'CPG', 'emergingClientTeam': False, 'manufacturerCode': '4',
             'manufacturerName': 'Coca-Cola', 'clientBccPricing': 'Stratum',
             'addresses': [

                 {'id': 'a064V00000XnGsdQAF', 'addressLines': ['1 Coca Cola Plz NW'], 'cityTown': 'Atlanta',
                  'stateProvince': 'GA', 'postalCode': '30313-2420', 'countryCode': 'US', 'status': 'Verified',
                  'addressType': 'CORPORATE', 'duplicate': False}],
             'nonBillableClient': True, 'nonBillable': True,
             'territoryModel': [['BCC', 'Core', 'Core 1', 'Core6'], ['KPM', 'Central', 'Central 1', 'Central 1N'],
                                ['CIL', 'Platinum', 'Platinum 2', 'Platinum 2B']],
             'knumbers': [{'name': 'K0341072', 'description': 'K0341072', 'primary': True}]}, 'meta': {
        'auth': {'displayName': 'Agency2 UM', 'internalUser': False, 'personId': '8995975e-c5cf-4eba-8634-254392c550de',
                 'worksFor': {'displayName': 'Universal McCann New York',
                              'clientId': '4ee3f974-c4af-49bf-b0f6-702360157330', 'type': 'BROKER_OR_AGENCY'}},
        'allAccountsAccess': False, 'internalUser': False}}

SIMPLE_REPORT_REQUEST = ReportRequestV1(
    dimensions=[DimensionsV1.CAMPAIGN_ID, DimensionsV1.HOUR],
    metrics=['clicks', MetricsV1.WIN_RATE, MetricsV1.HOURS_LIVE],
    filters=[],
    sort=[SortFieldV1(field='clicks', order='DESC')],
    startDate='2024-01-01',
    endDate='2025-03-30',
    pagination=Pagination(offset=0, size=100),
    advertiserIds=[3]
)

SIMPLE_REPORT_REQUEST_V2 = ReportRequestV2(
    dimensions=[DimensionsV2.CAMPAIGN_ID, DimensionsV2.HOUR],
    metrics=[
        MetricsV2.CLICKS,
        MetricsV2.WIN_RATE,
        MetricsV2.HOURS_LIVE,
        MetricsV2.UNIQUE_USER_CONVERSIONS,
        MetricsV2.UNIQUE_USER_IMPRESSIONS,
        MetricsV2.VIEWED_CVR,
        MetricsV2.VIEWED_AVG_UNIT_PRICE,
    ],
    filters=[],
    sort=[SortFieldV2(field=MetricsV2.CLICKS, order=SortOrderCommon.DESC)],
    startDate="2024-01-01",
    endDate="2025-03-30",
    pagination=Pagination(offset=0, size=100),
    advertiserIds=[3],
)

REPORT_RESPONSE_JSON = {
    "result": {
        "data": [
            {
                "campaign_id": 1234567,
                "clicks": 0,
                "hour": 3,
                "hours_live": 0.96258851,
                "win_rate": 0.00046119,
            }
        ],
        "headers": [
            {"name": "campaign_id", "title": "Campaign ID (INTERNAL)", "type": "number"},
            {"name": "clicks", "title": "Clicks", "type": "number"},
            {"name": "win_rate", "type": "percentage", "title": "Win Rate %"},
            {"name": "hours_live", "type": "percentage", "title": "Time Live"},
            {"name": "hour", "type": "decimal", "title": "Hour"},
        ],
        "total_count": 1,
    },
    "status": "success",
}

META_SUCCESS = EntityMeta(
    success=True,
    publishStatus=PublishStatus.PUBLISHED,
    warnings=Warnings(validation=[])
)
META_WARNINGS = EntityMeta(
    success=True,
    publishStatus=PublishStatus.PENDING,
    warnings=Warnings(
        validation=[UpstreamValidationWarning(detail=["budget","amount max than ad groups"],
                                              path="/update campaing")]
    ),
    errors=[]
)
META_ERRORS = EntityMeta(
    success=True,
    publishStatus=PublishStatus.EMPTY,
    warnings=Warnings(validation=[]),
    errors=[{"msg":"error budget field", "type": "max amount"},{"msg":"error status field", "type": "status unknown"}]
)

PRODUCT_MANAGER_PRODUCT = {
    "upc": "0001200017023",
    "description": "Amp Energy Organic Pineapple & Coconut Drink",
    "isValid": True,
    "brand": "Amp Energy",
    "quantity": "",
    "taxonomy": {
        "department": {
            "id": "4",
            "name": "Beverages"
        },
        "commodity": {
            "id": "4011",
            "name": "Energy Drinks"
        },
        "subCommodity": {
            "id": "401100001",
            "name": "Caffeinated Energy Drinks"
        }
    },
    "restrictions": {
        "prohibited": False,
        "sensitive": False,
        "notRestricted": False,
        "notFound": False,
    },
    "lastSoldDate": "2025-05-15"
}
