
import copy
import unittest

from floorball_registry import update_registry


class TestFloorballRegistry(unittest.TestCase):

    def setUp(self):
        self.jas_match = {
            "MatchID": 1750707,
            "CompetitionID": 45004,
            "HomeTeamID": 20872,
            "AwayTeamID": 99999,
            "HomeTeam": "Tyresö Trollbäcken IBK",
            "AwayTeam": "FBI Tullinge",
            "MatchDateTime": "2026-10-23T19:45:00",
            "MatchStatus": 1,
            "HasFinalResult": False,
        }

        self.herrar_match = {
            "MatchID": 1703577,
            "CompetitionID": 44356,
            "HomeTeamID": 4194,
            "AwayTeamID": 88888,
            "HomeTeam": "Tyresö Trollbäcken IBK (A)",
            "AwayTeam": "Älta IF A",
            "MatchDateTime": "2026-10-25T15:45:00",
            "MatchStatus": 1,
            "HasFinalResult": False,
        }

        self.teams = [
            {
                "team_id": 20872,
                "competition_id": 45004,
                "highlight_player_id": 585280,
            },
            {
                "team_id": 4194,
                "competition_id": 44356,
                "highlight_player_id": 585280,
            },
        ]

    def empty_registry(self):
        return {
            "schema_version": 1,
            "matches": {},
        }

    def test_new_matches_are_added(self):
        registry = self.empty_registry()

        result = update_registry(
            registry,
            [self.jas_match, self.herrar_match],
            self.teams,
        )

        self.assertEqual(len(result["matches"]), 2)

        self.assertIn("1750707", result["matches"])
        self.assertIn("1703577", result["matches"])

        jas = result["matches"]["1750707"]

        self.assertEqual(jas["team_id"], 20872)
        self.assertEqual(jas["competition_id"], 45004)
        self.assertEqual(
            jas["scheduled_start"],
            "2026-10-23T19:45:00",
        )
        self.assertEqual(
            jas["monitoring_status"],
            "scheduled",
        )

    def test_existing_matches_are_preserved(self):
        registry = update_registry(
            self.empty_registry(),
            [self.jas_match],
            self.teams,
        )

        result = update_registry(
            registry,
            [self.jas_match, self.herrar_match],
            self.teams,
        )

        self.assertEqual(len(result["matches"]), 2)
        self.assertIn("1750707", result["matches"])
        self.assertIn("1703577", result["matches"])

    def test_schedule_changes_are_updated(self):
        registry = update_registry(
            self.empty_registry(),
            [self.jas_match],
            self.teams,
        )

        changed_match = copy.deepcopy(self.jas_match)
        changed_match["MatchDateTime"] = (
            "2026-10-23T20:15:00"
        )

        result = update_registry(
            registry,
            [changed_match],
            self.teams,
        )

        self.assertEqual(
            result["matches"]["1750707"]["scheduled_start"],
            "2026-10-23T20:15:00",
        )

    def test_completed_matches_are_not_reactivated(self):
        registry = update_registry(
            self.empty_registry(),
            [self.jas_match],
            self.teams,
        )

        registry["matches"]["1750707"][
            "monitoring_status"
        ] = "completed"

        result = update_registry(
            registry,
            [self.jas_match],
            self.teams,
        )

        self.assertEqual(
            result["matches"]["1750707"][
                "monitoring_status"
            ],
            "completed",
        )

    def test_missing_matches_are_preserved(self):
        registry = update_registry(
            self.empty_registry(),
            [self.jas_match],
            self.teams,
        )

        result = update_registry(
            registry,
            [],
            self.teams,
        )

        self.assertIn("1750707", result["matches"])

    def test_unrelated_teams_are_excluded(self):
        unrelated_match = {
            "MatchID": 9999999,
            "CompetitionID": 45004,
            "HomeTeamID": 12345,
            "AwayTeamID": 67890,
            "HomeTeam": "Other Home",
            "AwayTeam": "Other Away",
            "MatchDateTime": "2026-10-23T19:00:00",
            "MatchStatus": 1,
            "HasFinalResult": False,
        }

        result = update_registry(
            self.empty_registry(),
            [unrelated_match],
            self.teams,
        )

        self.assertEqual(result["matches"], {})

    def test_failed_update_does_not_modify_original(self):
        registry = update_registry(
            self.empty_registry(),
            [self.jas_match],
            self.teams,
        )

        original = copy.deepcopy(registry)

        invalid_match = copy.deepcopy(self.herrar_match)
        del invalid_match["MatchID"]

        with self.assertRaises(
            (KeyError, ValueError, TypeError)
        ):
            update_registry(
                registry,
                [self.jas_match, invalid_match],
                self.teams,
            )

        self.assertEqual(registry, original)

    def test_original_registry_is_not_mutated(self):
        registry = self.empty_registry()
        original = copy.deepcopy(registry)

        update_registry(
            registry,
            [self.jas_match],
            self.teams,
        )

        self.assertEqual(registry, original)


if __name__ == "__main__":
    unittest.main()
