
"""
Automatic floorball match selection for Event Platform.

Selects matches eligible for Live monitoring from the
persistent match registry.

The module:
- Uses Swedish local time (Europe/Stockholm).
- Activates monitoring 15 minutes before scheduled start.
- Excludes completed, cancelled and postponed matches.
- Supports multiple simultaneous matches.
- Creates runtime Watches compatible with ibis_floorball.
- Does not modify its inputs.

No external APIs, file writes, Git operations or
notifications are performed.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


STOCKHOLM = ZoneInfo("Europe/Stockholm")
ACTIVATION_MINUTES = 15


def select_active_matches(
    registry: dict,
    now: datetime | None = None,
) -> list[dict]:
    """
    Return runtime Watches for matches eligible for monitoring.

    Args:
        registry:
            Match registry containing schema_version and matches.

        now:
            Optional timezone-aware datetime for testing.
            Defaults to current time in Europe/Stockholm.

    Returns:
        A list of runtime Watch dictionaries.

    A match is eligible when:
    - It is not completed.
    - It is not cancelled or postponed.
    - Its scheduled start is no more than 15 minutes away,
      or its scheduled start has already passed.

    Once eligible, a match remains eligible until completed
    or excluded by its source-derived status.

    Important:
        This initial implementation does not impose an upper
        time limit on overdue matches. Recovery and expiration
        rules must be designed before unattended production use.
    """

    if not isinstance(registry, dict):
        raise TypeError("Registry must be a dictionary")

    if registry.get("schema_version") != 1:
        raise ValueError("Unsupported registry schema version")

    matches = registry.get("matches")

    if not isinstance(matches, dict):
        raise ValueError("Registry matches must be a dictionary")

    if now is None:
        now = datetime.now(STOCKHOLM)
    elif now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    else:
        now = now.astimezone(STOCKHOLM)

    selected = []

    for match_key, match in matches.items():
        if not isinstance(match, dict):
            raise ValueError(
                f"Invalid registry match: {match_key}"
            )

        if match.get("monitoring_status") == "completed":
            continue

        if match.get("cancelled") is True:
            continue

        if match.get("postponed") is True:
            continue

        scheduled_value = match.get("scheduled_start")

        if not scheduled_value:
            continue

        scheduled_start = datetime.fromisoformat(
            scheduled_value.replace("Z", "+00:00")
        )

        if scheduled_start.tzinfo is None:
            # iBIS currently provides local timestamps without
            # an explicit UTC offset. This interpretation is a
            # design assumption pending source verification.
            scheduled_start = scheduled_start.replace(
                tzinfo=STOCKHOLM
            )
        else:
            scheduled_start = scheduled_start.astimezone(
                STOCKHOLM
            )

        activation_time = scheduled_start - timedelta(
            minutes=ACTIVATION_MINUTES
        )

        if now < activation_time:
            continue

        match_id = match["match_id"]
        team_id = match["team_id"]

        watch = {
            "id": f"floorball-match-{match_id}",
            "name": (
                f"{match.get('home_team', '')} - "
                f"{match.get('away_team', '')}"
            ),
            "connector": "ibis_floorball",
            "mode": "live",
            "source": {
                "match_id": match_id,
                "team_id": team_id,
                "highlight_player_id": match.get(
                    "highlight_player_id"
                ),
            },
        }

        selected.append(
            (scheduled_start, match_id, watch)
        )

    selected.sort(
        key=lambda item: (item[0], item[1])
    )

    return [
        watch
        for _, _, watch in selected
    ]
