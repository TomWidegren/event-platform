
"""
Safe in-memory merge logic for Event Platform floorball registry.

Discovery owns source-derived scheduling and match information.
Live owns monitoring lifecycle information.

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
            Dictionary keyed by MatchID containing only fields
            the requesting process intends to change.

        owner:
            Either "discovery" or "live".

    Returns:
        A new registry with the requested changes applied.

    Rules:
        - Discovery may update source-derived fields only.
        - Live may update monitoring_status only.
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

    # Work on a copy so that failed updates cannot partially
    # modify the original registry.
    updated = deepcopy(registry)

    for match_id, field_changes in changes.items():
        match_key = str(match_id)

        if match_key not in updated["matches"]:
            raise KeyError(
                f"Unknown match in registry: {match_key}"
            )

        if not isinstance(field_changes, dict):
            raise TypeError(
                f"Changes for {match_key} must be a dictionary"
            )

        invalid_fields = (
            set(field_changes) - allowed_fields
        )

        if invalid_fields:
            raise ValueError(
                f"{owner} cannot modify fields: "
                f"{sorted(invalid_fields)}"
            )

        match = updated["matches"][match_key]

        if not isinstance(match, dict):
            raise ValueError(
                f"Invalid registry entry: {match_key}"
            )

        if owner == "live":
            if "monitoring_status" in field_changes:
                new_status = field_changes[
                    "monitoring_status"
                ]

                if new_status not in VALID_MONITORING_STATUSES:
                    raise ValueError(
                        f"Invalid monitoring status: {new_status}"
                    )

                current_status = match.get(
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

        # Apply only fields explicitly included in this update.
        # All unrelated information is preserved.
        for field, value in field_changes.items():
            match[field] = deepcopy(value)

    return updated
