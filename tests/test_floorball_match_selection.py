
"""
Tests for automatic floorball match selection.

Defines expected behavior for selecting matches eligible
for Live monitoring.

All tests use in-memory data and simulated timestamps.

No API calls, file writes, Git operations or notifications.
"""

import copy
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from floorball_match_selection import select_active_matches


STOCKHOLM = ZoneInfo("Europe/Stockholm")


class TestFloorballMatchSelection(unittest.TestCase):

    def setUp(self):
        self.registry = {
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

    def at(self, year, month, day, hour, minute):
        return datetime(
            year, month, day, hour, minute,
            tzinfo=STOCKHOLM,
        )

    def selected_ids(self, now, registry=None):
        watches = select_active_matches(
            registry or self.registry,
            now=now,
        )
        return {watch["id"] for watch in watches}

    def test_not_selected_before_activation_window(self):
        ids = self.selected_ids(
            self.at(2026, 10, 23, 19, 29)
        )
        self.assertNotIn("floorball-match-1750707", ids)

    def test_selected_exactly_fifteen_minutes_before(self):
        ids = self.selected_ids(
            self.at(2026, 10, 23, 19, 30)
        )
        self.assertIn("floorball-match-1750707", ids)

    def test_selected_at_match_start(self):
        ids = self.selected_ids(
            self.at(2026, 10, 23, 19, 45)
        )
        self.assertIn("floorball-match-1750707", ids)

    def test_delayed_match_remains_eligible(self):
        ids = self.selected_ids(
            self.at(2026, 10, 23, 23, 15)
        )
        self.assertIn("floorball-match-1750707", ids)

    def test_completed_match_excluded(self):
        registry = copy.deepcopy(self.registry)
        registry["matches"]["1750707"][
            "monitoring_status"
        ] = "completed"

        ids = self.selected_ids(
            self.at(2026, 10, 23, 19, 45),
            registry,
        )
        self.assertNotIn("floorball-match-1750707", ids)

    def test_cancelled_match_excluded(self):
        registry = copy.deepcopy(self.registry)
        registry["matches"]["1750707"]["cancelled"] = True

        ids = self.selected_ids(
            self.at(2026, 10, 23, 19, 45),
            registry,
        )
        self.assertNotIn("floorball-match-1750707", ids)

    def test_postponed_match_excluded(self):
        registry = copy.deepcopy(self.registry)
        registry["matches"]["1750707"]["postponed"] = True

        ids = self.selected_ids(
            self.at(2026, 10, 23, 19, 45),
            registry,
        )
        self.assertNotIn("floorball-match-1750707", ids)

    def test_multiple_matches_selected(self):
        registry = copy.deepcopy(self.registry)
        registry["matches"]["1703577"][
            "scheduled_start"
        ] = "2026-10-23T19:45:00"

        ids = self.selected_ids(
            self.at(2026, 10, 23, 19, 45),
            registry,
        )

        self.assertEqual(
            ids,
            {
                "floorball-match-1750707",
                "floorball-match-1703577",
            },
        )

    def test_runtime_watch_structure(self):
        watches = select_active_matches(
            self.registry,
            now=self.at(2026, 10, 23, 19, 30),
        )

        watch = next(
            w for w in watches
            if w["id"] == "floorball-match-1750707"
        )

        self.assertEqual(watch["connector"], "ibis_floorball")
        self.assertEqual(watch["mode"], "live")
        self.assertEqual(watch["source"]["match_id"], 1750707)
        self.assertEqual(watch["source"]["team_id"], 20872)
        self.assertEqual(
            watch["source"]["highlight_player_id"],
            585280,
        )

    def test_no_matches_selected_between_events(self):
        ids = self.selected_ids(
            self.at(2026, 10, 22, 12, 0)
        )
        self.assertEqual(ids, set())

    def test_original_registry_not_modified(self):
        original = copy.deepcopy(self.registry)

        select_active_matches(
            self.registry,
            now=self.at(2026, 10, 23, 19, 45),
        )

        self.assertEqual(self.registry, original)

    def test_winter_time_handled(self):
        registry = copy.deepcopy(self.registry)
        registry["matches"]["1750707"][
            "scheduled_start"
        ] = "2026-11-06T19:45:00"

        ids = self.selected_ids(
            self.at(2026, 11, 6, 19, 30),
            registry,
        )

        self.assertIn("floorball-match-1750707", ids)


if __name__ == "__main__":
    unittest.main()
