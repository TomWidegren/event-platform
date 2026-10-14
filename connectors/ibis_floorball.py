
import requests


API_BASE_URL = "https://api.innebandy.se/v2/api/public"


def fetch_snapshot(watch: dict):
    """
    Fetch and normalize one floorball match snapshot.

    Acquisition and normalization are owned by the connector.
    State persistence, change detection and notifications
    remain responsibilities of Event Platform.
    """

    source = watch["source"]
    match_id = source["match_id"]

    url = f"{API_BASE_URL}/matches/{match_id}"

    response = requests.get(
        url,
        headers={
            "Accept": "application/json",
            "Origin": "https://stats.innebandy.se",
            "User-Agent": "Mozilla/5.0",
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

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
