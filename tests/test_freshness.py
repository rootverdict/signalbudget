import unittest
from datetime import UTC, datetime

from signalbudget.freshness import pricing_freshness


class FreshnessTests(unittest.TestCase):
    def test_pricing_profile_is_current_within_max_age(self) -> None:
        result = pricing_freshness(
            {"retrieved_at": "2026-07-21T00:00:00Z", "max_age_days": 90},
            as_of=datetime(2026, 7, 21, tzinfo=UTC),
        )

        self.assertTrue(result["fresh"])
        self.assertEqual(result["status"], "PRICING_FRESH")

    def test_pricing_profile_goes_stale_after_max_age(self) -> None:
        result = pricing_freshness(
            {"retrieved_at": "2026-07-21T00:00:00Z", "max_age_days": 90},
            as_of=datetime(2026, 11, 1, tzinfo=UTC),
        )

        self.assertFalse(result["fresh"])
        self.assertEqual(result["status"], "PRICING_STALE")

    def test_pricing_profile_with_future_retrieval_date_is_stale(self) -> None:
        result = pricing_freshness(
            {"retrieved_at": "2026-07-22T00:00:00Z", "max_age_days": 90},
            as_of=datetime(2026, 7, 21, tzinfo=UTC),
        )

        self.assertFalse(result["fresh"])
        self.assertEqual(result["status"], "PRICING_STALE")
        self.assertEqual(result["reason"], "PRICING_RETRIEVED_IN_FUTURE")


if __name__ == "__main__":
    unittest.main()
