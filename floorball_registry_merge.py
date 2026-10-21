
"""
Safe in-memory merge logic for Event Platform floorball registry.

Discovery owns source-derived scheduling and match information.
Live owns monitoring lifecycle information.

Discovery may create new match entries.
Live may only update existing match entries.

This module does not:
- Access external APIs.
- Read or write files.
- Send notifications.
- Modify Event Platform monitoring state.
- Execute Git operations.

GitHub persistence, conflict retries and workflow concurrency
are separate responsibilities.
"""

from copy import deepcopy


SCHEMA_VERSION = 1

DISCOVERY_FIELDS = frozenset({
    "match_id",
    "competition_id",
    "team_id",
    "highlight_player_id",
    "home_team",
    "away_team",
    "scheduled_start",
    "source_status",
    "cancelled",
    "postponed",
})

LIVE_FIELDS = frozenset({
    "monitoring_status",
})

VALID_MONITORING_STATUSES = frozenset({
    "scheduled",
    "completed",
})

REQUIRED_NEW_MATCH_FIELDS = frozenset({
    "match_id",
    "competition_id",
    "team_id",
    "scheduled_start",
})


def merge_registry_changes(
    registry: dict,
    changes: dict,
    owner: str,
) -> dict:
    """
    Apply owner-specific match changes to a registry.

    Args:
        registry:
            The latest available registry.

        changes:
            Dictionary keyed by MatchID containing fields
            the requesting process intends to change.

        owner:
            Either "discovery" or "live".

    Returns:
        A new registry with the requested changes applied.

    Rules:
        - Discovery may create new matches.
        - Discovery may update source-derived fields.
        - Live may update monitoring_status only.
        - Live cannot create new matches.
        - Completed matches cannot be reactivated.
        - Unrelated matches and fields are preserved.
        - Original inputs are never mutated.
        - Invalid updates are rejected atomically.

    This function does not guarantee safe GitHub persistence.
    """

    if owner not in ("discovery", "live"):
        raise ValueError(f"Unknown registry owner: {owner}")

    if not isinstance(registry, dict):
        raise TypeError("Registry must be a dictionary")

    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported registry schema version")

    existing_matches = registry.get("matches")

    if not isinstance(existing_matches, dict):
        raise ValueError("Registry matches must be a dictionary")

    if not isinstance(changes, dict):
        raise TypeError("Changes must be a dictionary")

    allowed_fields = (
        DISCOVERY_FIELDS
        if owner == "discovery"
        else LIVE_FIELDS
    )

    # All changes are applied to a copy.
    # A failed update cannot partially mutate the input.
    updated = deepcopy(registry)

    for match_id, field_changes in changes.items():
        match_key = str(match_id)

        if not isinstance(field_changes, dict):
            raise TypeError(
                f"Changes for {match_key} must be a dictionary"
            )

        invalid_fields = set(field_changes) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"{owner} cannot modify fields: "
                f"{sorted(invalid_fields)}"
            )

        existing = updated["matches"].get(match_key)

        # New matches may only be created by Discovery.
        if existing is None:
            if owner != "discovery":
                raise KeyError(
                    f"Live cannot create match: {match_key}"
                )

            missing_fields = (
                REQUIRED_NEW_MATCH_FIELDS - set(field_changes)
            )

            if missing_fields:
                raise ValueError(
                    f"Missing fields for new match {match_key}: "
                    f"{sorted(missing_fields)}"
                )

            new_match = deepcopy(field_changes)

            # Ensure that the registry key and stored MatchID
            # refer to the same match.
            if str(new_match["match_id"]) != match_key:
                raise ValueError(
                    f"MatchID mismatch for {match_key}"
                )

            if not isinstance(new_match["match_id"], int):
                raise ValueError("MatchID must be an integer")

            if new_match["match_id"] <= 0:
                raise ValueError("MatchID must be positive")

            if not isinstance(
                new_match["competition_id"], int
            ):
                raise ValueError(
                    "CompetitionID must be an integer"
                )

            if not isinstance(new_match["team_id"], int):
                raise ValueError("TeamID must be an integer")

            if not new_match["scheduled_start"]:
                raise ValueError(
                    "Scheduled start cannot be empty"
                )

            # Discovery never owns monitoring lifecycle.
            # Newly discovered matches always start scheduled.
            new_match["monitoring_status"] = "scheduled"

            updated["matches"][match_key] = new_match
            continue

        if not isinstance(existing, dict):
            raise ValueError(
                f"Invalid registry entry: {match_key}"
            )

        # Existing match: preserve all fields not explicitly
        # owned and updated by the requesting process.
        if owner == "live":
            if "monitoring_status" in field_changes:
                new_status = field_changes[
                    "monitoring_status"
                ]

                if new_status not in VALID_MONITORING_STATUSES:
                    raise ValueError(
                        f"Invalid monitoring status: {new_status}"
                    )

                current_status = existing.get(
                    "monitoring_status",
                    "scheduled",
                )

                if (
                    current_status == "completed"
                    and new_status != "completed"
                ):
                    raise ValueError(
                        "Completed matches cannot be reactivated"
                    )

        # Prevent changes to the stable identity of an
        # already registered match.
        if (
            "match_id" in field_changes
            and field_changes["match_id"]
            != existing.get("match_id")
        ):
            raise ValueError(
                f"Cannot change MatchID for {match_key}"
            )

        for field, value in field_changes.items():
            existing[field] = deepcopy(value)

    return updated
