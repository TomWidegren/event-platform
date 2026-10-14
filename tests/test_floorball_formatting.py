
import unittest

from notification_formatters import format_notification


WATCH = {
    "id": "floorball-match-1750693",
    "name": "Huddinge IBS - Tyresö Trollbäcken IBK",
    "connector": "ibis_floorball",
    "mode": "live",
    "source": {
        "match_id": 1750693,
        "team_id": 20872,
        "highlight_player_id": 585280,
    },
}


def snapshot(events=None, status=2, final=False):
    return {
        "match_id": 1750693,
        "home_team": "Huddinge IBS",
        "away_team": "Tyresö Trollbäcken IBK",
        "home_team_id": 100,
        "away_team_id": 20872,
        "home_match_team_id": 200,
        "away_match_team_id": 300,
        "match_status": status,
        "has_final_result": final,
        "home_goals": 1,
        "away_goals": 2,
        "events": events or [],
    }


def event(
    event_id,
    type_id,
    match_team_id,
    player_id=None,
    player_name=None,
    assist_id=None,
    assist_name=None,
    penalty_name=None,
):
    return {
        "event_id": event_id,
        "type_id": type_id,
        "type": "Mål" if type_id == 1 else "Utvisning",
        "match_team_id": match_team_id,
        "period": 2,
        "minute": 12,
        "second": 34,
        "home_goals": 1,
        "away_goals": 2,
        "player_id": player_id,
        "player_name": player_name,
        "assist_id": assist_id,
        "assist_name": assist_name,
        "penalty_name": penalty_name,
    }


class FloorballFormattingTests(unittest.TestCase):

    def test_multiple_new_events(self):
        previous = snapshot(events=[])

        current = snapshot(events=[
            event(1, 1, 200),
            event(
                2, 1, 300,
                player_id=585280,
                player_name="Lukas Widegren",
            ),
            event(
                3, 2, 300,
                player_id=12345,
                player_name="Test Player",
                penalty_name="Hårt spel 2 min",
            ),
        ])

        _, message = format_notification(
            WATCH, current, previous
        )

        self.assertIn("Mål motståndarlaget", message)
        self.assertIn("Lukas Widegren", message)
        self.assertIn("Test Player", message)
        self.assertIn("Hårt spel 2 min", message)
        self.assertEqual(
            message.count("P2 12:34"),
            3,
        )

    def test_lukas_goal_assist_and_penalty(self):
        previous = snapshot(events=[])

        current = snapshot(events=[
            event(
                10, 1, 300,
                player_id=585280,
                player_name="Lukas Widegren",
            ),
            event(
                11, 1, 300,
                player_id=12345,
                player_name="Test Player",
                assist_id=585280,
                assist_name="Lukas Widegren",
            ),
            event(
                12, 2, 300,
                player_id=585280,
                player_name="Lukas Widegren",
                penalty_name="Hårt spel 2 min",
            ),
        ])

        _, message = format_notification(
            WATCH, current, previous
        )

        self.assertEqual(message.count("⭐"), 3)

    def test_existing_events_are_not_repeated(self):
        old_event = event(20, 1, 200)

        previous = snapshot(events=[old_event])
        current = snapshot(events=[
            old_event,
            event(21, 1, 300),
        ])

        _, message = format_notification(
            WATCH, current, previous
        )

        self.assertEqual(
            message.count("P2 12:34"),
            1,
        )

    def test_final_result_without_new_events(self):
        previous = snapshot(events=[], final=False)
        current = snapshot(events=[], final=True)

        _, message = format_notification(
            WATCH, current, previous
        )

        self.assertIn("SLUTRESULTAT: 1 - 2", message)

    def test_golf_formatter_unchanged(self):
        golf_watch = {
            "connector": "sgf_ranking",
            "name": "SGF Ranking",
            "source": {"player": "Lukas Widegren"},
        }

        fields = {
            "name": "Lukas Widegren",
            "position": "1147",
            "points": "5,37",
            "competitions": "7",
        }

        title, message = format_notification(
            golf_watch, fields
        )

        self.assertEqual(
            title,
            "Golfuppdatering: Lukas Widegren",
        )
        self.assertIn("Poäng: 5,37", message)


if __name__ == "__main__":
    unittest.main()
