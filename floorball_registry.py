
"""
Floorball match registry logic for Event Platform.

This module manages discovered floorball match information.

It does not:
- Call external APIs.
- Read or write persistent files.
- Modify monitoring state.
- Send notifications.
- Control scheduling.

The update_registry function is intentionally pure:
it returns an updated registry without modifying its inputs.
"""

from copy import deepcopy


SCHEMA_VERSION = 1


def update_registry(
    registry: dict,
    discovered_matches: list,
    teams: list,
) -> dict:
    """
    Merge discovered floorball matches into an existing registry.

    Args:
        registry:
            Existing registry containing schema_version and matches.

        discovered_matches:
            Match dictionaries returned by the iBIS competition
            match-list API.

        teams:
            Configured teams containing team_id, competition_id
            and optional highlight_player_id.

    Returns:
        A new registry dictionary.

    Rules:
        - Add newly discovered relevant matches.
        - Update source-derived information for existing matches.
        - Preserve existing matches missing from discovery results.
        - Preserve completed monitoring status.
        - Exclude matches unrelated to configured teams.
        - Never mutate the original registry.
        - Raise an exception for malformed relevant input.
    """

    if not isinstance(registry, dict):
        raise TypeError("Registry must be a dictionary")

    if not isinstance(discovered_matches, list):
        raise TypeError("Discovered matches must be a list")

    if not isinstance(teams, list):
        raise TypeError("Teams must be a list")

    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported registry schema version")

    existing_matches = registry.get("matches")

    if not isinstance(existing_matches, dict):
        raise ValueError("Registry matches must be a dictionary")

    updated = deepcopy(registry)

    for match in discovered_matches:
        if not isinstance(match, dict):
            raise TypeError("Each discovered match must be a dictionary")

        # Validate identity before processing.
        match_id = match["MatchID"]
        competition_id = match["CompetitionID"]

        if match_id is None or competition_id is None:
            raise ValueError("Match identifiers cannot be null")

        # Identify the configured team associated with the match.
        matching_team = None

        for team in teams:
            if (
                team["competition_id"] == competition_id
                and (
                    team["team_id"] == match.get("HomeTeamID")
                    or team["team_id"] == match.get("AwayTeamID")
                )
            ):
                matching_team = team
                break

        # Ignore matches unrelated to configured teams.
        if matching_team is None:
            continue

        match_key = str(match_id)

        existing = updated["matches"].get(match_key)

        if existing is None:
            monitoring_status = "scheduled"
        else:
            monitoring_status = existing.get(
                "monitoring_status",
                "scheduled",
            )

        # Preserve the monitoring lifecycle while updating
        # information originating from iBIS.
        updated_match = {
            "match_id": match_id,
            "competition_id": competition_id,
            "team_id": matching_team["team_id"],
            "highlight_player_id": matching_team.get(
                "highlight_player_id"
            ),
            "home_team": match.get("HomeTeam"),
            "away_team": match.get("AwayTeam"),
            "scheduled_start": match.get("MatchDateTime"),
            "source_status": match.get("MatchStatus"),
            "cancelled": match.get("Cancelled", False),
            "postponed": match.get("Postponed", False),
            "monitoring_status": monitoring_status,
        }

        # Preserve any additional registry information that
        # may have been added by other lifecycle processes.
        if existing is not None:
            merged_match = deepcopy(existing)
            merged_match.update(updated_match)
            updated_match = merged_match

        updated["matches"][match_key] = updated_match

    return updated
