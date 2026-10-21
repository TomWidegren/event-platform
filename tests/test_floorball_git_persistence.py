
"""
Tests for safe Git persistence of the Floorball match registry.

Uses temporary local Git repositories to simulate:
- Independent Discovery and Live executions.
- Concurrent updates based on stale repository state.
- Git push conflicts.
- Refresh, merge and retry.
- Preservation of existing registry information.

No production repository, external API, state.json or
notification service is accessed.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from floorball_git_persistence import persist_registry_changes


class TestFloorballGitPersistence(unittest.TestCase):

    def git(self, cwd, *args):
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def write_registry(self, repo, registry):
        path = Path(repo) / "match_registry.json"
        path.write_text(
            json.dumps(
                registry,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    def read_registry(self, repo):
        path = Path(repo) / "match_registry.json"
        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        root = Path(self.temp.name)

        self.remote = root / "remote.git"
        self.discovery_repo = root / "discovery"
        self.live_repo = root / "live"

        self.git(root, "init", "--bare", str(self.remote))

        self.git(
            root,
            "clone",
            str(self.remote),
            str(self.discovery_repo),
        )

        self.git(
            self.discovery_repo,
            "config",
            "user.name",
            "Event Platform Test",
        )
        self.git(
            self.discovery_repo,
            "config",
            "user.email",
            "test@example.invalid",
        )

        self.git(
            self.discovery_repo,
            "checkout",
            "-b",
            "main",
        )

        initial_registry = {
            "schema_version": 1,
            "matches": {
                "1750707": {
                    "match_id": 1750707,
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

        self.write_registry(
            self.discovery_repo,
            initial_registry,
        )

        self.git(
            self.discovery_repo,
            "add",
            "match_registry.json",
        )
        self.git(
            self.discovery_repo,
            "commit",
            "-m",
            "Initial registry",
        )
        self.git(
            self.discovery_repo,
            "push",
            "-u",
            "origin",
            "main",
        )

        self.git(
            root,
            "clone",
            "-b",
            "main",
            str(self.remote),
            str(self.live_repo),
        )

        self.git(
            self.live_repo,
            "config",
            "user.name",
            "Event Platform Test",
        )
        self.git(
            self.live_repo,
            "config",
            "user.email",
            "test@example.invalid",
        )

    def test_discovery_persists_schedule_change(self):
        result = persist_registry_changes(
            repo_path=self.discovery_repo,
            changes={
                "1750707": {
                    "scheduled_start": "2026-10-23T20:15:00",
                }
            },
            owner="discovery",
        )

        self.assertTrue(result)

        self.git(
            self.discovery_repo,
            "fetch",
            "origin",
            "main",
        )

        registry = json.loads(
            self.git(
                self.discovery_repo,
                "show",
                "origin/main:match_registry.json",
            )
        )

        self.assertEqual(
            registry["matches"]["1750707"]["scheduled_start"],
            "2026-10-23T20:15:00",
        )

    def test_live_persists_completion(self):
        result = persist_registry_changes(
            repo_path=self.live_repo,
            changes={
                "1750707": {
                    "monitoring_status": "completed",
                }
            },
            owner="live",
        )

        self.assertTrue(result)

        self.git(
            self.live_repo,
            "fetch",
            "origin",
            "main",
        )

        registry = json.loads(
            self.git(
                self.live_repo,
                "show",
                "origin/main:match_registry.json",
            )
        )

        self.assertEqual(
            registry["matches"]["1750707"]["monitoring_status"],
            "completed",
        )

    def test_stale_clone_preserves_both_changes(self):
        # Both clones initially have the same registry.
        # Discovery commits first.
        persist_registry_changes(
            repo_path=self.discovery_repo,
            changes={
                "1750707": {
                    "scheduled_start": "2026-10-23T20:15:00",
                }
            },
            owner="discovery",
        )

        # Live starts with an outdated local clone.
        # Persistence must refresh before merging.
        persist_registry_changes(
            repo_path=self.live_repo,
            changes={
                "1750707": {
                    "monitoring_status": "completed",
                }
            },
            owner="live",
        )

        self.git(
            self.discovery_repo,
            "fetch",
            "origin",
            "main",
        )

        registry = json.loads(
            self.git(
                self.discovery_repo,
                "show",
                "origin/main:match_registry.json",
            )
        )

        match = registry["matches"]["1750707"]

        self.assertEqual(
            match["scheduled_start"],
            "2026-10-23T20:15:00",
        )
        self.assertEqual(
            match["monitoring_status"],
            "completed",
        )

    def test_different_matches_are_preserved(self):
        persist_registry_changes(
            repo_path=self.discovery_repo,
            changes={
                "1750707": {
                    "scheduled_start": "2026-10-23T20:15:00",
                }
            },
            owner="discovery",
        )

        persist_registry_changes(
            repo_path=self.live_repo,
            changes={
                "1703577": {
                    "monitoring_status": "completed",
                }
            },
            owner="live",
        )

        self.git(
            self.discovery_repo,
            "fetch",
            "origin",
            "main",
        )

        registry = json.loads(
            self.git(
                self.discovery_repo,
                "show",
                "origin/main:match_registry.json",
            )
        )

        self.assertEqual(
            registry["matches"]["1750707"]["scheduled_start"],
            "2026-10-23T20:15:00",
        )
        self.assertEqual(
            registry["matches"]["1703577"]["monitoring_status"],
            "completed",
        )

    def test_completed_match_not_reactivated(self):
        persist_registry_changes(
            repo_path=self.live_repo,
            changes={
                "1750707": {
                    "monitoring_status": "completed",
                }
            },
            owner="live",
        )

        persist_registry_changes(
            repo_path=self.discovery_repo,
            changes={
                "1750707": {
                    "scheduled_start": "2026-10-23T20:15:00",
                }
            },
            owner="discovery",
        )

        self.git(
            self.discovery_repo,
            "fetch",
            "origin",
            "main",
        )

        registry = json.loads(
            self.git(
                self.discovery_repo,
                "show",
                "origin/main:match_registry.json",
            )
        )

        match = registry["matches"]["1750707"]

        self.assertEqual(
            match["scheduled_start"],
            "2026-10-23T20:15:00",
        )
        self.assertEqual(
            match["monitoring_status"],
            "completed",
        )

    def test_invalid_update_does_not_change_remote(self):
        original_commit = self.git(
            self.discovery_repo,
            "rev-parse",
            "HEAD",
        )

        with self.assertRaises(ValueError):
            persist_registry_changes(
                repo_path=self.discovery_repo,
                changes={
                    "1750707": {
                        "monitoring_status": "completed",
                    }
                },
                owner="discovery",
            )

        remote_commit = self.git(
            self.discovery_repo,
            "ls-remote",
            "origin",
            "refs/heads/main",
        ).split()[0]

        self.assertEqual(
            remote_commit,
            original_commit,
        )


if __name__ == "__main__":
    unittest.main()
