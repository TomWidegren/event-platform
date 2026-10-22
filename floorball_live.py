
"""
Live Watch preparation for Event Platform.

Combines configured Live Watches with automatically selected
floorball matches from the persistent match registry.

This module only prepares runtime configuration.

It does not:
- Fetch external match data.
- Send notifications.
- Modify state.json or match_registry.json.
- Execute Git operations.
- Start monitoring automatically.
"""

import json
from pathlib import Path

from floorball_match_selection import select_active_matches
from floorball_watch_merge import merge_live_watches


REGISTRY_FILE = Path("match_registry.json")


def prepare_live_config(
    config: dict,
    registry: dict,
    now=None,
) -> dict:
    """
    Prepare a Live configuration with automatic floorball Watches.

    Existing non-floorball Live Watches are preserved.
    Automatically selected floorball Watches replace manually
    configured floorball Watches.

    The original configuration and registry are not modified.
    """

    if not isinstance(config, dict):
        raise TypeError("Configuration must be a dictionary")

    if not isinstance(registry, dict):
        raise TypeError("Registry must be a dictionary")

    automatic_watches = select_active_matches(
        registry,
        now=now,
    )

    combined_watches = merge_live_watches(
        config["watches"],
        automatic_watches,
    )

    return {
        **config,
        "watches": combined_watches,
    }


def load_live_config(
    config: dict,
    registry_path: Path = REGISTRY_FILE,
    now=None,
) -> dict:
    """
    Load the match registry and prepare Live configuration.

    Does not persist any changes.
    """

    with Path(registry_path).open(
        "r",
        encoding="utf-8",
    ) as file:
        registry = json.load(file)

    return prepare_live_config(
        config,
        registry,
        now=now,
    )
