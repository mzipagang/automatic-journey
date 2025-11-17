import secrets
from enum import StrEnum
from unittest import TestCase
from unittest.mock import patch

from app.common.model.campaign_types import (
    CampaignType,
    InternalCampaignType,
    BidManagerCampaignType,
    CASCampaignType,
    KoddiReportExperienceType,
    ignore_case_with_unsupported_fallback,
    convert_enum,
    parse_campaign_type,
    serialize_campaign_type
)
from app.common.model.shared import IgnoreCaseStrEnum


class TestCampaignTypes(TestCase):
    @staticmethod
    def __random_casing(value: str) -> str:
        def random_case(char: str) -> str:
            is_caps = secrets.choice([True, False])
            return char.upper() if is_caps else char.lower()

        return "".join(map(random_case, value))

    def __ignore_case_enum_check(
            self,
            cls,
            pla: str,
            toa: str,
            carousel: str
    ):
        if not issubclass(cls, IgnoreCaseStrEnum):
            self.fail(f"{cls.__name__} does not extend IgnoreCaseStrEnum")

        keys = cls.__members__.keys()

        self.assertIn("PLA", keys)
        self.assertIn("TOA", keys)
        self.assertIn("CAROUSEL", keys)

        pla_enum = cls(self.__random_casing(pla))
        toa_enum = cls(self.__random_casing(toa))
        carousel_enum = cls(self.__random_casing(carousel))
        invalid_key = self.__random_casing("invalid")

        with self.assertRaises(ValueError) as invalid_error:
            cls(invalid_key)

        self.assertEqual(cls.PLA, pla_enum)
        self.assertEqual(cls.TOA, toa_enum)
        self.assertEqual(cls.CAROUSEL, carousel_enum)
        self.assertIsNotNone(invalid_error)
        self.assertEqual(
            f"'{invalid_key}' is not a valid {cls.__name__}",
            invalid_error.exception.args[0]
        )

    def __ignore_case_with_fallback_enum_check(
            self,
            cls,
            pla: str,
            toa: str,
            carousel: str
    ):
        if not issubclass(cls, StrEnum):
            self.fail(f"{cls.__name__} does not extend StrEnum")

        keys = cls.__members__.keys()

        self.assertIn("PLA", keys)
        self.assertIn("TOA", keys)
        self.assertIn("CAROUSEL", keys)
        self.assertIn("UNSUPPORTED", keys)

        pla_enum = cls(self.__random_casing(pla))
        toa_enum = cls(self.__random_casing(toa))
        carousel_enum = cls(self.__random_casing(carousel))
        unsupported_enum = cls(self.__random_casing("invalid"))

        self.assertEqual(cls.PLA, pla_enum)
        self.assertEqual(cls.TOA, toa_enum)
        self.assertEqual(cls.CAROUSEL, carousel_enum)
        self.assertEqual(cls.UNSUPPORTED, unsupported_enum)

    def test_campaign_type(self):
        self.__ignore_case_enum_check(
            CampaignType,
            "pla",
            "toa",
            "carousel"
        )

    def test_internal_campaign_type(self):
        self.__ignore_case_with_fallback_enum_check(
            InternalCampaignType,
            "pla",
            "toa",
            "carousel"
        )

    def test_bid_manager_campaign_type(self):
        self.__ignore_case_with_fallback_enum_check(
            BidManagerCampaignType,
            "pla",
            "toa",
            "ppc"
        )

    def test_cas_campaign_type(self):
        self.__ignore_case_with_fallback_enum_check(
            CASCampaignType,
            "pla",
            "toa",
            "promoted_products_carousel"
        )

    def test_koddi_report_experience_type(self):
        self.__ignore_case_enum_check(
            KoddiReportExperienceType,
            "pla",
            "toa",
            "carousel"
        )

    def test_ignore_case_with_unsupported_fallback(self):
        class TestEnum(StrEnum):
            OK = "ok"
            UNSUPPORTED = "UNSUPPORTED"
        class IncorrectEnum(StrEnum):
            OK = "ok"
        class InvalidClass:
            pass

        ok_enum = ignore_case_with_unsupported_fallback(
            TestEnum,
            self.__random_casing("ok")
        )
        unsupported_enum = ignore_case_with_unsupported_fallback(
            TestEnum,
            "invalid"
        )

        with self.assertRaises(TypeError) as invalid_subclass_error:
            ignore_case_with_unsupported_fallback(InvalidClass,"")

        with self.assertRaises(TypeError) as invalid_enum_error:
            ignore_case_with_unsupported_fallback(IncorrectEnum,"")

        self.assertEqual(TestEnum.OK, ok_enum)
        self.assertEqual(TestEnum.UNSUPPORTED, unsupported_enum)
        self.assertIsNotNone(invalid_subclass_error)
        self.assertEqual(
            f"{InvalidClass.__name__} must be a subclass of StrEnum",
            invalid_subclass_error.exception.args[0]
        )
        self.assertIsNotNone(invalid_enum_error)
        self.assertEqual(
            f"{IncorrectEnum.__name__} must have UNSUPPORTED key",
            invalid_enum_error.exception.args[0]
        )

    def test_convert_enum(self):
        self.assertEqual(
            BidManagerCampaignType.CAROUSEL,
            convert_enum(
                InternalCampaignType.CAROUSEL,
                BidManagerCampaignType
            )
        )
        self.assertIsNone(
            convert_enum(
                InternalCampaignType.UNSUPPORTED,
                CampaignType
            )
        )

    def test_parse_campaign_type(self):
        # Handles none type
        self.assertIsNone(parse_campaign_type(None, CASCampaignType))
        # Handles other enum types
        self.assertEqual(
            InternalCampaignType.CAROUSEL,
            parse_campaign_type(CASCampaignType.CAROUSEL, CASCampaignType)
        )
        self.assertEqual(
            InternalCampaignType.PLA,
            parse_campaign_type(InternalCampaignType.PLA, CASCampaignType)
        )

        # Handles strings
        self.assertEqual(
            InternalCampaignType.PLA,
            parse_campaign_type("pla", CASCampaignType)
        )
        self.assertEqual(
            InternalCampaignType.TOA,
            parse_campaign_type("toa", CASCampaignType)
        )
        self.assertEqual(
            InternalCampaignType.CAROUSEL,
            parse_campaign_type("Promoted_Products_Carousel", CASCampaignType)
        )
        self.assertEqual(
            InternalCampaignType.UNSUPPORTED,
            parse_campaign_type("invalid", CASCampaignType)
        )

        # Anything else is unsupported
        self.assertEqual(
            InternalCampaignType.UNSUPPORTED,
            parse_campaign_type(42, CASCampaignType)
        )

    @patch('logging.Logger.warning')
    def test_parse_campaign_type__logs_unsupported_types(
            self,
            mock_log_warning
    ):
        parse_campaign_type("PREMIUM_PLACEMENTS", CASCampaignType)

        mock_log_warning.assert_called_once_with(
            "Unsupported campaign type PREMIUM_PLACEMENTS is not a supported CASCampaignType.",
            extra = {
                "campaign_type": "PREMIUM_PLACEMENTS",
                "target_type": "CASCampaignType"
            }
        )

    def test_serialize_campaign_type(self):
        self.assertIsNone(serialize_campaign_type(None, CASCampaignType))
        self.assertEqual(
            CASCampaignType.PLA,
            serialize_campaign_type(InternalCampaignType.PLA, CASCampaignType)
        )
        self.assertEqual(
            CASCampaignType.TOA,
            serialize_campaign_type(InternalCampaignType.TOA, CASCampaignType)
        )
        self.assertEqual(
            CASCampaignType.CAROUSEL,
            serialize_campaign_type(InternalCampaignType.CAROUSEL, CASCampaignType)
        )