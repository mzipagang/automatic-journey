import unittest
from copy import deepcopy
from unittest import TestCase

from app.common.model.campaign_types import InternalCampaignType, BidManagerCampaignType
from app.common.model.downstream.bid_manager import BidsResponseData, CreateBidsRequest


class TestBidManager(TestCase):
    def test_bids_response_data__validates_incoming_type(self):
        bids_response_params = {
            "id": "1234",
            "bids": [],
            "default_bid": 0
        }
        pla_bids_response = BidsResponseData(
            **bids_response_params,
            type="PLA",
        )
        toa_bids_response = BidsResponseData(
            **bids_response_params,
            type="TOA",
        )
        carousel_bids_response = BidsResponseData(
            **bids_response_params,
            type="PPC",
        )
        invalid_bids_response = BidsResponseData(
            **bids_response_params,
            type="INVALID",
        )

        self.assertEqual(InternalCampaignType.PLA, pla_bids_response.type)
        self.assertEqual(InternalCampaignType.TOA, toa_bids_response.type)
        self.assertEqual(InternalCampaignType.CAROUSEL, carousel_bids_response.type)
        self.assertEqual(InternalCampaignType.UNSUPPORTED, invalid_bids_response.type)

    def test_create_bids_request__serializes_outgoing_type(self):
        create_bids_params = {
            "bids": [],
            "default_bid": 0
        }
        pla_bids = CreateBidsRequest(
            **create_bids_params,
            type=InternalCampaignType.PLA,
        ).model_dump()
        toa_bids = CreateBidsRequest(
            **create_bids_params,
            type=InternalCampaignType.TOA,
        ).model_dump()
        carousel_bids = CreateBidsRequest(
            **create_bids_params,
            type=InternalCampaignType.CAROUSEL,
        ).model_dump()
        invalid_bids = CreateBidsRequest(
            **create_bids_params,
            type=InternalCampaignType.UNSUPPORTED,
        ).model_dump()

        self.assertEqual(BidManagerCampaignType.PLA, pla_bids.get("type"))
        self.assertEqual(BidManagerCampaignType.TOA, toa_bids.get("type"))
        self.assertEqual(BidManagerCampaignType.CAROUSEL, carousel_bids.get("type"))
        self.assertEqual(BidManagerCampaignType.UNSUPPORTED, invalid_bids.get("type"))