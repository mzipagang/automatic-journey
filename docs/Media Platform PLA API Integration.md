# Kroger Media Platform API Specifications

> Jun 18, 2024 - Version 1.0

# Table of Contents

<!-- TOC tocDepth:2..4 chapterDepth:2..6 -->

- [Kroger Media Platform API Specifications](#kroger-media-platform-api-specifications)
- [Table of Contents](#table-of-contents)
  - [1. Product Listing Ads (PLAs)](#1-product-listing-ads-plas)
  - [2. Summary](#2-summary)
  - [3. Campaign Documentation](#3-campaign-documentation)
    - [3.1. Timezone and Currency](#31-timezone-and-currency)
    - [3.2. Budgets](#32-budgets)
    - [3.3. Placements](#33-placements)
  - [4. API Conventions](#4-api-conventions)
    - [4.1. General](#41-general)
    - [4.2. Environments](#42-environments)
    - [4.3. Headers](#43-headers)
    - [4.4. Rate Limits](#44-rate-limits)
  - [5. Access and Authorization](#5-access-and-authorization)
    - [5.1. Authentication](#51-authentication)
    - [5.2. Authorization](#52-authorization)
    - [5.3. Authentication Parameters](#53-authentication-parameters)
  - [6. Error Handling](#6-error-handling)
  - [7. API Endpoint Documentation](#7-api-endpoint-documentation)
    - [7.1. Metadata APIs](#71-metadata-apis)
      - [7.1.1. Accounts](#711-accounts)
      - [7.1.2. Advertisers](#712-advertisers)
      - [7.1.3. Contacts](#713-contacts)
      - [7.1.4. Addresses](#714-addresses)
      - [7.1.5. Targets](#715-targets)
      - [7.1.6. Target - Placements](#716-target---placements)
      - [7.1.7. Target - Divisions](#717-target---divisions)
      - [7.1.8. Products](#718-products)
    - [7.2. Campaign Management APIs](#72-campaign-management-apis)
      - [7.2.1. V1 Campaign Management APIs](#721-v1-campaign-management-apis)
        - [7.2.1.1. Create Campaign](#7211-create-campaign)
        - [7.2.1.2. Get Campaigns by Advertiser Id](#7212-get-campaigns-by-advertiser-id)
        - [7.2.1.3. Get Campaign By Id](#7213-get-campaign-by-id)
        - [7.2.1.4. Update Campaign](#7214-update-campaign)
        - [7.2.1.5. Create Ad Group](#7215-create-ad-group)
        - [7.2.1.6. Get Ad Groups by Campaign Id](#7216-get-ad-groups-by-campaign-id)
        - [7.2.1.7. Get Ad Group By Id](#7217-get-ad-group-by-id)
        - [7.2.1.8. Update Ad Group](#7218-update-ad-group)
        - [7.2.1.9. Update Ad Group Entities](#7219-update-ad-group-entities)
        - [7.2.1.10. Get Eligible Keywords by Ad Group Id](#72110-get-eligible-keywords-by-ad-group-id)
        - [7.2.1.11. Update Ad Group Keyword Bid Modifiers](#72111-update-ad-group-keyword-bid-modifiers)
        - [7.2.1.12. System Constants](#72112-system-constants)
    - [7.3. Reporting APIs](#73-reporting-apis)
      - [7.3.1. Report](#731-report)

<!-- /TOC -->

## 1. Product Listing Ads (PLAs)

## 2. Summary

The Media Platform API integration allows Kroger Partners to activate Product Listing Ads (PLAs) media.

## 3. Campaign Documentation

### 3.1. Timezone and Currency

The Kroger Media Platform uses **US Dollar (USD)** as the primary and only currency and all times are **Eastern Timezone** (EST and EDT depending on the date).

### 3.2. Budgets

Budgets are set both at the campaign and ad group level.

- A Weekly Budget will reset every Monday, and the budget will cover Monday through Sunday.
- A Monthly Budget will reset every 1st day of the month, and the Monthly Budget will cover the entire month.
- If the campaign start-date or end-date does not fall on the first or last day of the week/month, the budget for that period will be prorated.
- An individual ad group budget must be less than the campaign budget.
- The sum of the ad group budgets may exceed the campaign budget. The campaign will stop as soon as the campaign budget is met even when there will be remaining ad group budget.

### 3.3. Placements

Ad Groups support multiple placement targets.

- Placements are what drives the price floor for the ad group.
- If more than one placement is selected in a single ad group, the highest price floor becomes the minimum bid for the promoted products.

## 4. API Conventions

### 4.1. General

The API is a fully functional Restful API using JSON formatting. Include the following with each request:

- Media type *application/json* for all calls.
- GET calls have empty bodies, using query parameters.
- POST/PUT/PATCH calls use JSON bodies.
- No support for DELETE calls.

### 4.2. Environments

There are two available environments for partners to integrate with the Media Platform

1. Production.
2. Non-production (sandbox).

### 4.3. Headers

All API requests must include the following headers

| Key           | Value                 |
|---------------|-----------------------|
| Authorization | Bearer {ACCESS_TOKEN} |
| Content-Type  | application/json      |

### 4.4. Rate Limits

- Rate limits are applied at the "application" level.
- Breaching rate limits should result in HTTP error 429.

| Advertisers | Request Limit           |
|-------------|-------------------------|
| < 50        | 50 requests per second  |
| 50-200      | 75 requests per second  |
| > 200       | 100 requests per second |

## 5. Access and Authorization

### 5.1. Authentication

- 84.51 provides has a single “application” (client ID and secret) for each environment for the partner to use
- A standard OAuth2 flow allows the partner to redirect users, once upon setup, to a URL which will allow them to log in to their account with 84.51, and then be redirected back to the partner.
- Access tokens have a validity of **60 minutes**.
- The result of that process is refresh token with validity of a maximum of **180 days** which partners can safely persist and associate with a specific advertiser account to generate new access tokens.
- A refresh token must be used within a **45 day** window to continue to extend it's validity up to the maximum.
- A refresh token will be exchanged for a short-lived access token usable for API calls. Each request must include a header with the token in the format of `Authorization: Bearer ACCESS_TOKEN_VALUE`

### 5.2. Authorization

- Users are assigned to accounts in the system. An account encompasses one or more advertisers.
- Each advertiser (also known as brand) has a list of products associated.
- Each campaign must have both the account id and the advertiser id.
- Users have a default role of "Advertiser" which allows them to access all APIs listed below.

### 5.3. Authentication Parameters

| Type             | Value                                                           |
|------------------|-----------------------------------------------------------------|
| Type             | OAuth 2.0                                                       |
| Grant Type       | Authorization Code                                              |
| Auth URL         | https://login.8451.com/oauth2/aus2rfaog9lmi37qz697/v1/authorize |
| Access Token URL | https://login.8451.com/oauth2/aus2rfaog9lmi37qz697/v1/token     |
| Client Id        | <Unique to your onboarding>                                     |
| Client Secret    | <Unique to your onboarding>                                     |
| Scope            | offline_access openid email e451.api.access                     |

## 6. Error Handling

The Kroger Media Platform will return appropriate error codes corresponding to the HTTP standard.

| Code | Description           | Message                                                                               |
|------|-----------------------|---------------------------------------------------------------------------------------|
| 200  | OK                    | The request has succeeded.                                                            |
| 201  | Created               | The entity was processed correctly. This applies to creating campaigns and ad groups. |
| 400  | Bad Request           | See payload for error description.                                                    |
| 401  | Unauthorized          | The client must have a valid access token to get the requested response.              |
| 403  | Forbidden             | The client is recognized but the requested entity is not available for the user.      |
| 404  | Not Found             | The request entity has not been found.                                                |
| 422  | Unprocessable Entity  | The expected payload was not sent.                                                    |
| 500  | Internal Server Error | See payload for error description.                                                    |


## 7. API Endpoint Documentation

 The API specifications are broken down into three sections:

1. **Metadata APIs.** A list of catalogs that retrieve the data necessary to create a campaign.
2. **Campaign Management APIs.** Create campaigns, ad groups, and updates them as necessary.
3. **Reporting APIs.** Endpoints to retrieve campaign reports.

### 7.1. Metadata APIs

#### 7.1.1. Accounts

`GET /media/pla/v1/metadata/accounts`

Notes:
- Whenever there is an update to [7.1.3. Contacts](https://github.com/8451LLC/map-onsite-apis/blob/main/docs/Media%20Platform%20PLA%20API%20Integration.md#713-contacts) or [7.1.4. Addresses](https://github.com/8451LLC/map-onsite-apis/blob/main/docs/Media%20Platform%20PLA%20API%20Integration.md#714-addresses), users are required to make a GET /accounts call. This will cache the updated contacts and addresses.

Parameters:

| Parameter | Description                                                                      | Required | Sample |
|-----------|----------------------------------------------------------------------------------|----------|--------|
| OFFSET    | The offset of the first account to return sent as an integer. Defaults to O.     | False    | 0      |
| SIZE      | The number of account to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 100,
      "name": "Account 100 Co",
      "active": true
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

#### 7.1.2. Advertisers

`GET /media/pla/v1/metadata/advertisers?accountId={{ACCOUNT_ID}}`

Parameters:

| Parameter  | Description                                                                          | Required | Sample |
|------------|--------------------------------------------------------------------------------------|----------|--------|
| ACCOUNT_ID | Id that identifies the account ID. Integer.                                          | True     | 100    |
| OFFSET     | The offset of the first advertiser to return sent as an integer. Defaults to O.      | False    | 0      |
| SIZE       | The number of advertisers to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 8,
      "name": "Advertiser 1",
      "accountId": 100,
      "description": "Account Name - Advertiser 1",
      "active": true
    },
    {
      "id": 26,
      "name": "Advertiser 2",
      "accountId": 100,
      "description": "Account Name - Advertiser 2",
      "active": true
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

#### 7.1.3. Contacts

`GET /media/pla/v1/metadata/contacts?accountId={{ACCOUNT_ID}}`

Notes:
- For Agency users this API will return the CPG contacts and the Agency contacts.
- When creating campaigns, if an Agency contact is provided as the billing contact the campaign will be billed against the agency.
- The field `contactType` is an enum with values: `CPG` and `AGENCY`
- Whenever there is an update to contacts, users are required to make a [GET /accounts](https://github.com/8451LLC/map-onsite-apis/blob/main/docs/Media%20Platform%20PLA%20API%20Integration.md#711-accounts) call. This will cache the updated contacts.

Parameters:

| Parameter  | Description                                                                       | Required | Sample |
|------------|-----------------------------------------------------------------------------------|----------|--------|
| ACCOUNT_ID | Id that identifies the account ID. Integer.                                       | True     | 100    |
| OFFSET     | The offset of the first contact to return sent as an integer. Defaults to O.      | False    | 0      |
| SIZE       | The number of contacts to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 101,
      "firstName": "Jane",
      "lastName": "Doe",
      "email": "jane.doe@account.com",
      "contactType": "CPG",
      "active": true
    },
    {
      "id": 102,
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@account.com",
      "contactType": "AGENCY",
      "active": true
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

#### 7.1.4. Addresses

`GET /media/pla/v1/metadata/addresses?accountId={{ACCOUNT_ID}}`

Notes:
- For Agency users this API will return the CPG addresses and the Agency addresses.
- When creating campaigns, if an Agency address is provided as the billing address the campaign will be billed against the agency.
- The field `addressType` is an enum with values: `CPG` and `AGENCY`
- Whenever there is an update to addresses, users are required to make a [GET /accounts](https://github.com/8451LLC/map-onsite-apis/blob/main/docs/Media%20Platform%20PLA%20API%20Integration.md#711-accounts) call. This will cache the updated addresses.

Parameters:

| Parameter  | Description                                                                        | Required | Sample |
|------------|------------------------------------------------------------------------------------|----------|--------|
| ACCOUNT_ID | Id that identifies the account ID. Integer.                                        | True     | 100    |
| OFFSET     | The offset of the first address to return sent as an integer. Defaults to O.       | False    | 0      |
| SIZE       | The number of addresses to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 101,
      "companyName": "Company Name 1",
      "addressLine1": "100 W 5th St",
      "addressLine2": "",
      "city": "Cincinnati",
      "state": "OH",
      "postalCode": "45202",
      "country": "US",
      "addressType": "CPG",
      "active": true
    },
    {
      "id": 102,
      "companyName": "Company Name 2",
      "addressLine1": "433 W Van Buren St",
      "addressLine2": "#610s",
      "city": "Chicago",
      "state": "IL",
      "postalCode": "60607",
      "country": "US",
      "addressType": "AGENCY",
      "active": true
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

#### 7.1.5. Targets

`GET /media/pla/v1/metadata/targets`

Parameters:

| Parameter | Description                                                                      | Required | Sample |
|-----------|----------------------------------------------------------------------------------|----------|--------|
| OFFSET    | The offset of the first target to return sent as an integer. Defaults to O.      | False    | 0      |
| SIZE      | The number of targets to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 1,
      "dimensionType": "PLACEMENTS"
    },
    {
      "id": 2,
      "dimensionType": "DIVISIONS"
    },
    {
      "id": 3,
      "dimensionType": "HOUR"
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

#### 7.1.6. Target - Placements

`GET /media/pla/v1/metadata/placements`

Parameters:

| Parameter | Description                                                                         | Required | Sample |
|-----------|-------------------------------------------------------------------------------------|----------|--------|
| OFFSET    | The offset of the first placement to return sent as an integer. Defaults to O.      | False    | 0      |
| SIZE      | The number of placements to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 1,
      "name": "Search & Browse",
      "description": "Search & Browse PLA",
      "active": true,
      "priceFloor": 0.5
    },
    {
      "id": 2,
      "name": "Basket Builder",
      "description": "Basket Builder PLA",
      "active": true,
      "priceFloor": 0.6
    },
    {
      "id": 3,
      "name": "Savings",
      "description": "Savings PLA",
      "active": true,
      "priceFloor": 0.3
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

#### 7.1.7. Target - Divisions

`GET /media/pla/v1/metadata/divisions`

Parameters:

| Parameter | Description                                                                        | Required | Sample |
|-----------|------------------------------------------------------------------------------------|----------|--------|
| OFFSET    | The offset of the first division to return sent as an integer. Defaults to O.      | False    | 0      |
| SIZE      | The number of divisions to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 1,
      "name": "011 Atlanta",
      "active": true
    },
    {
      "id": 2,
      "name": "014 Cincinnati",
      "active": true
    },
    {
      "id": 3,
      "name": "016 Columbus",
      "active": true
    },
    {
      "id": 4,
      "name": "018 Michigan",
      "active": true
    },
    {
      "id": 5,
      "name": "021 Central",
      "active": true
    },
    {
      "id": 6,
      "name": "024 Louisville",
      "active": true
    },
    {
      "id": 7,
      "name": "024 JayC",
      "active": true
    },
    {
      "id": 8,
      "name": "025 Delta",
      "active": true
    },
    {
      "id": 9,
      "name": "026 Nashville",
      "active": true
    },
    {
      "id": 10,
      "name": "029 Mid Atlantic",
      "active": true
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": true
    }
  }
}
```

#### 7.1.8. Products

`GET /media/pla/v1/metadata/products?advertiserId={{ADVERTISER_ID}}`

Parameters:

| Parameter     | Description                                                                        | Required | Sample |
|---------------|------------------------------------------------------------------------------------|----------|--------|
| ADVERTISER_ID | Id that identified the advertiser.                                                 | True     | 12     |
| OFFSET        | The offset of the first product to return sent as an integer. Defaults to O.      | False    | 0      |
| SIZE          | The number of products to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 1000231,
      "upc": "0004300000287",
      "name": "My Brand Original Cheese Sauce Pouches",
      "packshot": "https://www.kroger.com/product/images/medium/front/0004300000287",
      "price": 3.99,
      "maxSuggestedBid": 0.7,
      "minSuggestedBid": 0.4,
      "brand": "My Brand",
      "category": "Sour Cream & Dips",
      "subcategory": "Cheese Dips",
      "available": true
    },
    {
      "id": 1000231,
      "upc": "0004300000287",
      "name": "My Brand Shells and Cheese Macaroni and Cheese Cups Easy Microwavable Dinner",
      "packshot": "https://www.kroger.com/product/images/medium/front/0004300000287",
      "price": 3.99,
      "maxSuggestedBid": 0.7,
      "minSuggestedBid": 0.4,
      "brand": "My Brand",
      "category": "Packaged Meals & Sides",
      "subcategory": "Macaroni & Cheese",
      "available": true
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 2,
      "hasMore": true
    }
  }
}
```

### 7.2. Campaign Management APIs

#### 7.2.1. V1 Campaign Management APIs


##### 7.2.1.1. Create Campaign

`POST /media/pla/v1/campaigns`

Fields:

| Field                    | Description                                                                                                                                         | Required | Type                                           |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|----------|------------------------------------------------|
| name                     | The campaign name. Cannot contain the following characters: %"'*#@!^$~`<>?/\{}[]                                                                    | True     | String                                         |
| status                   | The status of the campaign                                                                                                                          | True     | Enum (DRAFT, SCHEDULED, ACTIVE, ENDED, PAUSED) |
| startDate                | The start date of the campaign.                                                                                                                     | True     | Date (YYYY-MM-DD)                              |
| endDate                  | The end date of the campaign. Must be after start date. If null the campaign is considered "always-on". Cannot be null if budget type is `LIFETIME` | True     | Date (YYYY-MM-DD) or null                      |
| budgetAmount             | The total budget of the campaign. The sum of all the budgets from the ad group(s) may not exceed this number.                                       | True     | Float                                          |
| budgetType               | The type of budget.                                                                                                                                 | True     | Enum (DAILY, WEEKLY, MONTHLY, LIFETIME)        |
| pacingType               | The pacing for the campaign                                                                                                                         | True     | Enum (EVEN, ASAP)                              |
| accountId                | Id from the Account entity.                                                                                                                         | True     | Integer                                        |
| advertiserId             | Id from the Advertiser entity associated with the account.                                                                                          | True     | Integer                                        |
| billingInsertionOrder    | Insertion order number for this campaign.                                                                                                           | False    | String                                         |
| billingPurchaseOrder     | Purchase order number for this campaign.                                                                                                            | False    | String                                         |
| billingAdditionalDetails | Notes that the advertiser wants to notify the billing department.                                                                                   | False    | String                                         |
| billingContactId         | Id from the Contact entity associated with the account.                                                                                             | True     | Integer                                        |
| billingAddressId         | Id from the Address entity associated with the account.                                                                                             | True     | Integer                                        |


Payload:

```json
{
  "name": "Summer 2023 Campaign",
  "status": "DRAFT",
  "startDate": "2023-07-01",
  "endDate": null,
  "budgetAmount": 25000,
  "budgetType": "MONTHLY",
  "pacingType": "EVEN",
  "accountId": 100,
  "advertiserId": 12,
  "billingInsertionOrder": "",
  "billingPurchaseOrder": "",
  "billingAdditionalDetails": "",
  "billingContactId": 102,
  "billingAddressId": 5001
}
```

Sample **success** response:

```json
{
  "data": {
    "id": 1000231,
    "name": "Summer 2023 Campaign",
    "status": "DRAFT",
    "startDate": "2023-07-01",
    "endDate": null,
    "budgetAmount": 25000,
    "budgetType": "MONTHLY",
    "pacingType": "EVEN",
    "accountId": 100,
    "advertiserId": 12,
    "billingInsertionOrder": "",
    "billingPurchaseOrder": "",
    "billingAdditionalDetails": "",
    "billingContactId": 102,
    "billingAddressId": 5001
  },
  "meta": {
    "success": true
  }
}
```

Sample **400 error** response (start date was set after end date in the payload):

```json
{
  "detail": [
    {
      "msg": "Campaign end date must be after start date"
    }
  ]
}
```

Sample **422 error** response (start date was not sent in the payload):

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "startDate"
      ],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

##### 7.2.1.2. Get Campaigns by Advertiser Id

`GET /media/pla/v1/campaigns?advertiserId={{ADVERTISER_ID}}`

Parameters:

| Parameter     | Description                                                                        | Required | Sample |
|---------------|------------------------------------------------------------------------------------|----------|--------|
| ADVERTISER_ID | Id that identified the advertiser.                                                 | True     | 12     |
| OFFSET        | The offset of the first campaign to return sent as an integer. Defaults to O.      | False    | 0      |
| SIZE          | The number of campaigns to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10     |

Sample response:

```json
{
  "data": [
    {
      "id": 1000231,
      "name": "Summer 2023 Campaign",
      "status": "ACTIVE",
      "startDate": "2023-07-01",
      "endDate": "2023-07-31",
      "budgetAmount": 25000,
      "budgetType": "MONTHLY",
      "pacingType": "EVEN",
      "accountId": 100,
      "advertiserId": 12,
      "billingInsertionOrder": "",
      "billingPurchaseOrder": "",
      "billingAdditionalDetails": "",
      "billingContactId": 102,
      "billingAddressId": 5001
    },
    {
      "id": 1000233,
      "name": "Fall 2023 Campaign",
      "status": "DRAFT",
      "startDate": "2023-09-01",
      "endDate": "2023-09-31",
      "budgetAmount": 25000,
      "budgetType": "WEEKLY",
      "pacingType": "EVEN",
      "accountId": 100,
      "advertiserId": 12,
      "billingInsertionOrder": "",
      "billingPurchaseOrder": "",
      "billingAdditionalDetails": "",
      "billingContactId": 102,
      "billingAddressId": 5001
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

##### 7.2.1.3. Get Campaign By Id

`GET /media/pla/v1/campaigns/{{CAMPAIGN_ID}}`

Path Parameters:

| Parameter   | Description                      | Required | Sample  |
|-------------|----------------------------------|----------|---------|
| CAMPAIGN_ID | Id that identified the campaign. | True     | 1000231 |

Query Parameters:

| Parameter        | Description                                                               | Required | Sample |
|------------------|---------------------------------------------------------------------------|----------|--------|
| include.adgroups | If true, returns the ad groups associated with this campaign as an array. | False    | false  |

Sample response:

```json
{
  "data": {
    "id": 1000231,
    "name": "Summer 2023 Campaign",
    "status": "DRAFT",
    "startDate": "2023-07-01",
    "endDate": "2023-07-31",
    "budgetAmount": 25000,
    "budgetType": "MONTHLY",
    "pacingType": "EVEN",
    "accountId": 100,
    "advertiserId": 12,
    "billingInsertionOrder": "",
    "billingPurchaseOrder": "",
    "billingAdditionalDetails": "",
    "billingContactId": 102,
    "billingAddressId": 5001
  },
  "meta": {
    "success": true
  }
}
```

##### 7.2.1.4. Update Campaign

`PUT /media/pla/v1/campaigns/{{CAMPAIGN_ID}}`

Path Parameters:

| Parameter   | Description                      | Required | Sample  |
|-------------|----------------------------------|----------|---------|
| CAMPAIGN_ID | Id that identified the campaign. | True     | 1000231 |

Notes:

- If the campaign has the status of `DRAFT` the following fields can be updated: Name, status, start date, end date, budget amount, budget type, pacing type, billing insertion order, billing purchase order, billing additional details.
- If the campaign has the status of `ACTIVE`, `SCHEDULED` or `PAUSED` the following fields can be updated: Name, status, end date, pacing type, budget amount, billing additional details.
- Both startDate and status can not be updated in the same request, status changes should be processed in a seperate API call.
- To stop a live campaign, change the end date to today's date.
- To cancel a scheduled campaign, set the status to PAUSE and set the end date to match the start date.

Payload:

```json
{
  "name": "Summer 2023 Campaign - Update",
  "endDate": "2023-08-31",
  "budgetAmount": 25000,
  "pacingType": "EVEN",
  "billingAdditionalDetails": "",
  "status": "PAUSED"
}
```

Sample response:

```json
{
  "data": {
    "id": 1000231,
    "name": "Summer 2023 Campaign - Update",
    "status": "ACTIVE",
    "startDate": "2023-07-01",
    "endDate": "2023-08-31",
    "budgetAmount": 25000,
    "budgetType": "MONTHLY",
    "pacingType": "EVEN",
    "accountId": 100,
    "advertiserId": 12,
    "billingInsertionOrder": "",
    "billingPurchaseOrder": "",
    "billingAdditionalDetails": "",
    "billingContactId": 102,
    "billingAddressId": 5001
  },
  "meta": {
    "success": true
  }
}
```

##### 7.2.1.5. Create Ad Group

`POST /media/pla/v1/adgroups`

Notes:

- Ad groups allow multiple placements, however, when more than one is selected the base bid and the bid amounts must be higher than the highest floor price specified in the placements API.
- Ad least one **placement target** must be included in the campaign. 
- If no **divisions target** is set, the ad group will default to include all divisions. 
- Only one **day parting target** is allowed.

Ad Group Fields:

| Field                    | Description                                                                                                                                      | Required | Type                                                   |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|----------|--------------------------------------------------------|
| campaignId               | The campaign id associated with this ad group.                                                                                                   | True     | Integer                                                |
| name                     | The ad group name.                                                                                                                               | True     | String                                                 |
| startDate                | The start date of the ad group.                                                                                                                  | True     | Date (YYYY-MM-DD)                                      |
| endDate                  | The end date of the ad group. If null the ad group is considered "always-on" and will stop when/if the campaign has an end date.                 | True     | Date (YYYY-MM-DD) or null                              |
| budgetAmount             | The budget of the ad group. The sum of all the budgets from the ad group(s) may not exceed the campaign budget.                                  | True     | Float                                                  |
| status                   | The status of the ad group.                                                                                                                      | True     | Enum (DRAFT, SCHEDULED, ACTIVE, ENDED, PAUSED, FAILED) |
| baseBid                  | The base bid used for all entities that have the useBaseBid flag as true. It must be above the highers floor price of the placement(s) selected. | True     | Float                                                  |
| entities                 | The products to be advertised                                                                                                                    | True     | Array                                                  |
| targets                  | The target dimensions for this ad group. Includes placements, divisions, and day parting.                                                        | True     | Array                                                  |                                            |

Entity (Product) Fields:

| Field       | Description                                                                        | Required | Type    |
|-------------|------------------------------------------------------------------------------------|----------|---------|
| id          | The id of the product to be advertised.                                            | True     | Integer |
| useBaseBid  | Flag that set the base bid of the ad group for the product.                        | True     | Boolean |
| bidAmount   | The bid amount for this product. Required if useBaseBid is false.                  | False    | Float   |
| deleted     | The id of the product to be advertised.                                            | True     | Boolean |

Target (Dimension) Fields:

| Field  | Description                                                                                                                                                                                     | Required | Type              |
|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-------------------|
| type   | The id of the target. Retrieved from the targets endpoint.                                                                                                                                      | True     | Integer           |
| id     | The id of the entity that belongs to the target. Required if target is **placement** and **division**.                                                                                          | False    | Boolean           |
| values | The bid amount for this product. Required if target is **hour**. Must be an array of two integers. Integers must be in the rage of 0 to 24. The first integer must be less than the second one. | False    | Array of integers |

Payload:

```json
{
  "campaignId": 1000231,
  "name": "Ad Group 1",
  "startDate": "2023-07-01",
  "endDate": "2023-07-31",
  "budgetAmount": 25000,
  "status": "DRAFT",
  "baseBid": 0.85,
  "entities": [
    {
      "id": 1000231,
      "useBaseBid": true,
      "bidAmount": null,
      "deleted": false
    },
    {
      "id": 1000232,
      "useBaseBid": false,
      "bidAmount": 1.1,
      "deleted": false
    }
  ],
  "targets": [
    {
      "type": 1,
      "id": 1
    },
    {
      "type": 1,
      "id": 2
    },
    {
      "type": 1,
      "id": 3
    },
    {
      "type": 2,
      "id": 2
    },
    {
      "type": 3,
      "values": [
        10,
        20
      ]
    }
  ]
}
```

Sample **success** response:

```json
{
  "data": {
    "adGroupId": 2343223,
    "campaignId": 1000231,
    "name": "Ad Group 1",
    "startDate": "2023-07-01",
    "endDate": "2023-07-31",
    "budgetType": "MONTHLY",
    "budgetAmount": 25000,
    "status": "ACTIVE",
    "baseBid": 0.85,
    "entities": [
      {
        "id": 1000231,
        "useBaseBid": true,
        "bidAmount": null,
        "deleted": false
      },
      {
        "id": 1000232,
        "useBaseBid": false,
        "bidAmount": 1.1,
      "deleted": false
      }
    ],
    "targets": [
      {
        "type": 1,
        "id": 1
      },
      {
        "type": 1,
        "id": 2
      },
      {
        "type": 1,
        "id": 3
      },
      {
        "type": 2,
        "id": 2
      },
      {
        "type": 3,
        "values": [
          10,
          20
        ]
      }
    ]
  },
  "meta": {
    "success": true
  }
}
```

Sample **400 error** response (base bid was lower than the floor price of one of the selected placements):

```json
{
  "detail": [
    {
      "msg": "Base bid must be greater than 0"
    }
  ]
}
```

Sample **422 error** response (campaign id was not sent in the payload):

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "campaignId"
      ],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

##### 7.2.1.6. Get Ad Groups by Campaign Id

`GET /media/pla/v1/adgroups?campaignId={{CAMPAIGN_ID}}`

Parameters:

| Parameter   | Description                                                                        | Required | Sample  |
|-------------|------------------------------------------------------------------------------------|----------|---------|
| CAMPAIGN_ID | Id that identified the campaign.                                                   | True     | 1000231 |
| OFFSET      | The offset of the first ad group to return sent as an integer. Defaults to O.      | False    | 0       |
| SIZE        | The number of ad groups to return sent as an integer. Defaults to 1O. Maximum 100. | False    | 10      |

Sample response:

```json
{
  "data": [
    {
      "adGroupId": 2343223,
      "campaignId": 1000231,
      "name": "Ad Group 1",
      "startDate": "2023-07-01",
      "endDate": "2023-07-31",
      "budgetType": "MONTHLY",
      "budgetAmount": 25000,
      "status": "ACTIVE",
      "baseBid": 0.85,
      "entities": [
        {
          "id": 1000231,
          "useBaseBid": true,
          "bidAmount": null,
          "deleted": false
        },
        {
          "id": 1000232,
          "useBaseBid": false,
          "bidAmount": 1.1,
          "deleted": false
        }
      ],
      "targets": [
        {
          "type": 1,
          "id": 1
        },
        {
          "type": 1,
          "id": 2
        },
        {
          "type": 1,
          "id": 3
        },
        {
          "type": 2,
          "id": 2
        }
      ],
      "keywordBidModifiers": [
        {
            "keyword": "keyword 1",
            "modifier": 0.75,
            "deleted": false
        },
        {
            "keyword": "keyword 2",
            "modifier": 0.25,
            "deleted": false
        }
      ]
    },
    {
      "adGroupId": 2343299,
      "campaignId": 1000231,
      "name": "Ad Group 2",
      "startDate": "2023-07-01",
      "endDate": "2023-07-31",
      "budgetType": "MONTHLY",
      "budgetAmount": 25000,
      "status": "ACTIVE",
      "baseBid": 0.85,
      "entities": [
        {
          "id": 1000231,
          "useBaseBid": true,
          "bidAmount": null,
          "deleted": false
        },
        {
          "id": 1000232,
          "useBaseBid": false,
          "bidAmount": 1.1,
          "deleted": false
        }
      ],
      "targets": [
        {
          "type": 1,
          "id": 1
        },
        {
          "type": 1,
          "id": 2
        },
        {
          "type": 1,
          "id": 3
        },
        {
          "type": 2,
          "id": 2
        }
      ],
      "keywordBidModifiers": [
        {
            "keyword": "keyword 1",
            "modifier": 0.75,
            "deleted": false
        },
        {
            "keyword": "keyword 2",
            "modifier": 0.25,
            "deleted": false
        }
      ]
    }
  ],
  "meta": {
    "page": {
      "offset": 0,
      "size": 10,
      "hasMore": false
    }
  }
}
```

##### 7.2.1.7. Get Ad Group By Id

`GET /media/pla/v1/adgroups/{{ADGROUP_ID}}`

Parameters:

| Parameter  | Description                      | Required | Sample  |
|------------|----------------------------------|----------|---------|
| ADGROUP_ID | Id that identified the Ad Group. | True     | 2343299 |

Sample response:

```json
{
  "data": {
    "adGroupId": 2343299,
    "campaignId": 1000231,
    "name": "Ad Group 2",
    "startDate": "2023-07-01",
    "endDate": "2023-07-31",
    "budgetType": "MONTHLY",
    "budgetAmount": 25000,
    "status": "ACTIVE",
    "baseBid": 0.85,
    "entities": [
      {
        "id": 1000231,
        "useBaseBid": true,
        "bidAmount": null,
        "deleted": false
      },
      {
        "id": 1000232,
        "useBaseBid": false,
        "bidAmount": 1.1,
        "deleted": false
      }
    ],
    "targets": [
      {
        "type": 1,
        "id": 1
      },
      {
        "type": 1,
        "id": 2
      },
      {
        "type": 1,
        "id": 3
      },
      {
        "type": 2,
        "id": 2
      }
    ],
    "keywordBidModifiers": [
      {
          "keyword": "keyword 1",
          "modifier": 0.75,
          "deleted": false
      },
      {
          "keyword": "keyword 2",
          "modifier": 0.25,
          "deleted": false
      }
    ]
  },
  "meta": {
    "success": true
  }
}
```

##### 7.2.1.8. Update Ad Group

`PUT /media/pla/v1/adgroups/{{ADGROUP_ID}}`

Parameters:

| Parameter  | Description                      | Required | Sample  |
|------------|----------------------------------|----------|---------|
| ADGROUP_ID | Id that identified the Ad Group. | True     | 2343299 |

Notes:

- This API allows updates to the ad group entity. The information sent will replace/override the existing information.
- If the intent is to only update the entities object or the base bid use the PATCH Entities API call below.
- Target `Placement` updates **are NOT** allowed for ad groups that have the status `ACTIVE`.
- Target `Division` updates **are** allowed.
- Target `Hour` updates **are** allowed.
- If Targets are sent, it will replace all existing targets even if they are not send on the request.
- Keyword modifiers can only be modified as long as the `Search and Browse` placement is present.
- No changes will be processed for `ENDED` and `FAILED` ad groups.

`Draft` Ad Groups Fields allowed:

- name
- startDate
- endDate
- budgetAmount
- status (Can only be changed to **SCHEDULED** or **ACTIVE** depending on the start date)
- targets (Placement, Division, and Hour)

`Scheduled` Ad Groups Fields allowed:

- name
- startDate
- endDate
- budgetAmount
- status (Can only be changed to **PAUSED** status)
- targets (Placement, Division, and Hour)

`Active` Ad Groups Fields allowed:

- name
- endDate
- budgetAmount
- status (Can only be changed to **PAUSED** status)
- targets (Division and Hour)

`Paused` Ad Groups Fields allowed:

- name
- endDate
- budgetAmount
- status (Can only be changed to **ACTIVE** status)
- targets (Division and Hour)


Payload:

```json
{
  "name": "Ad Group 1 - Modified",
  "endDate": "2023-07-21",
  "budgetAmount": 25000,
  "targets": [
    {
      "type": 1,
      "id": 1
    },
    {
      "type": 1,
      "id": 2
    },
    {
      "type": 1,
      "id": 3
    },
    {
      "type": 2,
      "id": 2
    },
    {
      "type": 3,
      "values": [
        10,
        20
      ]
    }
  ],
  "keywordBidModifiers": [
    {
        "keyword": "keyword 1",
        "modifier": 0.75,
        "deleted": false
    },
    {
        "keyword": "keyword 2",
        "modifier": 0.25,
        "deleted": false
    }
  ]
}
```

Sample response:

```json
{
  "data": {
    "adGroupId": 2343223,
    "campaignId": 1000231,
    "name": "Ad Group 1 - Modified",
    "startDate": "2023-07-01",
    "endDate": "2023-07-21",
    "budgetType": "MONTHLY",
    "budgetAmount": 25000,
    "status": "ACTIVE",
    "baseBid": 0.85,
    "entities": [
      {
        "id": 1000231,
        "useBaseBid": true,
        "bidAmount": null,
        "deleted": false
      },
      {
        "id": 1000232,
        "useBaseBid": false,
        "bidAmount": 1.1,
        "deleted": false
      }
    ],
    "targets": [
      {
        "type": 1,
        "id": 1
      },
      {
        "type": 1,
        "id": 2
      },
      {
        "type": 1,
        "id": 3
      },
      {
        "type": 2,
        "id": 2
      },
      {
        "type": 3,
        "values": [
          10,
          20
        ]
      }
    ],
    "keywordBidModifiers": [
      {
          "keyword": "keyword 1",
          "modifier": 0.75,
          "deleted": false
      },
      {
          "keyword": "keyword 2",
          "modifier": 0.25,
          "deleted": false
      }
    ]
  },
  "meta": {
    "success": true
  }
}
```

##### 7.2.1.9. Update Ad Group Entities

`PATCH /media/pla/v1/adgroups/{{ADGROUP_ID}}/entities`

Parameters:

| Parameter  | Description                      | Required | Sample  |
|------------|----------------------------------|----------|---------|
| ADGROUP_ID | Id that identified the Ad Group. | True     | 2343299 |

Notes:

- This API allows updates to the entity array.
- `baseBid` is an optional field.
- Existing entities that match are not deleted will be updated with the new values under `useBaseBid` and `bidAmount`.
- New entities will be added to the ad group.
- Entities with the field `deleted` as `true` will be removed from the ad group. 
- Bad request error will be return if any of the entities has a bid amount lower than the ad group placement(s) floor price.
- It will return all the ad group entity object after updates.
- Response does not return entities that have been deleted.

Payload:

```json
{
  "baseBid": 0.85,
  "entities": [
    {
      "id": 1000231,
      "useBaseBid": true,
      "bidAmount": null,
      "deleted": true
    },
    {
      "id": 1000232,
      "useBaseBid": false,
      "bidAmount": 1.1,
      "deleted": false
    },
    {
      "id": 1000233,
      "useBaseBid": false,
      "bidAmount": 1.25,
      "deleted": false
    }
  ]
}
```

Sample response:

```json
{
  "data": {
    "adGroupId": 2343223,
    "campaignId": 1000231,
    "name": "Ad Group 1",
    "startDate": "2023-07-01",
    "endDate": "2023-07-31",
    "budgetType": "MONTHLY",
    "budgetAmount": 25000,
    "status": "ACTIVE",
    "baseBid": 0.85,
    "entities": [
      {
        "id": 1000232,
        "useBaseBid": false,
        "bidAmount": 1.1,
        "deleted": false
      },
      {
        "id": 1000233,
        "useBaseBid": false,
        "bidAmount": 1.25,
        "deleted": false
      }
    ],
    "targets": [
      {
        "type": 1,
        "id": 1
      },
      {
        "type": 1,
        "id": 2
      },
      {
        "type": 1,
        "id": 3
      },
      {
        "type": 2,
        "id": 2
      },
      {
        "type": 3,
        "values": [
          10,
          20
        ]
      }
    ]
  },
  "meta": {
    "success": true
  }
}
```

##### 7.2.1.10. Get Eligible Keywords by Ad Group Id

`GET /media/pla/v1/adgroups/{{ADGROUP_ID}}/keywords`

Parameters:

| Parameter  | Description                      | Required | Sample  |
|------------|----------------------------------|----------|---------|
| ADGROUP_ID | Id that identified the Ad Group. | True     | 2343299 |

Notes:

- This API grabs up to 100 keywords that the given ad group is eligible to target.

Sample response:

```json
{
  "data": [
    "fromage",
    "gourmet cheese",
    "carrs crackers",
    "goat cheese log",
    "chip dip",
    "boursin cheese",
    "port wine",
    "sesame crackers",
    "gouda cheese",
  ]
}
```

##### 7.2.1.11. Update Ad Group Keyword Bid Modifiers

`PATCH /media/pla/v1/adgroups/{{ADGROUP_ID}}/keywords`

Parameters:

| Parameter  | Description                      | Required | Sample  |
|------------|----------------------------------|----------|---------|
| ADGROUP_ID | Id that identified the Ad Group. | True     | 2343299 |

Notes:

- This API allows for modifying keyword bid modifers for the given ad group
- Keyword modifiers may only be added to ad groups with the `Search and Browse` placement
- The response is the full ad group including the modified keywords

Payload:

```json
{
  "keywordBidModifiers": [
    {
        "keyword": "keyword 1",
        "modifier": 0.75,
        "deleted": false
    },
    {
        "keyword": "keyword 2",
        "modifier": 0.25,
        "deleted": false
    }
  ]
}
```

Sample Response:

```json
{
  "data": {
    "adGroupId": 2343299,
    "campaignId": 1000231,
    "name": "Ad Group 2",
    "startDate": "2023-07-01",
    "endDate": "2023-07-31",
    "budgetType": "MONTHLY",
    "budgetAmount": 25000,
    "status": "ACTIVE",
    "baseBid": 0.85,
    "entities": [
      {
        "id": 1000231,
        "useBaseBid": true,
        "bidAmount": null,
        "deleted": false
      },
      {
        "id": 1000232,
        "useBaseBid": false,
        "bidAmount": 1.1,
        "deleted": false
      }
    ],
    "targets": [
      {
        "type": 1,
        "id": 1
      },
      {
        "type": 1,
        "id": 2
      },
      {
        "type": 1,
        "id": 3
      },
      {
        "type": 2,
        "id": 2
      }
    ],
    "keywordBidModifiers": [
      {
          "keyword": "keyword 1",
          "modifier": 0.75,
          "deleted": false
      },
      {
          "keyword": "keyword 2",
          "modifier": 0.25,
          "deleted": false
      }
    ]
  },
  "meta": {
    "success": true
  }
}
```

##### 7.2.1.12. System Constants

**Budget Types**

| Value    | Description                                                          |
|----------|----------------------------------------------------------------------|
| DAILY    | Budget is spent on a daily basis for the duration of the campaign.   |
| WEEKLY   | Budget is spent on a weekly basis for the duration of the campaign.  |
| MONTHLY  | Budget is spent on a monthly basis for the duration of the campaign. |
| LIFETIME | Budget is spent until met.                                           |

**Pacing Types**

| Value | Description                                                                                                                              |
|-------|------------------------------------------------------------------------------------------------------------------------------------------|
| EVEN  | A remaining budget should be spent evenly over the number of days remaining within a Budget Type and evenly within the given day itself. |
| ASAP  | The total budget can be spent as fast as possible within the total time period of a given Budget Type.                                   |

**Campaign Status**

| Value     | Description                                                                                                                                                                                                                                                                                         |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DRAFT     | Campaign is not ready to launch. If the start date is today or in the past, the campaign can be activated by sending the `ACTIVE` status. If the start date is in the future, activate the campaign by sending the `SCHEDULED` status. A minimum of one Ad group is required to change this status. |
| SCHEDULED | Campaign has been submitted and is ready to go-live when current date matches the start date. This status will change to `ACTIVE` automatically.                                                                                                                                                    |
| ACTIVE    | Campaign is live in the system. It will automatically changed to `ENDED` when it reaches its end date. Can be changed to `PAUSED` via an update call.                                                                                                                                               |
| ENDED     | Campaign has ended. No changes can be done to the campaign or its ad group(s).                                                                                                                                                                                                                      |
| PAUSED    | Campaign has been paused. Can be changed to `ACTIVE` or `SCHEDULED` depending on the start date via an update call. Campaigns with this status will change to `ENDED` if they reach the end date. Pausing a campaign pauses spend of all associated ad groups (Ad group status will not change).    |

4.4 Ad Group Status

| Value     | Description                                                                                                                                                                                                                                                                                                                                        |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DRAFT     | Ad group is been created. If the start date is today or in the past, the ad group can be activated by sending the `ACTIVE` status. If the start date is in the future, activate the ad group by sending the `SCHEDULED` status. Activating the first ad group of a camping will result in the campaign changing status to `ACTIVE` or `SCHEDULED`. |
| SCHEDULED | Ad group has been submitted and is ready to go-live when current date matches the start date.                                                                                                                                                                                                                                                      |
| ACTIVE    | Ad group is live in the system. It will automatically changed to `ENDED` when it reaches its end date. Can be changed to `PAUSED` via an update call.                                                                                                                                                                                              |
| ENDED     | Ad group has ended. No changes can be done to it.                                                                                                                                                                                                                                                                                                  |
| PAUSED    | Ad group has been paused. Can be changed to `ACTIVE` via an update call. Ad groups with this status will change to `ENDED` if they reach the end date.`ENDED`.                                                                                                                                                                                     |
| FAILED    | Ad group has failed publishing. Contact us to solve this issue.                                                                                                                                                                                                                                                                                    |
### 7.3. Reporting APIs

#### 7.3.1. Report

**Available dimensions**

| Name                  | Description                                                                     |
|-----------------------|---------------------------------------------------------------------------------|
| placement             | The corresponding placement of the ad                                           |
| division_banner       | The corresponding division and banner related to the ad                         |
| keyword               | The corresponding keyword related to the ad                                     |
| ad_group_id           | The ID for the ad group related to the activity                                 |
| ad_group_name         | The name of the ad group related to the activity                                |
| advertiser_id         | The ID for the advertiser related to the activity                               |
| advertiser_name       | The name of the advertiser related to the activity                              |
| campaign_id           | The ID for the campaign related to the activity                                 |
| campaign_name         | The name for the campaign related to the activity                               |
| conversion_source     | Where the conversion happened - this is equivalent to modality.                 |
| daily_date            | The date the activity occurred                                                  |
| entity_id             | The ID for the entity related to the activity. This will be the UPC ID          |
| entity_name           | The name of the entity related to the activity. This will be the product name   |
| purchased_entity_id   | The ID for the product that was purchased                                       |
| purchased_entity_name | The name of the product that was purchased                                      |

**Available metrics**

| Name                    | Description                                                                                                               |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------|
| click_through_rate      | The percentage of impressions that resulted in a click on your ad, generated from a click, and the entity can be different than the one in the ad |
| clicked_conversion_rate | The percentage of interactions on your ad that resulted in a conversion, generated from a click, and the entity can be different than the one in the ad |
| clicked_order_value_avg | The average revenue per conversion, generated from a click, and the entity can be different than the one in the ad         |
| clicked_unit_price_avg  | The average price per unit purchased, generated from a click, and the entity can be different than the one in the ad. Units for Kroger will be individual products.   |
| clicks                  | The count of times your ad was clicked on by a user	                                                                       |
| cost                    | The amount of money spent for the desired actions	                                                                         |
| cost_per_click          | The average amount spent on a click within a CPC model                                                                     |
| cost_per_thousand       | The average amount spent per 1000 impressions within a CPM model                                                           |
| cost_per_transaction    | The average amount spent per conversion	                                                                                   |
| halo_revenue            | (Clicked Revenue) Default metric shown in Media Platform UI. The revenue generated from a click, and the entity can be different than the one in the ad	 |
| halo_roas               | (Clicked ROAS) Default metric shown in Media Platform UI. The return on ad spend generated from a click, and the entity can be different than the one in the ad |
| halo_transactions       | (Clicked Transactions) Default metric shown in Media Platform UI. The number of transactions generated from a click, and the entity can be different than the one in the ad  |
| halo_units              | (Clicked Units) Default metric shown in Media Platform UI. The number of units generated from a click, and the entity can be different than the one in the ad  |
| halo_exposed_revenue	  | (Viewed Revenue) 	The revenue generated from an impression or a click, and the entity can be different than the one in the ad |
| halo_exposed_roas       | (Viewed ROAS) The return on ad spend generated from an impression or a click; the entity can be different than the one in the ad |
| halo_exposed_transactions | (Viewed Transactions) The number of transactions generated from an impression or a click, and the entity can be different than the one in the ad |
| halo_exposed_units      | (Viewed Units) The number of units generated from an impression or a click, and the entity can be different than the one in the ad |
| impressions             | The number of times your ad was viewed by the end user                                                                     |
| ad_group_budget         | The budget for the ad group in the report	                                                                                 |
| ad_group_budget_type    | The budget type for the ad group in the report	                                                                           |
| ad_group_end_date       | The end date for the ad group in the report	                                                                               |
| ad_group_start_date     | The start date for the ad group in the report	                                                                             |
| ad_group_status         | The current status for the ad group in the report	                                                                         |
| base_bid                | The bid on the ad group in the report	                                                                                     |
| bid_type                | The bid type for the ad group in the report - will be `CPC` or `CPM`	                                                     |
| campaign_budget         | The budget for the campaign in the report                                 	                                               |
| campaign_budget_type    | The budget type for the campaign in the report	                                                                           |
| campaign_end_date       | The end date for the campaign in the report	                                                                               |
| campaign_start_date     | The start date for the campaign in the report	                                                                             |
| campaign_status         | The current status for the campaign in the report	                                                                         |
| entity_bid              | The bid at either the sub-commodity or UPC level	                                                                         |
| pacing                  | The pacing setting for the media. Will be ASAP or Evenly          	                                                       |
| use_base_bid            | The flag indicating if the entity is using the ad group-level bid  in the auction                                          |
| viewed_order_value_avg  | The average revenue per conversion, generated from a click or an impression, and the entity can be different than the one in the ad   |

**Filter operators available:**

| Name                  |
|-----------------------|
| EQUALS                |
| NOT_EQUALS            |
| GREATER_THAN          |
| GREATER_THAN_OR_EQUAL |
| LESS_THAN             |
| LESS_THAN_OR_EQUAL    |
| LIKE_IN               |
| NOT_IN                |
| IS_NULL               |
| NOT_NULL              |
| NOT_LIKE              |
| BETWEEN               |

**Notes:**

- Attribution window for PLA is 14 days. 
- We recommend pulling data for the day prior no earlier than 3 AM ET that day. This gives a safe buffer for any lingering data that came in at the end of the day to make it into our reporting system.
- We will attribute and conversion events on the day that they occur, not the day that the click or impression occurred, so historical reporting data will not change.
- Reports will sort by `last_modified ASC` by default.
- If no `size` variable is provided, only the first **250 records** will be returned.
- There is a limit of **10,000 records** in the `size` variable.
- For filters the `field` element may contain any `dimension` or `metric`.
- If `sort` fields are provided in the request payload, they **must be valid** `metric`s and/or `dimension`s, that are also provided in the same request payload, respectively.
- `total_count` is the total rows for the criteria, can be more than the `count` indicated in the call.
- Submitting pagination parameters that are out of the result data set will result in a 200 OK response but the data object will be blank.

`POST /media/pla/v1/report`

**Sample request payload:**

```json
{
  "dimensions": [
    "campaign_name",
    "campaign_id",
    "placement",
    "division_banner",
    "keyword",
    "entity_id",
    "entity_name"
  ],
  "metrics": [
    "cost_per_click",
    "click_through_rate",
    "clicked_conversion_rate",
    "impressions"
  ],
  "filters": [
    {
      "field": "impressions",
      "operator": "GREATER_THAN",
      "values": [
        0
      ]
    }
  ],
  "sort": [
    {
      "field": "click_through_rate",
      "order": "DESC"
    }
  ],
  "advertiserIds": [
    9
  ],
  "startDate": "2023-01-01",
  "endDate": "2024-01-01",
  "pagination": {
    "offset": 0,
    "size": 100
  }
}
```

**Sample `success` response payload:**

```json
{
  "headers": [
    {
      "name": "campaign_name",
      "title": "Campaign Name",
      "type": "text"
    },
    {
      "name": "campaign_id",
      "title": "Campaign ID",
      "type": "number"
    },
    {
      "name": "placement",
      "title": "Placement",
      "type": "text"
    },
    {
      "name": "division_banner",
      "title": "Division - Banner",
      "type": "text"
    },
    {
      "name": "keyword",
      "title": "Keyword",
      "type": "text"
    },
    {
      "name": "entity_id",
      "title": "Product ID",
      "type": "text"
    },
    {
      "name": "entity_name",
      "title": "Product Name",
      "type": "text"
    },
    {
      "name": "cost_per_click",
      "title": "Cost Per Click (CPC)",
      "type": "currency"
    },
    {
      "name": "click_through_rate",
      "title": "Click Through Rate (CTR)",
      "type": "percentage"
    },
    {
      "name": "impressions",
      "title": "Impressions",
      "type": "number"
    },
    {
      "name": "clicks",
      "title": "Clicks",
      "type": "number"
    }
  ],
  "data": [
    {
      "campaign_id": 1285413,
      "campaign_name": "Bug 13616 Campaign 2",
      "click_through_rate": 20,
      "clicks": 40,
      "cost_per_click": 0.5,
      "division_banner": null,
      "keyword": null,
      "entity_id": "0007061218581",
      "entity_name": "Armor All® Leather Care Wipes",
      "impressions": 2,
      "placement": null
    },
    {
      "campaign_id": 1285186,
      "campaign_name": "BUG_531 Campaign",
      "click_through_rate": 4,
      "clicks": 4,
      "cost_per_click": 0.5,
      "division_banner": null,
      "keyword": null,
      "entity_id": "0073373900470",
      "entity_name": "NOW  Choline & Inositol",
      "impressions": 1,
      "placement": null
    },
    {
      "campaign_id": 1293587,
      "campaign_name": "kat test overspend campaign 4",
      "click_through_rate": 4,
      "clicks": 4,
      "cost_per_click": 0.225,
      "division_banner": null,
      "keyword": null,
      "entity_id": "0007061218581",
      "entity_name": "Armor All® Leather Care Wipes",
      "impressions": 1,
      "placement": null
    },
    {
      "campaign_id": 1293645,
      "campaign_name": "AEB-481 co test",
      "click_through_rate": 0,
      "clicks": 1,
      "cost_per_click": 0,
      "division_banner": null,
      "keyword": null,
      "entity_id": "0007061218581",
      "entity_name": "Armor All® Leather Care Wipes",
      "impressions": 0,
      "placement": null
    },
    {
      "campaign_id": 1285461,
      "campaign_name": "co test campaign 1",
      "click_through_rate": 0,
      "clicks": 20,
      "cost_per_click": 0.5,
      "division_banner": null,
      "keyword": null,
      "entity_id": "0007061218581",
      "entity_name": "Armor All® Leather Care Wipes",
      "impressions": 0,
      "placement": null
    }
  ],
  "total_count": 5
}
```

**Errors:**

1. Error details may vary depending on the error type. Examples of common errors are listed below.

Status 422 - Unprocessable Entity: A request payload that includes invalid fields (e.g. metrics) was sent.

```json
{
  "detail": [
    {
      "loc": [ ... ],
      "msg": "value is not a valid enumeration member; permitted: [...]",
      "type": "type_error.enum",
      "ctx": { ... }
    }
  ]
}
```

Status 400 - Bad Request: Incorrect usage and/or combinations of accepted reporting fields.

```json
{
  "detail": [
    {
      "code": 1390,
      "error": "error when executing query: {{failure}}",
      "formatting": {
         "failure": "sort must be included in dimension or metrics"
      }
    }
  ]
}
```

```json
{
  "detail": [
    {
      "code": 1027,
      "error": "sort field is invalid: {{field}}",
      "formatting": {
        "field": "campaign_budget"
      }
    }
  ]
}
```
