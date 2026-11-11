"""
Read-only floorball match discovery for Event Platform.

Returns an updated in-memory registry.
Does not write files, send notifications, execute Git commands
or activate Live monitoring.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from ibis_client import open_ibis_client
from floorball_registry import update_registry


STOCKHOLM = ZoneInfo("Europe/Stockholm")


def discover_matches(
    config: dict,
    registry: dict,
    now: datetime | None = None,
) -> dict:
    """Discover upcoming matches without modifying the inputs."""

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

    with open_ibis_client() as client:
        # Avoid duplicate competition requests.
        competition_ids = sorted({
            team["competition_id"]
            for team in teams
        })

        for competition_id in competition_ids:
            matches = client.get_json(
                f"competitions/{competition_id}/matches"
            )

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
                    # Preserve the existing assumption of
                    # Swedish local time, pending verification.
                    start = start.replace(tzinfo=STOCKHOLM)
                else:
                    start = start.astimezone(STOCKHOLM)

                # Include today's matches even after their
                # scheduled start time.
                if start.date() < today:
                    continue

                if match.get("HasFinalResult") is True:
                    continue

                # Preserve the existing provisional filtering.
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
