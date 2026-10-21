
"""
Isolated integration tests for automatic floorball Live monitoring.

Verifies:
- Runtime Watch selection from the match registry.
- Integration with the existing Event Platform watcher.
- Initial baseline without notifications.
- Change detection and notification formatting.
- No repeated notifications for unchanged observations.
- Final-result notification and state persistence.

All match data is simulated.

No real iBIS API calls, ntfy notifications, Git operations
or production state changes are performed.
"""

import copy
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import watcher
from floorball_match_selection import select_active_matches


STOCKHOLM = ZoneInfo("Europe/Stockholm")


class TestFloorballLiveIntegration(unittest.TestCase):

    MATCH_ID = 1750707
    WATCH_ID = "floorball-match-1750707"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.state_file = Path(self.temp.name) / "state.json"

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

        self.now = datetime(
            2026, 10, 23, 19, 30,
            tzinfo=STOCKHOLM,
        )

        self.baseline = {
            "match_id": self.MATCH_ID,
            "competition": "Juniorallsvenskan D HJ18",
            "home_team": "Tyresö Trollbäcken IBK",
            "away_team": "FBI Tullinge",
            "home_team_id": 20872,
            "away_team_id": 21360,
            "home_match_team_id": 111,
            "away_match_team_id": 222,
            "match_datetime": "2026-10-23T19:45:00",
            "match_status": 1,
            "has_final_result": False,
            "home_goals": 0,
            "away_goals": 0,
            "events": [],
        }

        self.goal_event = {
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
        }

    def make_watches(self):
        return select_active_matches(
            self.registry,
            now=self.now,
        )

    def run_watcher(self, snapshot, mock_ntfy):
        watches = self.make_watches()

        config = {
            "watches": watches,
            "ntfy": {"topic": "test-only"},
        }

        def fake_fetcher(connector_name):
            self.assertEqual(
                connector_name,
                "ibis_floorball",
            )
            return lambda watch: copy.deepcopy(snapshot)

        with (
            patch.object(
                watcher,
                "load_config",
                return_value=config,
            ),
            patch.object(
                watcher,
                "STATE_FILE",
                self.state_file,
            ),
            patch.object(
                watcher,
                "get_fetcher",
                side_effect=fake_fetcher,
            ),
            patch.object(
                watcher,
                "send_ntfy",
                mock_ntfy,
            ),
            patch.dict(
                os.environ,
                {
                    "RUN_MODE": "live",
                    "WATCH_ID": "",
                },
            ),
        ):
            watcher.main()

    def read_state(self):
        return json.loads(
            self.state_file.read_text(encoding="utf-8")
        )

    def test_runtime_watch_selected(self):
        watches = self.make_watches()

        self.assertEqual(len(watches), 1)
        self.assertEqual(watches[0]["id"], self.WATCH_ID)
        self.assertEqual(
            watches[0]["source"]["match_id"],
            self.MATCH_ID,
        )

    def test_initial_baseline_without_notification(self):
        from unittest.mock import Mock

        mock_ntfy = Mock()

        self.run_watcher(self.baseline, mock_ntfy)

        state = self.read_state()

        self.assertIn(self.WATCH_ID, state)
        self.assertFalse(mock_ntfy.called)

    def test_goal_change_generates_notification(self):
        from unittest.mock import Mock

        mock_ntfy = Mock()

        self.run_watcher(self.baseline, mock_ntfy)

        updated = copy.deepcopy(self.baseline)
        updated["match_status"] = 2
        updated["home_goals"] = 1
        updated["events"] = [self.goal_event]

        self.run_watcher(updated, mock_ntfy)

        self.assertEqual(mock_ntfy.call_count, 1)

        args = mock_ntfy.call_args.args

        self.assertEqual(
            args[1],
            "Innebandy - Matchuppdatering",
        )
        self.assertIn("Lukas Widegren", args[2])
        self.assertIn("⭐", args[2])
        self.assertIn("1-0", args[2])

    def test_unchanged_snapshot_no_repeat_notification(self):
        from unittest.mock import Mock

        mock_ntfy = Mock()

        self.run_watcher(self.baseline, mock_ntfy)

        updated = copy.deepcopy(self.baseline)
        updated["match_status"] = 2
        updated["home_goals"] = 1
        updated["events"] = [self.goal_event]

        self.run_watcher(updated, mock_ntfy)
        self.run_watcher(updated, mock_ntfy)

        self.assertEqual(mock_ntfy.call_count, 1)

    def test_final_result_notification_and_state(self):
        from unittest.mock import Mock

        mock_ntfy = Mock()

        self.run_watcher(self.baseline, mock_ntfy)

        final = copy.deepcopy(self.baseline)
        final["match_status"] = 4
        final["has_final_result"] = True
        final["home_goals"] = 5
        final["away_goals"] = 4

        self.run_watcher(final, mock_ntfy)

        self.assertEqual(mock_ntfy.call_count, 1)

        message = mock_ntfy.call_args.args[2]

        self.assertIn("SLUTRESULTAT: 5 - 4", message)

        state = self.read_state()

        self.assertTrue(
            state[self.WATCH_ID]["fields"]["has_final_result"]
        )
        self.assertEqual(
            state[self.WATCH_ID]["fields"]["home_goals"],
            5,
        )

    def test_no_match_selected_before_activation(self):
        early = datetime(
            2026, 10, 23, 19, 29,
            tzinfo=STOCKHOLM,
        )

        watches = select_active_matches(
            self.registry,
            now=early,
        )

        self.assertEqual(watches, [])

    def test_existing_golf_state_preserved(self):
        from unittest.mock import Mock

        existing = {
            "lukas-sgf-ranking": {
                "snapshot": "existing-ranking",
                "fields": {"position": "120"},
            }
        }

        self.state_file.write_text(
            json.dumps(existing),
            encoding="utf-8",
        )

        self.run_watcher(self.baseline, Mock())

        state = self.read_state()

        self.assertEqual(
            state["lukas-sgf-ranking"],
            existing["lukas-sgf-ranking"],
        )
        self.assertIn(self.WATCH_ID, state)


if __name__ == "__main__":
    unittest.main()
