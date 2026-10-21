
"""
Tests for coordinated persistence of Event Platform monitoring
state and the Floorball match registry.

The tests use temporary local Git repositories.

No production repository, external API, notification service
or production state file is accessed.

These tests define the expected behavior of a future
persist_match_completion() function.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from floorball_atomic_persistence import persist_match_completion


class TestFloorballAtomicPersistence(unittest.TestCase):

    MATCH_ID = 1750707
    WATCH_ID = "floorball-match-1750707"

    def git(self, cwd, *args):
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def write_json(self, repo, filename, data):
        path = Path(repo) / filename
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def remote_json(self, filename):
        self.git(self.repo, "fetch", "origin", "main")
        return json.loads(
            self.git(
                self.repo,
                "show",
                f"origin/main:{filename}",
            )
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        root = Path(self.temp.name)
        self.remote = root / "remote.git"
        self.repo = root / "worker"

        self.git(root, "init", "--bare", str(self.remote))
        self.git(root, "clone", str(self.remote), str(self.repo))
        self.git(self.repo, "checkout", "-b", "main")
        self.git(
            self.repo,
            "config",
            "user.name",
            "Event Platform Test",
        )
        self.git(
            self.repo,
            "config",
            "user.email",
            "test@example.invalid",
        )

        self.initial_state = {
            "lukas-sgf-ranking": {
                "snapshot": "existing-golf-snapshot",
                "fields": {"position": "120"},
            },
            self.WATCH_ID: {
                "snapshot": "previous-floorball-snapshot",
                "fields": {
                    "match_id": self.MATCH_ID,
                    "home_goals": 0,
                    "away_goals": 0,
                    "has_final_result": False,
                },
            },
        }

        self.final_fields = {
            "match_id": self.MATCH_ID,
            "home_goals": 5,
            "away_goals": 4,
            "has_final_result": True,
        }

        self.initial_registry = {
            "schema_version": 1,
            "matches": {
                str(self.MATCH_ID): {
                    "match_id": self.MATCH_ID,
                    "competition_id": 45004,
                    "team_id": 20872,
                    "scheduled_start": "2026-10-23T19:45:00",
                    "monitoring_status": "scheduled",
                },
                "1703577": {
                    "match_id": 1703577,
                    "competition_id": 44356,
                    "team_id": 4194,
                    "scheduled_start": "2026-10-25T15:45:00",
                    "monitoring_status": "scheduled",
                },
            },
        }

        self.write_json(self.repo, "state.json", self.initial_state)
        self.write_json(
            self.repo,
            "match_registry.json",
            self.initial_registry,
        )

        self.git(self.repo, "add", "state.json", "match_registry.json")
        self.git(self.repo, "commit", "-m", "Initial test state")
        self.git(self.repo, "push", "-u", "origin", "main")

    def complete_match(self):
        return persist_match_completion(
            repo_path=self.repo,
            match_id=self.MATCH_ID,
            watch_id=self.WATCH_ID,
            final_fields=self.final_fields,
        )

    def test_final_state_and_registry_saved_together(self):
        result = self.complete_match()
        self.assertTrue(result)

        state = self.remote_json("state.json")
        registry = self.remote_json("match_registry.json")

        self.assertEqual(
            state[self.WATCH_ID]["fields"],
            self.final_fields,
        )
        self.assertTrue(
            registry["matches"][str(self.MATCH_ID)]
            ["monitoring_status"] == "completed"
        )

    def test_both_files_in_same_commit(self):
        before = self.git(self.repo, "rev-parse", "HEAD")
        self.complete_match()

        after = self.git(
            self.repo,
            "ls-remote",
            "origin",
            "refs/heads/main",
        ).split()[0]

        self.assertNotEqual(before, after)

        changed = self.git(
            self.repo,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            after,
        ).splitlines()

        self.assertEqual(
            set(changed),
            {"state.json", "match_registry.json"},
        )

    def test_unrelated_state_and_matches_preserved(self):
        self.complete_match()

        state = self.remote_json("state.json")
        registry = self.remote_json("match_registry.json")

        self.assertEqual(
            state["lukas-sgf-ranking"],
            self.initial_state["lukas-sgf-ranking"],
        )
        self.assertEqual(
            registry["matches"]["1703577"],
            self.initial_registry["matches"]["1703577"],
        )

    def test_invalid_final_snapshot_does_not_commit(self):
        before = self.git(
            self.repo,
            "ls-remote",
            "origin",
            "refs/heads/main",
        ).split()[0]

        with self.assertRaises(ValueError):
            persist_match_completion(
                repo_path=self.repo,
                match_id=self.MATCH_ID,
                watch_id=self.WATCH_ID,
                final_fields={
                    "match_id": self.MATCH_ID,
                    "has_final_result": False,
                },
            )

        after = self.git(
            self.repo,
            "ls-remote",
            "origin",
            "refs/heads/main",
        ).split()[0]

        self.assertEqual(before, after)

    def test_failed_push_does_not_publish_partial_completion(self):
        import floorball_atomic_persistence

        original_git = floorball_atomic_persistence._git

        def reject_push(repo_path, *args, **kwargs):
            if args and args[0] == "push":
                result = subprocess.CompletedProcess(
                    args=["git", *args],
                    returncode=1,
                    stdout="",
                    stderr="Simulated push failure",
                )
                return result

            return original_git(repo_path, *args, **kwargs)

        with patch.object(
            floorball_atomic_persistence,
            "_git",
            side_effect=reject_push,
        ):
            with self.assertRaises(RuntimeError):
                self.complete_match()

        state = self.remote_json("state.json")
        registry = self.remote_json("match_registry.json")

        self.assertEqual(state, self.initial_state)
        self.assertEqual(registry, self.initial_registry)

    def test_invalid_match_id_does_not_commit(self):
        before = self.git(
            self.repo,
            "ls-remote",
            "origin",
            "refs/heads/main",
        ).split()[0]

        with self.assertRaises((KeyError, ValueError)):
            persist_match_completion(
                repo_path=self.repo,
                match_id=9999999,
                watch_id="floorball-match-9999999",
                final_fields=self.final_fields,
            )

        after = self.git(
            self.repo,
            "ls-remote",
            "origin",
            "refs/heads/main",
        ).split()[0]

        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
