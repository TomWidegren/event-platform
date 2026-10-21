
"""
Tests for safe Floorball match registry merging.

These tests define how independent Discovery and Live updates
must be combined without losing information.

The tests use only in-memory data.

No external APIs, GitHub writes, state.json changes or
notifications are involved.
"""

import copy
import unittest

from floorball_registry_merge import merge_registry_changes


class TestFloorballRegistryMerge(unittest.TestCase):

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
                },
                "1703577": {
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
                },
            },
        }

    def test_discovery_schedule_change(self):
        """
        Discovery may update scheduling information without
        modifying monitoring lifecycle.
        """
        changes = {
            "1750707": {
                "scheduled_start": "2026-10-23T20:15:00",
            }
        }

        result = merge_registry_changes(
            self.original,
            changes,
            owner="discovery",
        )

        match = result["matches"]["1750707"]

        self.assertEqual(
            match["scheduled_start"],
            "2026-10-23T20:15:00",
        )
        self.assertEqual(
            match["monitoring_status"],
            "scheduled",
        )

    def test_live_completion(self):
        """
        Live may update monitoring lifecycle without
        modifying scheduling information.
        """
        changes = {
            "1750707": {
                "monitoring_status": "completed",
            }
        }

        result = merge_registry_changes(
            self.original,
            changes,
            owner="live",
        )

        match = result["matches"]["1750707"]

        self.assertEqual(
            match["monitoring_status"],
            "completed",
        )
        self.assertEqual(
            match["scheduled_start"],
            "2026-10-23T19:45:00",
        )

    def test_same_match_changes_are_preserved(self):
        """
        Discovery and Live may start from the same original
        registry but must not overwrite each other's changes.
        """
        discovery_changes = {
            "1750707": {
                "scheduled_start": "2026-10-23T20:15:00",
            }
        }

        live_changes = {
            "1750707": {
                "monitoring_status": "completed",
            }
        }

        after_discovery = merge_registry_changes(
            self.original,
            discovery_changes,
            owner="discovery",
        )

        final = merge_registry_changes(
            after_discovery,
            live_changes,
            owner="live",
        )

        match = final["matches"]["1750707"]

        self.assertEqual(
            match["scheduled_start"],
            "2026-10-23T20:15:00",
        )
        self.assertEqual(
            match["monitoring_status"],
            "completed",
        )

    def test_reverse_merge_order(self):
        """
        Both changes must survive when Live is merged first
        and Discovery second.
        """
        live_changes = {
            "1750707": {
                "monitoring_status": "completed",
            }
        }

        discovery_changes = {
            "1750707": {
                "scheduled_start": "2026-10-23T20:15:00",
            }
        }

        after_live = merge_registry_changes(
            self.original,
            live_changes,
            owner="live",
        )

        final = merge_registry_changes(
            after_live,
            discovery_changes,
            owner="discovery",
        )

        match = final["matches"]["1750707"]

        self.assertEqual(
            match["scheduled_start"],
            "2026-10-23T20:15:00",
        )
        self.assertEqual(
            match["monitoring_status"],
            "completed",
        )

    def test_different_matches_are_preserved(self):
        """
        Updates to different matches must not interfere.
        """
        discovery_changes = {
            "1750707": {
                "scheduled_start": "2026-10-23T20:15:00",
            }
        }

        live_changes = {
            "1703577": {
                "monitoring_status": "completed",
            }
        }

        result = merge_registry_changes(
            self.original,
            discovery_changes,
            owner="discovery",
        )

        result = merge_registry_changes(
            result,
            live_changes,
            owner="live",
        )

        self.assertEqual(
            result["matches"]["1750707"]["scheduled_start"],
            "2026-10-23T20:15:00",
        )
        self.assertEqual(
            result["matches"]["1703577"]["monitoring_status"],
            "completed",
        )

    def test_discovery_cannot_reset_completed(self):
        """
        Discovery must never reactivate a completed match.
        """
        registry = copy.deepcopy(self.original)

        registry["matches"]["1750707"][
            "monitoring_status"
        ] = "completed"

        changes = {
            "1750707": {
                "monitoring_status": "scheduled",
            }
        }

        with self.assertRaises(ValueError):
            merge_registry_changes(
                registry,
                changes,
                owner="discovery",
            )

        self.assertEqual(
            registry["matches"]["1750707"][
                "monitoring_status"
            ],
            "completed",
        )

    def test_live_cannot_change_schedule(self):
        """
        Live must not modify fields owned by Discovery.
        """
        changes = {
            "1750707": {
                "scheduled_start": "2026-10-23T21:00:00",
            }
        }

        with self.assertRaises(ValueError):
            merge_registry_changes(
                self.original,
                changes,
                owner="live",
            )

    def test_unrelated_matches_are_preserved(self):
        """
        Updating one match must preserve all other matches.
        """
        changes = {
            "1750707": {
                "scheduled_start": "2026-10-23T20:15:00",
            }
        }

        result = merge_registry_changes(
            self.original,
            changes,
            owner="discovery",
        )

        self.assertEqual(
            result["matches"]["1703577"],
            self.original["matches"]["1703577"],
        )

    def test_original_registry_not_modified(self):
        """
        The merge function must never mutate its inputs.
        """
        original_copy = copy.deepcopy(self.original)

        changes = {
            "1750707": {
                "scheduled_start": "2026-10-23T20:15:00",
            }
        }
        changes_copy = copy.deepcopy(changes)

        merge_registry_changes(
            self.original,
            changes,
            owner="discovery",
        )

        self.assertEqual(self.original, original_copy)
        self.assertEqual(changes, changes_copy)

    def test_invalid_owner_rejected(self):
        """
        Unknown processes must not update the registry.
        """
        with self.assertRaises(ValueError):
            merge_registry_changes(
                self.original,
                {
                    "1750707": {
                        "scheduled_start": "2026-10-23T20:15:00",
                    }
                },
                owner="unknown",
            )

    def test_unknown_match_rejected(self):
        """
        Live must not create a match implicitly.
        """
        with self.assertRaises((KeyError, ValueError)):
            merge_registry_changes(
                self.original,
                {
                    "9999999": {
                        "monitoring_status": "completed",
                    }
                },
                owner="live",
            )

    def test_invalid_status_rejected(self):
        """
        Live may only use supported monitoring statuses.
        """
        with self.assertRaises(ValueError):
            merge_registry_changes(
                self.original,
                {
                    "1750707": {
                        "monitoring_status": "unknown",
                    }
                },
                owner="live",
            )


if __name__ == "__main__":
    unittest.main()
