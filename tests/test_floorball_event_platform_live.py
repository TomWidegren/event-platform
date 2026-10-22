
"""
Regression tests for the new Event Platform Live runner.

No external API calls, notifications or production Git writes.

Includes a safety regression test for stale same-Watch state.
"""

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import event_platform_live as live


class TestEventPlatformLive(unittest.TestCase):

    WATCH_ID = "floorball-match-1750707"

    def setUp(self):
        self.watch = {
            "id": self.WATCH_ID,
            "name": "Tyresö Trollbäcken IBK - FBI Tullinge",
            "connector": "ibis_floorball",
            "mode": "live",
            "source": {
                "match_id": 1750707,
                "team_id": 20872,
                "highlight_player_id": 585280,
            },
        }

        self.config = {
            "ntfy": {"topic": "test-only"},
            "watches": [self.watch],
        }

        self.baseline = {
            "match_id": 1750707,
            "home_goals": 0,
            "away_goals": 0,
            "has_final_result": False,
            "events": [],
        }

    def snapshot_entry(self, fields):
        return {
            "snapshot": json.dumps(
                fields,
                ensure_ascii=False,
                sort_keys=True,
            ),
            "fields": copy.deepcopy(fields),
        }

    def test_first_observation_creates_baseline(self):
        notify = Mock()

        with (
            patch.object(
                live.watcher,
                "get_fetcher",
                return_value=lambda watch: copy.deepcopy(
                    self.baseline
                ),
            ),
            patch.object(
                live.watcher,
                "send_ntfy",
                notify,
            ),
        ):
            changes, completed = live.collect_updates(
                self.config,
                {},
            )

        self.assertIn(self.WATCH_ID, changes)
        self.assertEqual(completed, set())
        notify.assert_not_called()

    def test_unchanged_observation_does_not_notify(self):
        previous = {
            self.WATCH_ID: self.snapshot_entry(self.baseline)
        }

        notify = Mock()

        with (
            patch.object(
                live.watcher,
                "get_fetcher",
                return_value=lambda watch: copy.deepcopy(
                    self.baseline
                ),
            ),
            patch.object(
                live.watcher,
                "send_ntfy",
                notify,
            ),
        ):
            changes, completed = live.collect_updates(
                self.config,
                previous,
            )

        self.assertEqual(changes, {})
        self.assertEqual(completed, set())
        notify.assert_not_called()

    def test_late_baseline_is_rejected(self):
        late = copy.deepcopy(self.baseline)
        late["home_goals"] = 1

        notify = Mock()

        with (
            patch.object(
                live.watcher,
                "get_fetcher",
                return_value=lambda watch: late,
            ),
            patch.object(
                live.watcher,
                "send_ntfy",
                notify,
            ),
        ):
            with self.assertRaises(RuntimeError):
                live.collect_updates(self.config, {})

        notify.assert_not_called()

    def test_final_result_is_collected(self):
        final = copy.deepcopy(self.baseline)
        final["home_goals"] = 5
        final["away_goals"] = 4
        final["has_final_result"] = True

        previous = {
            self.WATCH_ID: self.snapshot_entry(self.baseline)
        }

        notify = Mock()

        with (
            patch.object(
                live.watcher,
                "get_fetcher",
                return_value=lambda watch: final,
            ),
            patch.object(
                live.watcher,
                "send_ntfy",
                notify,
            ),
        ):
            changes, completed = live.collect_updates(
                self.config,
                previous,
            )

        self.assertEqual(completed, {1750707})
        self.assertTrue(
            changes[self.WATCH_ID]["fields"]["has_final_result"]
        )
        notify.assert_called_once()

    def test_stale_snapshot_must_not_replace_newer_state(self):
        """
        Safety requirement:

        An older non-final snapshot must never overwrite
        a newer final snapshot already stored remotely.
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            repo = root / "worker"

            def git(cwd, *args):
                return subprocess.run(
                    ["git", *args],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )

            git(root, "init", "--bare", str(remote))
            git(root, "clone", str(remote), str(repo))
            git(repo, "checkout", "-b", "main")
            git(repo, "config", "user.name", "Test")
            git(
                repo,
                "config",
                "user.email",
                "test@example.invalid",
            )

            final = copy.deepcopy(self.baseline)
            final["home_goals"] = 5
            final["away_goals"] = 4
            final["has_final_result"] = True

            state = {
                self.WATCH_ID: self.snapshot_entry(final)
            }

            registry = {
                "schema_version": 1,
                "matches": {
                    "1750707": {
                        "match_id": 1750707,
                        "monitoring_status": "completed",
                    }
                },
            }

            (repo / "state.json").write_text(
                json.dumps(state),
                encoding="utf-8",
            )
            (repo / "match_registry.json").write_text(
                json.dumps(registry),
                encoding="utf-8",
            )

            git(
                repo,
                "add",
                "state.json",
                "match_registry.json",
            )
            git(repo, "commit", "-m", "Final state")
            git(repo, "push", "-u", "origin", "main")

            stale = {
                self.WATCH_ID: self.snapshot_entry(
                    self.baseline
                )
            }

            with self.assertRaises(RuntimeError):
                live.persist_live_updates(
                    repo_path=repo,
                    changes=stale,
                    completed=set(),
                )

            git(repo, "fetch", "origin", "main")

            saved = json.loads(
                git(
                    repo,
                    "show",
                    "origin/main:state.json",
                ).stdout
            )

            self.assertTrue(
                saved[self.WATCH_ID]["fields"][
                    "has_final_result"
                ]
            )


if __name__ == "__main__":
    unittest.main()
