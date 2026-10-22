
"""
End-to-end tests for Event Platform automatic Live preparation.

Verifies integration between:
- floorball_live.py
- floorball_match_selection.py
- floorball_watch_merge.py
- watcher.py

All external data acquisition and notifications are mocked.
Monitoring state is stored in a temporary directory.

No production files, external APIs or Git operations are used.
"""

import copy
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import watcher
from floorball_live import load_live_config


STOCKHOLM = ZoneInfo("Europe/Stockholm")


class TestFloorballLiveEntry(unittest.TestCase):

    MATCH_ID = 1750707
    WATCH_ID = "floorball-match-1750707"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        root = Path(self.temp.name)

        self.registry_path = root / "match_registry.json"
        self.state_path = root / "state.json"

        self.config = {
            "ntfy": {"topic": "test-only"},
            "watches": [
                {
                    "id": "lukas-sgf-ranking",
                    "name": "SGF Ranking",
                    "connector": "sgf_ranking",
                    "mode": "daily",
                },
                {
                    "id": "lukas-golfbox",
                    "name": "GolfBox",
                    "connector": "golfbox_leaderboard",
                    "mode": "live",
                },
                {
                    "id": "lukas-tournytt",
                    "name": "Tournytt",
                    "connector": "tournytt_api",
                    "mode": "live",
                },
                {
                    "id": "floorball-match-1750693",
                    "name": "Previous floorball match",
                    "connector": "ibis_floorball",
                    "mode": "live",
                },
            ],
        }

        self.registry = {
            "schema_version": 1,
            "matches": {
                str(self.MATCH_ID): {
                    "match_id": self.MATCH_ID,
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

        self.registry_path.write_text(
            json.dumps(self.registry, ensure_ascii=False),
            encoding="utf-8",
        )

        self.baseline = {
            "match_id": self.MATCH_ID,
            "competition": "Juniorallsvenskan D HJ18",
            "home_team": "Tyresö Trollbäcken IBK",
            "away_team": "FBI Tullinge",
            "home_team_id": 20872,
            "away_team_id": 99999,
            "home_match_team_id": 111,
            "away_match_team_id": 222,
            "match_datetime": "2026-10-23T19:45:00",
            "match_status": 1,
            "has_final_result": False,
            "home_goals": 0,
            "away_goals": 0,
            "events": [],
        }

        self.activation_time = datetime(
            2026, 10, 23, 19, 30,
            tzinfo=STOCKHOLM,
        )

    def prepare(self, now=None):
        return load_live_config(
            self.config,
            registry_path=self.registry_path,
            now=now or self.activation_time,
        )

    def run_monitor(self, snapshot):
        runtime_config = self.prepare()
        notifications = Mock()

        def fake_fetcher(connector_name):
            if connector_name == "ibis_floorball":
                return lambda watch: copy.deepcopy(snapshot)

            return lambda watch: None

        with (
            patch.object(
                watcher,
                "STATE_FILE",
                self.state_path,
            ),
            patch.object(
                watcher,
                "get_fetcher",
                side_effect=fake_fetcher,
            ),
            patch.object(
                watcher,
                "send_ntfy",
                notifications,
            ),
            patch.dict(
                os.environ,
                {
                    "RUN_MODE": "live",
                    "WATCH_ID": "",
                },
            ),
        ):
            watcher.main(config=runtime_config)

        return notifications

    def read_state(self):
        return json.loads(
            self.state_path.read_text(encoding="utf-8")
        )

    def test_runtime_config_preserves_golf(self):
        config = self.prepare()

        ids = {watch["id"] for watch in config["watches"]}

        self.assertIn("lukas-golfbox", ids)
        self.assertIn("lukas-tournytt", ids)
        self.assertIn(self.WATCH_ID, ids)

        self.assertNotIn("lukas-sgf-ranking", ids)
        self.assertNotIn("floorball-match-1750693", ids)

    def test_before_activation_no_floorball(self):
        early = datetime(
            2026, 10, 23, 19, 29,
            tzinfo=STOCKHOLM,
        )

        config = self.prepare(now=early)

        ids = {watch["id"] for watch in config["watches"]}

        self.assertNotIn(self.WATCH_ID, ids)
        self.assertIn("lukas-golfbox", ids)

    def test_first_observation_creates_baseline(self):
        notifications = self.run_monitor(self.baseline)

        self.assertEqual(notifications.call_count, 0)

        state = self.read_state()

        self.assertIn(self.WATCH_ID, state)
        self.assertEqual(
            state[self.WATCH_ID]["fields"]["match_id"],
            self.MATCH_ID,
        )

    def test_goal_generates_one_notification(self):
        self.run_monitor(self.baseline)

        updated = copy.deepcopy(self.baseline)
        updated["match_status"] = 2
        updated["home_goals"] = 1

        updated["events"] = [{
            "event_id": 900001,
            "type": "Mål",
            "type_id": 1,
            "match_team_id": 111,
            "period": 1,
            "minute": 5,
            "second": 20,
            "home_goals": 1,
            "away_goals": 0,
            "player_id": 585280,
            "player_name": "Lukas Widegren",
            "assist_id": None,
            "assist_name": None,
            "penalty_name": None,
        }]

        notifications = self.run_monitor(updated)

        self.assertEqual(notifications.call_count, 1)

        message = notifications.call_args.args[2]

        self.assertIn("Lukas Widegren", message)
        self.assertIn("⭐", message)

        repeated = self.run_monitor(updated)

        self.assertEqual(repeated.call_count, 0)

    def test_final_result_is_saved(self):
        self.run_monitor(self.baseline)

        final = copy.deepcopy(self.baseline)
        final["match_status"] = 4
        final["has_final_result"] = True
        final["home_goals"] = 5
        final["away_goals"] = 4

        notifications = self.run_monitor(final)

        self.assertEqual(notifications.call_count, 1)

        message = notifications.call_args.args[2]

        self.assertIn("SLUTRESULTAT: 5 - 4", message)

        state = self.read_state()

        self.assertTrue(
            state[self.WATCH_ID]["fields"]["has_final_result"]
        )

    def test_existing_golf_state_preserved(self):
        existing = {
            "lukas-sgf-ranking": {
                "snapshot": "existing-ranking",
                "fields": {"position": "120"},
            }
        }

        self.state_path.write_text(
            json.dumps(existing),
            encoding="utf-8",
        )

        self.run_monitor(self.baseline)

        state = self.read_state()

        self.assertEqual(
            state["lukas-sgf-ranking"],
            existing["lukas-sgf-ranking"],
        )

    def test_completed_match_is_excluded(self):
        completed = copy.deepcopy(self.registry)

        completed["matches"][str(self.MATCH_ID)][
            "monitoring_status"
        ] = "completed"

        self.registry_path.write_text(
            json.dumps(completed),
            encoding="utf-8",
        )

        config = self.prepare()

        ids = {watch["id"] for watch in config["watches"]}

        self.assertNotIn(self.WATCH_ID, ids)

    def test_configuration_and_registry_unchanged(self):
        original_config = copy.deepcopy(self.config)
        original_registry = copy.deepcopy(self.registry)

        self.prepare()

        self.assertEqual(self.config, original_config)

        saved_registry = json.loads(
            self.registry_path.read_text(encoding="utf-8")
        )

        self.assertEqual(saved_registry, original_registry)


if __name__ == "__main__":
    unittest.main()
