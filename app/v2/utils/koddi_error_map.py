# This class is used to remap error messages from the Koddi API into more user-friendly messages.
# Any issues that the customers cannot fix themselves (but we can) will include a message to contact support.
class KoddiErrorMap:
    error_map = {
        # Campaign errors
        "custom budgets cannot be always on":
            "Please select a daily, weekly or monthly budget for always on campaigns.",
        "cannot disable always on when there are children with always on enabled":
            "Please adjust ad group end dates before updating campaign.",
        "cannot edit start date when Campaign is in progress":
            "Start date cannot be changed for an in-progress campaign. Please contact Support for assistance.",
        "status is invalid for date range":
            "Status is invalid for the selected date range. Please contact Support for assistance.",
        "Error creating campaign":
            "Error creating or updating campaign, please try again.",

        # Ad Group errors
        "ad group name must be unique within a campaign":
            "Please select an ad group name that is unique for this campaign.",
        "end date is required when always on is not set":
            (
                "End date is required for ad groups where the always on flag is not set. "
                "Please contact Support for assistance."
            ),
        "ad group cannot be always on when campaign is not always on":
            "Ad group cannot be always on if the campaign is not always on.",
        "cannot edit ended Ad Group":
            "Sorry, you cannot edit an ad group that has ended.",
        "cannot edit start date when Ad Group is in progress":
            "Start date cannot be changed for an in-progress ad group. Please contact Support for assistance.",
        "start and/or end date cannot be in the past":
            "Start and/or end dates cannot be in the past. Please select a future date.",
        "attribute_key_values invalid":
            (
                "One or more of the commodities selected for attribution is invalid, "
                "please delete and re-add UPCs."
            ),
        "ad group attribute key value not found in client attribute list":
            (
                "One or more of the products associated with the commodity is invalid. "
                "Please contact Support for assistance."
            ),
        "amount cannot be zero if use base bid is false":
            (
                "If the default bid for a UPC or sub-commodity is not selected, "
                "please set the specific bid amount."
            ),
        "invalidbidder":
            (
                "One or more of the UPCs or sub-commodities selected is invalid or not available, "
                "please adjust your selection."
            ),
        # Adding in case of a typo
        "invalid bidder":
            (
                "One or more of the UPCs or sub-commodities selected is invalid or not available, "
                "please adjust your selection."
            ),
        "operation IN should be for a nonempty list":
            "Please select at least one UPC or sub-commodity.",
        "bidders must belong to advertiser":
            "One or more bidders selected is invalid. Please contact Support for assistance.",
        "Invalid bidder":
            (
                "Update successful, but one or more of the selected bidders was invalid. "
                "Please contact Support for assistance."
            ),
    }

    # If the error message is not in the error_map, it will return the original message.
    @classmethod
    def remap(cls, original_message):
        if isinstance(original_message, str):
            return cls.error_map.get(original_message, original_message)
        if isinstance(original_message, list):
            return [cls.error_map.get(msg, msg) for msg in original_message]
        raise TypeError("Cannot remap message of type: {type(original_message)}")
