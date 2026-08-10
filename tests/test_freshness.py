import unittest
from datetime import UTC, datetime

from signalbudget.freshness import pricing_freshness, pricing_provenance_lines


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

    def test_pricing_profile_is_stale_after_exact_max_age_duration(self) -> None:
        result = pricing_freshness(
            {"retrieved_at": "2026-01-01T00:00:00Z", "max_age_days": 90},
            as_of=datetime(2026, 4, 1, 23, 59, tzinfo=UTC),
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

    def test_reverification_resets_the_staleness_clock(self) -> None:
        profile = {
            "retrieved_at": "2026-07-23T00:00:00Z",
            "verified_at": "2026-08-10T00:00:00Z",
            "max_age_days": 90,
        }

        # 2026-10-25 is past 90 days from retrieval but not from verification.
        result = pricing_freshness(profile, as_of=datetime(2026, 10, 25, tzinfo=UTC))

        self.assertTrue(result["fresh"])
        self.assertEqual(result["status"], "PRICING_FRESH")
        self.assertEqual(result["freshness_basis"], "verified_at")
        self.assertEqual(result["age_days"], 76)

    def test_verification_only_defers_staleness_by_its_own_max_age(self) -> None:
        profile = {
            "retrieved_at": "2026-07-23T00:00:00Z",
            "verified_at": "2026-08-10T00:00:00Z",
            "max_age_days": 90,
        }

        result = pricing_freshness(profile, as_of=datetime(2026, 11, 20, tzinfo=UTC))

        self.assertFalse(result["fresh"])
        self.assertEqual(result["reason"], "PRICING_OLDER_THAN_MAX_AGE")

    def test_freshness_falls_back_to_retrieval_without_verification(self) -> None:
        result = pricing_freshness(
            {"retrieved_at": "2026-07-23T00:00:00Z", "max_age_days": 90},
            as_of=datetime(2026, 10, 25, tzinfo=UTC),
        )

        self.assertFalse(result["fresh"])
        self.assertEqual(result["freshness_basis"], "retrieved_at")
        self.assertIsNone(result["verified_at"])

    def test_verification_older_than_retrieval_does_not_age_the_profile(self) -> None:
        result = pricing_freshness(
            {
                "retrieved_at": "2026-08-10T00:00:00Z",
                "verified_at": "2026-01-01T00:00:00Z",
                "max_age_days": 90,
            },
            as_of=datetime(2026, 8, 20, tzinfo=UTC),
        )

        self.assertTrue(result["fresh"])
        self.assertEqual(result["freshness_basis"], "retrieved_at")

    def test_provenance_lines_report_the_profile_dates(self) -> None:
        freshness = pricing_freshness(
            {"retrieved_at": "2026-07-21T00:00:00Z", "max_age_days": 90},
            as_of=datetime(2026, 7, 21, tzinfo=UTC),
        )

        lines = pricing_provenance_lines(freshness)

        self.assertIn("2026-07-21T00:00:00Z", lines[0])
        self.assertIn("90", lines[0])

    def test_provenance_lines_do_not_drift_with_the_calendar(self) -> None:
        profile = {
            "retrieved_at": "2026-07-21T00:00:00Z",
            "verified_at": "2026-08-10T00:00:00Z",
            "max_age_days": 90,
        }
        fresh = pricing_freshness(profile, as_of=datetime(2026, 8, 10, tzinfo=UTC))
        stale = pricing_freshness(profile, as_of=datetime(2027, 1, 1, tzinfo=UTC))

        self.assertNotEqual(fresh["age_days"], stale["age_days"])
        self.assertEqual(
            pricing_provenance_lines(fresh),
            pricing_provenance_lines(stale),
        )

    def test_provenance_lines_report_the_verification_date(self) -> None:
        freshness = pricing_freshness(
            {
                "retrieved_at": "2026-07-23T00:00:00Z",
                "verified_at": "2026-08-10T00:00:00Z",
                "max_age_days": 90,
            },
            as_of=datetime(2026, 8, 10, tzinfo=UTC),
        )

        lines = pricing_provenance_lines(freshness)

        self.assertIn("2026-08-10T00:00:00Z", lines[1])
        self.assertIn("verified_at", lines[1])

    def test_provenance_omits_verification_line_when_absent(self) -> None:
        freshness = pricing_freshness(
            {"retrieved_at": "2026-07-23T00:00:00Z", "max_age_days": 90},
            as_of=datetime(2026, 8, 10, tzinfo=UTC),
        )

        self.assertNotIn(
            "Last verified", "\n".join(pricing_provenance_lines(freshness))
        )


if __name__ == "__main__":
    unittest.main()
