
"""
Calculate source-owned registry changes for Floorball Discovery.

Compares an existing match registry with an updated registry
and returns only new or changed Discovery-owned fields.

This module does not:
- Access external APIs.
- Read or write files.
- Execute Git operations.
- Send notifications.
- Modify its inputs.
"""

from copy import deepcopy

from floorball_registry_merge import (
    DISCOVERY_FIELDS,
    REQUIRED_NEW_MATCH_FIELDS,
    SCHEMA_VERSION,
)


def calculate_discovery_changes(
    original: dict,
    updated: dict,
) -> dict:
    """
    Calculate changes suitable for persist_registry_changes().

    Existing matches:
        Return only changed Discovery-owned fields.

    New matches:
        Return Discovery-owned fields, including all required
        fields needed to create a valid registry entry.

    Removed matches:
        Ignore removals. Discovery must not delete matches.

    Monitoring lifecycle:
        Never include monitoring_status.

    Returns:
        A dictionary keyed by string MatchID.
    """

    for name, registry in (
        ("original", original),
        ("updated", updated),
    ):
        if not isinstance(registry, dict):
            raise TypeError(
                f"{name} registry must be a dictionary"
            )

        if registry.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported {name} registry schema version"
            )

        if not isinstance(registry.get("matches"), dict):
            raise ValueError(
                f"{name} registry matches must be a dictionary"
            )

    original_matches = original["matches"]
    updated_matches = updated["matches"]

    changes = {}

    for match_id, updated_match in updated_matches.items():
        match_key = str(match_id)

        if not isinstance(updated_match, dict):
            raise ValueError(
                f"Invalid updated match: {match_key}"
            )

        existing_match = original_matches.get(match_key)

        if existing_match is None:
            # New match: include only fields owned by Discovery.
            new_fields = {
                field: deepcopy(value)
                for field, value in updated_match.items()
                if field in DISCOVERY_FIELDS
            }

            missing = (
                REQUIRED_NEW_MATCH_FIELDS - set(new_fields)
            )

            if missing:
                raise ValueError(
                    f"Missing fields for new match {match_key}: "
                    f"{sorted(missing)}"
                )

            changes[match_key] = new_fields
            continue

        if not isinstance(existing_match, dict):
            raise ValueError(
                f"Invalid original match: {match_key}"
            )

        # Existing match: include only changed fields
        # that belong to Daily Discovery.
        field_changes = {}

        for field in DISCOVERY_FIELDS:
            if field not in updated_match:
                continue

            if (
                field not in existing_match
                or updated_match[field] != existing_match[field]
            ):
                field_changes[field] = deepcopy(
                    updated_match[field]
                )

        if field_changes:
            changes[match_key] = field_changes

    return changes
