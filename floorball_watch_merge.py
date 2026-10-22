
"""
Merge configured Live Watches with automatically selected
floorball Watches for Event Platform.

The module:
- Preserves existing non-floorball Live Watches.
- Excludes Daily Watches.
- Replaces manually configured floorball Watches with
  automatically selected floorball Watches.
- Prevents duplicate Watch IDs.
- Gives automatically selected floorball Watches precedence.
- Does not modify its inputs.

No API calls, file writes, Git operations or notifications.
"""

from copy import deepcopy


def merge_live_watches(
    configured_watches: list,
    automatic_watches: list,
) -> list:
    """
    Return the combined Live Watch configuration.

    Existing non-floorball Live Watches are preserved.

    Manually configured floorball Watches are excluded.
    Only automatically selected floorball Watches are used.

    Duplicate Watch IDs are removed.

    The input lists and their contents are never modified.
    """

    if not isinstance(configured_watches, list):
        raise TypeError(
            "configured_watches must be a list"
        )

    if not isinstance(automatic_watches, list):
        raise TypeError(
            "automatic_watches must be a list"
        )

    merged = {}
    order = []

    # Preserve configured Live Watches other than floorball.
    for watch in configured_watches:
        if not isinstance(watch, dict):
            raise TypeError(
                "Each configured Watch must be a dictionary"
            )

        if watch.get("mode", "daily") != "live":
            continue

        if watch.get("connector") == "ibis_floorball":
            continue

        watch_id = watch["id"]

        if watch_id not in merged:
            order.append(watch_id)

        merged[watch_id] = deepcopy(watch)

    # Add automatically selected floorball Watches.
    # The automatic version takes precedence for duplicate IDs.
    for watch in automatic_watches:
        if not isinstance(watch, dict):
            raise TypeError(
                "Each automatic Watch must be a dictionary"
            )

        if watch.get("mode") != "live":
            raise ValueError(
                "Automatic Watch must use live mode"
            )

        if watch.get("connector") != "ibis_floorball":
            raise ValueError(
                "Automatic Watch must use ibis_floorball"
            )

        watch_id = watch["id"]

        if watch_id not in merged:
            order.append(watch_id)

        merged[watch_id] = deepcopy(watch)

    return [
        merged[watch_id]
        for watch_id in order
    ]
