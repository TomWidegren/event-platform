
"""
Tests for calculating Floorball Discovery registry changes.

The function compares an existing registry with a newly
discovered registry and returns only source-owned changes.

No API requests, file writes, Git operations or notifications.
"""

import copy
import unittest

from floorball_discovery_changes import calculate_discovery_changes


class TestFloorballDiscoveryChanges(unittest.TestCase):

    def setUp(self):
        self.original = {
            "schema_version": 1,
            "matches": {
                "1750707": {
                    "match_id": 1750707,
                    "competition_id": 45004,
                    "team_id": 20872,
                    "highlight_player_id": 585280,
                    "home_team": "Tyresö Trollbäcken IBK",
                    "away_team": "FBI Tullinge",
                    "scheduled_start": "2026-10-23T19:45:00",
                    "source_status": 1,
                    "cancelled": False,
                    "postponed": False,
                    "monitoring_status": "scheduled",
                }
            },
        }

    def test_no_changes_returns_empty(self):
        updated = copy.deepcopy(self.original)

        result = calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertEqual(result, {})

    def test_schedule_change_only(self):
        updated = copy.deepcopy(self.original)

        updated["matches"]["1750707"][
            "scheduled_start"
        ] = "2026-10-23T20:15:00"

        result = calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertEqual(
            result,
            {
                "1750707": {
                    "scheduled_start": "2026-10-23T20:15:00"
                }
            },
        )

    def test_new_match_includes_required_fields(self):
        updated = copy.deepcopy(self.original)

        updated["matches"]["1703577"] = {
            "match_id": 1703577,
            "competition_id": 44356,
            "team_id": 4194,
            "highlight_player_id": 585280,
            "home_team": "Tyresö Trollbäcken IBK (A)",
            "away_team": "Älta IF A",
            "scheduled_start": "2026-10-25T15:45:00",
            "source_status": 1,
            "cancelled": False,
            "postponed": False,
            "monitoring_status": "scheduled",
        }

        result = calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertIn("1703577", result)

        new_match = result["1703577"]

        self.assertEqual(new_match["match_id"], 1703577)
        self.assertEqual(new_match["competition_id"], 44356)
        self.assertEqual(new_match["team_id"], 4194)
        self.assertEqual(
            new_match["scheduled_start"],
            "2026-10-25T15:45:00",
        )

        self.assertNotIn(
            "monitoring_status",
            new_match,
        )

    def test_completed_status_not_included(self):
        updated = copy.deepcopy(self.original)

        updated["matches"]["1750707"][
            "monitoring_status"
        ] = "completed"

        result = calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertEqual(result, {})

    def test_schedule_change_preserves_completed(self):
        original = copy.deepcopy(self.original)

        original["matches"]["1750707"][
            "monitoring_status"
        ] = "completed"

        updated = copy.deepcopy(original)

        updated["matches"]["1750707"][
            "scheduled_start"
        ] = "2026-10-23T20:15:00"

        result = calculate_discovery_changes(
            original,
            updated,
        )

        self.assertEqual(
            result,
            {
                "1750707": {
                    "scheduled_start": "2026-10-23T20:15:00"
                }
            },
        )

    def test_multiple_field_changes(self):
        updated = copy.deepcopy(self.original)

        match = updated["matches"]["1750707"]

        match["scheduled_start"] = "2026-10-23T20:15:00"
        match["source_status"] = 2
        match["home_team"] = "Updated Home Team"

        result = calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertEqual(
            result["1750707"],
            {
                "scheduled_start": "2026-10-23T20:15:00",
                "source_status": 2,
                "home_team": "Updated Home Team",
            },
        )

    def test_missing_match_not_deleted(self):
        updated = copy.deepcopy(self.original)
        updated["matches"] = {}

        result = calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertEqual(result, {})

    def test_original_inputs_not_modified(self):
        original_copy = copy.deepcopy(self.original)
        updated = copy.deepcopy(self.original)
        updated_copy = copy.deepcopy(updated)

        calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertEqual(self.original, original_copy)
        self.assertEqual(updated, updated_copy)

    def test_unknown_fields_ignored(self):
        updated = copy.deepcopy(self.original)

        updated["matches"]["1750707"][
            "internal_note"
        ] = "Do not persist"

        result = calculate_discovery_changes(
            self.original,
            updated,
        )

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
