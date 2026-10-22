
"""
Tests for merging configured Live Watches with automatically
selected floorball matches.

No API calls, file writes, notifications or Git operations.
"""

import copy
import unittest

from floorball_watch_merge import merge_live_watches


class TestFloorballWatchMerge(unittest.TestCase):

    def setUp(self):
        self.configured = [
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
                "name": "Previous JAS match",
                "connector": "ibis_floorball",
                "mode": "live",
            },
            {
                "id": "floorball-match-1703572",
                "name": "Previous men's match",
                "connector": "ibis_floorball",
                "mode": "live",
            },
        ]

        self.automatic = [
            {
                "id": "floorball-match-1750707",
                "name": "Tyresö Trollbäcken IBK - FBI Tullinge",
                "connector": "ibis_floorball",
                "mode": "live",
                "source": {
                    "match_id": 1750707,
                    "team_id": 20872,
                    "highlight_player_id": 585280,
                },
            },
            {
                "id": "floorball-match-1703577",
                "name": "Tyresö Trollbäcken IBK (A) - Älta IF A",
                "connector": "ibis_floorball",
                "mode": "live",
                "source": {
                    "match_id": 1703577,
                    "team_id": 4194,
                    "highlight_player_id": 585280,
                },
            },
        ]

    def merge(self, configured=None, automatic=None):
        return merge_live_watches(
            self.configured if configured is None else configured,
            self.automatic if automatic is None else automatic,
        )

    def test_golf_watches_preserved(self):
        result = self.merge()
        ids = {watch["id"] for watch in result}

        self.assertIn("lukas-golfbox", ids)
        self.assertIn("lukas-tournytt", ids)

    def test_daily_watches_excluded(self):
        ids = {watch["id"] for watch in self.merge()}
        self.assertNotIn("lukas-sgf-ranking", ids)

    def test_automatic_matches_included(self):
        ids = {watch["id"] for watch in self.merge()}

        self.assertIn("floorball-match-1750707", ids)
        self.assertIn("floorball-match-1703577", ids)

    def test_old_manual_floorball_watches_excluded(self):
        ids = {watch["id"] for watch in self.merge()}

        self.assertNotIn("floorball-match-1750693", ids)
        self.assertNotIn("floorball-match-1703572", ids)

    def test_no_duplicate_watch_ids(self):
        result = self.merge(
            automatic=self.automatic + [
                copy.deepcopy(self.automatic[0])
            ]
        )

        ids = [watch["id"] for watch in result]
        self.assertEqual(len(ids), len(set(ids)))

    def test_automatic_watch_takes_precedence(self):
        manual = copy.deepcopy(self.automatic[0])
        manual["name"] = "Old manual configuration"

        result = self.merge(
            configured=self.configured + [manual]
        )

        selected = next(
            watch for watch in result
            if watch["id"] == "floorball-match-1750707"
        )

        self.assertEqual(
            selected["name"],
            self.automatic[0]["name"],
        )

    def test_no_automatic_matches(self):
        result = self.merge(automatic=[])

        self.assertEqual(
            {watch["id"] for watch in result},
            {"lukas-golfbox", "lukas-tournytt"},
        )

    def test_original_inputs_unchanged(self):
        configured_before = copy.deepcopy(self.configured)
        automatic_before = copy.deepcopy(self.automatic)

        self.merge()

        self.assertEqual(self.configured, configured_before)
        self.assertEqual(self.automatic, automatic_before)

    def test_all_result_watches_are_live(self):
        result = self.merge()

        self.assertTrue(
            all(watch["mode"] == "live" for watch in result)
        )

    def test_automatic_floorball_watch_structure_preserved(self):
        result = self.merge()

        selected = next(
            watch for watch in result
            if watch["id"] == "floorball-match-1750707"
        )

        self.assertEqual(
            selected["source"],
            self.automatic[0]["source"],
        )


if __name__ == "__main__":
    unittest.main()
