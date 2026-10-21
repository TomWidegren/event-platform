
"""
Isolated tests for Event Platform Floorball Discovery.

Tests configuration, iBIS authentication, competition retrieval,
team filtering, registry updates and failure handling.

No real API requests, Git operations, file writes or
notifications are performed.
"""

import copy
import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from floorball_discovery import discover_matches


STOCKHOLM = ZoneInfo("Europe/Stockholm")

API_ROOT = "https://api.innebandy.se/v2/api/public"


class TestFloorballDiscovery(unittest.TestCase):

    def setUp(self):
        self.config = {
            "floorball_discovery": {
                "teams": [
                    {
                        "name": "Tyresö Trollbäcken IBK - JAS",
                        "team_id": 20872,
                        "competition_id": 45004,
                        "highlight_player_id": 585280,
                    },
                    {
                        "name": "Tyresö Trollbäcken IBK - Herrar",
                        "team_id": 4194,
                        "competition_id": 44356,
                        "highlight_player_id": 585280,
                    },
                ]
            }
        }

        self.registry = {
            "schema_version": 1,
            "matches": {},
        }

        self.now = datetime(
            2026, 10, 21, 15, 0,
            tzinfo=STOCKHOLM,
        )

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

    def make_response(self, payload, status_code=200):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = payload

        if status_code >= 400:
            response.raise_for_status.side_effect = (
                RuntimeError("Simulated API failure")
            )

        return response

    def run_discovery(
        self,
        registry=None,
        config=None,
        competition_data=None,
    ):
        registry = (
            self.registry if registry is None else registry
        )
        config = (
            self.config if config is None else config
        )

        if competition_data is None:
            competition_data = {
                45004: [self.jas_match],
                44356: [self.herrar_match],
            }

        session = Mock()

        def fake_get(url, **kwargs):
            if url.endswith("/startkit"):
                return self.make_response({
                    "accessToken": "test-token",
                    "apiRoot": API_ROOT,
                })

            for competition_id, matches in competition_data.items():
                if url.endswith(
                    f"/competitions/{competition_id}/matches"
                ):
                    return self.make_response(matches)

            raise AssertionError(
                f"Unexpected API request: {url}"
            )

        session.get.side_effect = fake_get

        context_manager = Mock()
        context_manager.__enter__ = Mock(
            return_value=session
        )
        context_manager.__exit__ = Mock(
            return_value=False
        )

        with patch(
            "floorball_discovery.requests.Session",
            return_value=context_manager,
        ):
            result = discover_matches(
                config,
                registry,
                now=self.now,
            )

        return result, session

    def test_both_teams_discovered(self):
        result, _ = self.run_discovery()

        self.assertEqual(len(result["matches"]), 2)
        self.assertIn("1750707", result["matches"])
        self.assertIn("1703577", result["matches"])

    def test_correct_team_configuration(self):
        result, _ = self.run_discovery()

        jas = result["matches"]["1750707"]
        herrar = result["matches"]["1703577"]

        self.assertEqual(jas["team_id"], 20872)
        self.assertEqual(jas["competition_id"], 45004)
        self.assertEqual(
            jas["highlight_player_id"],
            585280,
        )

        self.assertEqual(herrar["team_id"], 4194)
        self.assertEqual(herrar["competition_id"], 44356)

    def test_unrelated_matches_excluded(self):
        unrelated = {
            **self.jas_match,
            "MatchID": 9999999,
            "HomeTeamID": 12345,
            "AwayTeamID": 67890,
        }

        result, _ = self.run_discovery(
            competition_data={
                45004: [self.jas_match, unrelated],
                44356: [self.herrar_match],
            }
        )

        self.assertNotIn("9999999", result["matches"])
        self.assertEqual(len(result["matches"]), 2)

    def test_past_matches_excluded(self):
        past = {
            **self.jas_match,
            "MatchID": 1750693,
            "MatchDateTime": "2026-10-15T20:15:00",
        }

        result, _ = self.run_discovery(
            competition_data={
                45004: [past, self.jas_match],
                44356: [self.herrar_match],
            }
        )

        self.assertNotIn("1750693", result["matches"])
        self.assertIn("1750707", result["matches"])

    def test_completed_source_matches_excluded(self):
        completed = {
            **self.jas_match,
            "MatchID": 1750693,
            "HasFinalResult": True,
        }

        result, _ = self.run_discovery(
            competition_data={
                45004: [completed, self.jas_match],
                44356: [self.herrar_match],
            }
        )

        self.assertNotIn("1750693", result["matches"])

    def test_existing_registry_preserved(self):
        registry = {
            "schema_version": 1,
            "matches": {
                "1750693": {
                    "match_id": 1750693,
                    "monitoring_status": "completed",
                    "scheduled_start": "2026-10-15T20:15:00",
                }
            },
        }

        original = copy.deepcopy(registry)

        result, _ = self.run_discovery(registry=registry)

        self.assertEqual(
            result["matches"]["1750693"],
            original["matches"]["1750693"],
        )
        self.assertEqual(registry, original)

    def test_schedule_change_updated(self):
        registry = {
            "schema_version": 1,
            "matches": {
                "1750707": {
                    "match_id": 1750707,
                    "scheduled_start": "2026-10-23T19:45:00",
                    "monitoring_status": "scheduled",
                }
            },
        }

        changed = {
            **self.jas_match,
            "MatchDateTime": "2026-10-23T20:15:00",
        }

        result, _ = self.run_discovery(
            registry=registry,
            competition_data={
                45004: [changed],
                44356: [self.herrar_match],
            },
        )

        self.assertEqual(
            result["matches"]["1750707"]["scheduled_start"],
            "2026-10-23T20:15:00",
        )

    def test_completed_registry_match_not_reactivated(self):
        registry = {
            "schema_version": 1,
            "matches": {
                "1750707": {
                    "match_id": 1750707,
                    "monitoring_status": "completed",
                }
            },
        }

        result, _ = self.run_discovery(registry=registry)

        self.assertEqual(
            result["matches"]["1750707"]["monitoring_status"],
            "completed",
        )

    def test_api_failure_preserves_original_registry(self):
        registry = copy.deepcopy(self.registry)
        original = copy.deepcopy(registry)

        session = Mock()

        session.get.return_value = self.make_response(
            {},
            status_code=500,
        )

        context_manager = Mock()
        context_manager.__enter__ = Mock(
            return_value=session
        )
        context_manager.__exit__ = Mock(
            return_value=False
        )

        with patch(
            "floorball_discovery.requests.Session",
            return_value=context_manager,
        ):
            with self.assertRaises(RuntimeError):
                discover_matches(
                    self.config,
                    registry,
                    now=self.now,
                )

        self.assertEqual(registry, original)

    def test_invalid_api_root_rejected(self):
        session = Mock()

        session.get.return_value = self.make_response({
            "accessToken": "test-token",
            "apiRoot": "https://untrusted.example/api",
        })

        context_manager = Mock()
        context_manager.__enter__ = Mock(
            return_value=session
        )
        context_manager.__exit__ = Mock(
            return_value=False
        )

        with patch(
            "floorball_discovery.requests.Session",
            return_value=context_manager,
        ):
            with self.assertRaises(ValueError):
                discover_matches(
                    self.config,
                    self.registry,
                    now=self.now,
                )

    def test_missing_configuration_rejected(self):
        with self.assertRaises(ValueError):
            discover_matches(
                {},
                self.registry,
                now=self.now,
            )

    def test_competition_fetched_only_once(self):
        config = copy.deepcopy(self.config)

        config["floorball_discovery"]["teams"].append({
            "name": "Another team in JAS",
            "team_id": 12345,
            "competition_id": 45004,
        })

        _, session = self.run_discovery(config=config)

        urls = [
            call.args[0]
            for call in session.get.call_args_list
        ]

        jas_url = (
            f"{API_ROOT}/competitions/45004/matches"
        )

        self.assertEqual(urls.count(jas_url), 1)


if __name__ == "__main__":
    unittest.main()
