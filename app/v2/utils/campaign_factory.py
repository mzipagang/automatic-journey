from typing import List

from app.common.view_models import PatchOperation
from app.v2.view_models import CampaignPatchRequest


class CampaignFactory:
    @staticmethod
    def build_campaign(payload: CampaignPatchRequest, operation_type: str, **kwargs):
        campaign_builder = get_builder(operation_type)
        return campaign_builder(payload, **kwargs)


def get_builder(operation_type):
    if operation_type == 'CREATE':
        return build_create_payload
    if operation_type == 'UPDATE':
        return build_update_payload
    raise ValueError(f"Unknown factory operation '{operation_type}'")


def build_create_payload(base_payload: CampaignPatchRequest, **kwargs):
    koddi_advertiser_id = kwargs.get('koddi_advertiser_id', None)
    if koddi_advertiser_id is None:
        raise ValueError(f"Koddi advertiser cannot be {koddi_advertiser_id}")

    if base_payload.startDate is None:
        raise ValueError("Start date cannot be None")

    start_date_str = base_payload.startDate.strftime('%Y-%m-%dT%H:%M:%SZ')

    payload = [
        PatchOperation(op="replace", path="/source", value=base_payload.source),
        PatchOperation(
            op="add",
            path="/externalIDs/-",
            value={"id": int(koddi_advertiser_id), "partner": "KODDI_ADVERTISER_ID"}
        ),
        PatchOperation(op="replace", path="/backgroundInformation", value=base_payload.backgroundInfo),
        PatchOperation(op="replace", path="/budget/amount", value=base_payload.budgetAmount),
        PatchOperation(op="replace", path="/budget/pacingType", value=base_payload.pacingType.value),
        PatchOperation(op="replace", path="/budget/type", value=base_payload.budgetType.value),
        PatchOperation(op="replace", path="/isAlwaysOn", value=base_payload.isAlwaysOn),
        PatchOperation(op="replace", path="/name", value=base_payload.name),
        PatchOperation(op="replace", path="/primaryAccount/brands", value=base_payload.brandIds),
        PatchOperation(
            op="replace",
            path="/additionalBillingDetails",
            value=base_payload.additionalBillingDetails
        ),
        PatchOperation(op="replace", path="/internalContacts", value=base_payload.internalContactList),
        PatchOperation(op="replace", path="/primaryAccount/id", value=base_payload.accountId),
        PatchOperation(
            op="replace",
            path="/startDate",
            value=start_date_str
        ),
        PatchOperation(op="replace", path="/status", value=base_payload.status.value)
    ]

    if base_payload.agencyId is not None:
        # Agency is involved in this campaign
        payload.append(PatchOperation(op="replace", path="/primaryAccount/isAgencyBeingInvolved", value=True))
        payload.append(
            PatchOperation(op="replace", path="/primaryAccount/agency/id", value=base_payload.agencyId)
        )
    else:
        # Agency is not involved in this campaign
        payload.append(PatchOperation(op="replace", path="/primaryAccount/isAgencyBeingInvolved", value=False))

    billing_base_path = "/primaryAccount/billingInfo"
    if base_payload.isAgencyBilled:
        billing_base_path = "/primaryAccount/agency/billingInfo"

    payload.append(PatchOperation(op="replace", path=f"{billing_base_path}/budgetShare", value=100))
    payload.append(PatchOperation(op="replace", path=f"{billing_base_path}/isBeingBilled", value=True))
    payload.extend(__build_purchase_and_insertion_patches(base_payload, billing_base_path))

    if base_payload.endDate is not None and base_payload.endDate != "":
        payload.append(PatchOperation(
            op="replace",
            path="/endDate",
            value=base_payload.endDate.strftime('%Y-%m-%dT%H:%M:%SZ'))
        )
    elif base_payload.endDate is None or base_payload.endDate == "":
        payload.append(PatchOperation(
            op="remove",
            path="/endDate")
        )
        payload.append(PatchOperation(
            op="replace",
            path="/isAlwaysOn",
            value=True)
        )

    create_payload = [patch.dict() for patch in payload]
    return create_payload


def build_update_payload(base_payload: CampaignPatchRequest):
    payload = [
        PatchOperation(op="replace", path="/source", value=base_payload.source),
        PatchOperation(op="replace", path="/backgroundInformation", value=base_payload.backgroundInfo),
        PatchOperation(op="replace", path="/budget/amount", value=base_payload.budgetAmount),
        PatchOperation(op="replace", path="/budget/pacingType", value=base_payload.pacingType.value),
        PatchOperation(op="replace", path="/budget/type", value=base_payload.budgetType.value),
        PatchOperation(op="replace", path="/isAlwaysOn", value=base_payload.isAlwaysOn),
        PatchOperation(op="replace", path="/name", value=base_payload.name),
        PatchOperation(
            op="replace",
            path="/additionalBillingDetails",
            value=base_payload.additionalBillingDetails
        ),
        PatchOperation(op="replace", path="/internalContacts", value=base_payload.internalContactList),
        PatchOperation(op="replace", path="/status", value=base_payload.status.value)
    ]

    if base_payload.startDate is not None:
        payload.append(PatchOperation(
            op="replace",
            path="/startDate",
            value=base_payload.startDate.strftime('%Y-%m-%dT%H:%M:%SZ')
        ))

    billing_base_path = "/primaryAccount/billingInfo"
    if base_payload.isAgencyBilled:
        billing_base_path = "/primaryAccount/agency/billingInfo"

    payload.extend(__build_purchase_and_insertion_patches(base_payload, billing_base_path))

    if base_payload.endDate is not None and base_payload.endDate != "":
        payload.append(PatchOperation(
            op="replace",
            path="/endDate",
            value=base_payload.endDate.strftime('%Y-%m-%dT%H:%M:%SZ'))
        )
    elif base_payload.endDate is None or base_payload.endDate == "":
        payload.append(PatchOperation(
            op="remove",
            path="/endDate")
        )
        payload.append(PatchOperation(
            op="replace",
            path="/isAlwaysOn",
            value=True)
        )

    update_payload = [patch.dict() for patch in payload]
    return update_payload

def __build_purchase_and_insertion_patches(base_payload: CampaignPatchRequest, base_path: str) -> List[PatchOperation]:
    patches = []
    is_po_required = base_payload.isPoRequired
    po_number = base_payload.billingPurchaseOrder
    is_io_required = base_payload.isIoRequired
    io_number = base_payload.billingInsertionOrder

    if is_po_required is not None:
        patches.append(PatchOperation(
            op="replace",
            path=f"{base_path}/isPORequired",
            value=is_po_required
        ))

    if is_io_required is not None:
        patches.append(PatchOperation(
            op="replace",
            path=f"{base_path}/isIORequired",
            value=is_io_required
        ))

    if is_po_required:
        patches.append(PatchOperation(
            op="replace",
            path=f"{base_path}/poNumber",
            value=po_number
        ))
    elif is_po_required is False:
        patches.append(PatchOperation(
            op="replace",
            path=f"{base_path}/poNumber",
            value=""
        ))

    if is_io_required:
        patches.append(PatchOperation(
            op="replace",
            path=f"{base_path}/ioNumber",
            value=io_number
        ))
    elif is_io_required is False:
        patches.append(PatchOperation(
            op="replace",
            path=f"{base_path}/ioNumber",
            value=""
        ))

    return patches
