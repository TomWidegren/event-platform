
"""
Read-only floorball match discovery for Event Platform.

Reads configured teams and competitions, retrieves match lists
from the iBIS API, and calculates an updated match registry.

This module does not:
- Write configuration or registry files.
- Modify state.json.
- Send notifications.
- Execute Git commands.
- Activate Live monitoring.

Persistent Git storage and scheduling are separate concerns.
"""

from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests

from floorball_registry import update_registry


STARTKIT_URL = (
    "https://api.innebandy.se/StatsAppApi/api/startkit"
)

EXPECTED_API_HOST = "api.innebandy.se"
STOCKHOLM = ZoneInfo("Europe/Stockholm")


def discover_matches(
    config: dict,
    registry: dict,
    now: datetime | None = None,
) -> dict:
    """
    Discover upcoming matches and return an updated registry.

    Args:
        config:
            Event Platform configuration containing a
            floorball_discovery section.

        registry:
            Existing match registry.

        now:
            Optional timezone-aware datetime for testing.
            Defaults to current time in Europe/Stockholm.

    Returns:
        A new in-memory match registry.

    The function does not persist any changes.
    """

    if not isinstance(config, dict):
        raise TypeError("Configuration must be a dictionary")

    discovery_config = config.get("floorball_discovery")

    if not isinstance(discovery_config, dict):
        raise ValueError(
            "Missing floorball_discovery configuration"
        )

    teams = discovery_config.get("teams")

    if not isinstance(teams, list) or not teams:
        raise ValueError(
            "floorball_discovery.teams must be a non-empty list"
        )

    for team in teams:
        if not isinstance(team, dict):
            raise ValueError("Invalid team configuration")

        for required in ("team_id", "competition_id"):
            if required not in team:
                raise ValueError(
                    f"Missing team configuration: {required}"
                )

    if now is None:
        now = datetime.now(STOCKHOLM)
    elif now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    else:
        now = now.astimezone(STOCKHOLM)

    today = now.date()
    discovered = []

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

        parsed = urlparse(api_root)

        if (
            parsed.scheme != "https"
            or parsed.hostname != EXPECTED_API_HOST
            or parsed.path != "/v2/api/public"
        ):
            raise ValueError("Unexpected iBIS API root")

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Origin": "https://stats.innebandy.se",
        }

        # Avoid duplicate competition requests.
        competition_ids = sorted({
            team["competition_id"]
            for team in teams
        })

        for competition_id in competition_ids:
            response = session.get(
                (
                    f"{api_root}/competitions/"
                    f"{competition_id}/matches"
                ),
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            matches = response.json()

            if not isinstance(matches, list):
                raise ValueError(
                    "Unexpected competition match-list format"
                )

            for match in matches:
                if not isinstance(match, dict):
                    raise ValueError(
                        "Invalid match in competition response"
                    )

                match_id = match.get("MatchID")
                match_competition = match.get("CompetitionID")

                if match_id is None:
                    raise ValueError(
                        "Missing MatchID in competition response"
                    )

                if match_competition != competition_id:
                    continue

                matching_team = next(
                    (
                        team
                        for team in teams
                        if (
                            team["competition_id"]
                            == competition_id
                            and team["team_id"] in (
                                match.get("HomeTeamID"),
                                match.get("AwayTeamID"),
                            )
                        )
                    ),
                    None,
                )

                if matching_team is None:
                    continue

                start_value = match.get("MatchDateTime")

                if not start_value:
                    continue

                start = datetime.fromisoformat(
                    start_value.replace("Z", "+00:00")
                )

                if start.tzinfo is None:
                    # iBIS timestamps are assumed to represent
                    # Swedish local time, pending verification.
                    start = start.replace(tzinfo=STOCKHOLM)
                else:
                    start = start.astimezone(STOCKHOLM)

                # Include upcoming matches and today's matches,
                # including matches whose scheduled start passed.
                if start.date() < today:
                    continue

                if match.get("HasFinalResult") is True:
                    continue

                # These fields remain provisional until the
                # source status model has been verified.
                if match.get("Cancelled") is True:
                    continue

                if match.get("Abandoned") is True:
                    continue

                discovered.append(match)

    return update_registry(
        registry,
        discovered,
        teams,
    )
