
import requests


STARTKIT_URL = "https://api.innebandy.se/StatsAppApi/api/startkit"
EXPECTED_API_HOST = "api.innebandy.se"


def fetch_snapshot(watch: dict):
    """
    Fetch and normalize one floorball match snapshot.

    The connector owns authentication, acquisition and normalization.
    State persistence, change detection and notifications remain
    responsibilities of Event Platform.
    """

    source = watch["source"]
    match_id = int(source["match_id"])

    with requests.Session() as session:
        startkit_response = session.get(
            STARTKIT_URL,
            headers={
                "Accept": "application/json",
                "Origin": "https://stats.innebandy.se",
            },
            timeout=30,
        )
        startkit_response.raise_for_status()

        credentials = startkit_response.json()
        token = credentials["accessToken"]
        api_root = credentials["apiRoot"].rstrip("/")

        from urllib.parse import urlparse

        parsed_url = urlparse(api_root)
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname != EXPECTED_API_HOST
            or parsed_url.path != "/v2/api/public"
        ):
            raise ValueError("Unexpected iBIS API root")

        response = session.get(
            f"{api_root}/matches/{match_id}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
                "Origin": "https://stats.innebandy.se",
            },
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

    if data.get("MatchID") != match_id:
        raise ValueError("iBIS returned an unexpected match ID")

    events = []

    for event in data.get("Events") or []:
        events.append({
            "event_id": event.get("MatchEventID"),
            "type": event.get("MatchEventType"),
            "type_id": event.get("MatchEventTypeID"),
            "match_team_id": event.get("MatchTeamID"),
            "period": event.get("Period"),
            "minute": event.get("Minute"),
            "second": event.get("Second"),
            "home_goals": event.get("GoalsHomeTeam"),
            "away_goals": event.get("GoalsAwayTeam"),
            "player_id": event.get("PlayerID"),
            "player_name": event.get("PlayerName"),
            "assist_id": event.get("PlayerAssistID"),
            "assist_name": event.get("PlayerAssistName"),
            "penalty_name": event.get("PenaltyName"),
        })

    events.sort(
        key=lambda event: (
            event["period"] or 0,
            event["minute"] or 0,
            event["second"] or 0,
            event["event_id"] or 0,
        )
    )

    return {
        "match_id": data.get("MatchID"),
        "competition": data.get("CompetitionName"),
        "home_team": data.get("HomeTeam"),
        "away_team": data.get("AwayTeam"),
        "home_team_id": data.get("HomeTeamID"),
        "away_team_id": data.get("AwayTeamID"),
        "home_match_team_id": data.get("HomeMatchTeamID"),
        "away_match_team_id": data.get("AwayMatchTeamID"),
        "match_datetime": data.get("MatchDateTime"),
        "match_status": data.get("MatchStatus"),
        "has_final_result": data.get("HasFinalResult"),
        "home_goals": data.get("GoalsHomeTeam"),
        "away_goals": data.get("GoalsAwayTeam"),
        "events": events,
    }
