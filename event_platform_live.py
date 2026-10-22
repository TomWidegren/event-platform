
"""
Event Platform - Automatic Live execution.

Combines configured Golf Live Watches with automatically
selected floorball matches.

Collects observations, sends notifications and persists
changed Watch snapshots and completed matches through Git.

IMPORTANT:
- Requires a dedicated disposable GitHub Actions checkout.
- Uses git reset --hard during persistence.
- Does not modify Daily execution.
- Does not activate scheduling.
- Notifications are not guaranteed exactly once.
"""

import os
from copy import deepcopy
from pathlib import Path

import watcher

from floorball_live import load_live_config
from floorball_registry_merge import merge_registry_changes
from floorball_atomic_persistence import (
    _git,
    _read_json,
    _write_json,
)
from notification_formatters import format_notification


MAX_ATTEMPTS = 3
STATE_FILE = "state.json"
REGISTRY_FILE = "match_registry.json"


def collect_updates(config, existing_state):
    """
    Collect changed Live observations.

    Returns:
        changes:
            Dictionary of changed Watch snapshots.

        completed:
            Set of completed floorball MatchIDs.

    Notifications are sent before Git persistence.
    """

    changes = {}
    completed = set()

    topic = config["ntfy"]["topic"]

    for watch in config["watches"]:
        if watch.get("mode", "daily") != "live":
            continue

        watch_id = watch["id"]
        connector = watch["connector"]

        fetch_snapshot = watcher.get_fetcher(connector)
        fields = fetch_snapshot(watch)

        if not fields:
            print(f"{watch_id}: no observation")
            continue

        snapshot = watcher.snapshot_for(fields)
        previous = existing_state.get(watch_id)

        previous_fields = None
        previous_snapshot = None

        if isinstance(previous, dict):
            previous_fields = previous.get("fields")
            previous_snapshot = previous.get("snapshot")

            if previous_snapshot is None:
                previous_snapshot = watcher.snapshot_for(
                    previous
                )

        if previous_snapshot == snapshot:
            print(f"{watch_id}: unchanged")
            continue

        # Reject a late first observation containing
        # match activity, rather than silently losing events.
        if previous is None and connector == "ibis_floorball":
            if (
                fields.get("events")
                or fields.get("has_final_result")
                or fields.get("home_goals") not in (None, 0)
                or fields.get("away_goals") not in (None, 0)
            ):
                raise RuntimeError(
                    "Late Floorball baseline requires review: "
                    f"{watch_id}"
                )

        should_notify = (
            previous is not None
            or connector != "ibis_floorball"
        )

        if should_notify:
            title, message = format_notification(
                watch,
                fields,
                previous_fields,
            )

            watcher.send_ntfy(
                topic,
                title,
                message,
            )

        changes[watch_id] = {
            "snapshot": snapshot,
            "fields": deepcopy(fields),
        }

        if (
            connector == "ibis_floorball"
            and fields.get("has_final_result") is True
        ):
            completed.add(fields["match_id"])

        print(f"{watch_id}: update collected")

    return changes, completed


def persist_live_updates(
    repo_path,
    changes,
    completed,
    max_attempts=MAX_ATTEMPTS,
    expected_state=None,
):
    """
    Persist Live updates safely against latest origin/main.

    Uses optimistic concurrency control:

    - Unrelated Watch updates are preserved.
    - An already persisted identical observation is accepted.
    - A changed remote Watch cannot be overwritten using
      an observation based on stale state.
    - Completed matches update state.json and
      match_registry.json in the same Git commit.

    A detected same-Watch conflict raises RuntimeError.
    """

    repo_path = Path(repo_path)

    if not changes and not completed:
        print("No persistence required")
        return False

    if not isinstance(changes, dict):
        raise TypeError("Changes must be a dictionary")

    if not isinstance(completed, (set, list, tuple)):
        raise TypeError("Completed must be a collection")

    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError(
            "max_attempts must be a positive integer"
        )

    if expected_state is not None:
        if not isinstance(expected_state, dict):
            raise TypeError(
                "expected_state must be a dictionary"
            )

    for attempt in range(1, max_attempts + 1):
        print(
            f"Live persistence attempt "
            f"{attempt}/{max_attempts}"
        )

        # Refresh the dedicated Git working directory.
        _git(
            repo_path,
            "fetch",
            "origin",
            "main",
        )

        _git(
            repo_path,
            "reset",
            "--hard",
            "origin/main",
        )

        state = _read_json(
            repo_path,
            STATE_FILE,
        )

        registry = _read_json(
            repo_path,
            REGISTRY_FILE,
        )

        if not isinstance(state, dict):
            raise ValueError("Invalid state.json")

        if not isinstance(registry, dict):
            raise ValueError(
                "Invalid match_registry.json"
            )

        # Verify that no other execution has changed
        # the same Watch since observation.
        #
        # Compatibility note:
        # Existing callers may omit expected_state.
        # In that case the original behavior is retained.
        if expected_state is not None:
            for watch_id, entry in changes.items():
                remote_entry = state.get(watch_id)
                original_entry = expected_state.get(
                    watch_id
                )

                if remote_entry == entry:
                    continue

                if remote_entry != original_entry:
                    raise RuntimeError(
                        "Concurrent Watch update detected: "
                        f"{watch_id}. Refusing to overwrite "
                        "newer remote state."
                    )

        updated_state = deepcopy(state)

        for watch_id, entry in changes.items():
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Invalid Watch update: {watch_id}"
                )

            if not isinstance(
                entry.get("fields"), dict
            ):
                raise ValueError(
                    f"Missing fields for Watch: {watch_id}"
                )

            current = updated_state.get(watch_id)

            # Protect already persisted final results.
            if (
                isinstance(current, dict)
                and isinstance(
                    current.get("fields"), dict
                )
                and current["fields"].get(
                    "has_final_result"
                ) is True
                and entry["fields"].get(
                    "has_final_result"
                ) is not True
            ):
                raise RuntimeError(
                    "Refusing to overwrite final state: "
                    f"{watch_id}"
                )

            updated_state[watch_id] = deepcopy(entry)

        registry_changes = {}

        for match_id in completed:
            watch_id = f"floorball-match-{match_id}"
            entry = updated_state.get(watch_id)

            if (
                not isinstance(entry, dict)
                or not isinstance(
                    entry.get("fields"), dict
                )
                or entry["fields"].get(
                    "has_final_result"
                ) is not True
                or entry["fields"].get(
                    "match_id"
                ) != match_id
            ):
                raise ValueError(
                    "Missing final snapshot for match "
                    f"{match_id}"
                )

            registry_changes[str(match_id)] = {
                "monitoring_status": "completed",
            }

        updated_registry = merge_registry_changes(
            registry,
            registry_changes,
            owner="live",
        )

        if (
            updated_state == state
            and updated_registry == registry
        ):
            print("Updates already persisted")
            return False

        changed_files = []

        if updated_state != state:
            _write_json(
                repo_path,
                STATE_FILE,
                updated_state,
            )
            changed_files.append(STATE_FILE)

        if updated_registry != registry:
            _write_json(
                repo_path,
                REGISTRY_FILE,
                updated_registry,
            )
            changed_files.append(REGISTRY_FILE)

        _git(
            repo_path,
            "add",
            *changed_files,
        )

        _git(
            repo_path,
            "commit",
            "-m",
            "Update Event Platform Live state",
        )

        result = _git(
            repo_path,
            "push",
            "origin",
            "HEAD:refs/heads/main",
            check=False,
        )

        if result.returncode == 0:
            print(
                "Live state persisted successfully"
            )
            return True

        if attempt == max_attempts:
            raise RuntimeError(
                "Live persistence failed after retries: "
                + result.stderr.strip()
            )

        print(
            "Git push failed; refreshing and retrying"
        )

    raise RuntimeError(
        "Live persistence retries exhausted"
    )


def main():
    if os.getenv("RUN_MODE") != "live":
        raise RuntimeError(
            "RUN_MODE must be live"
        )

    if os.getenv("WATCH_ID"):
        raise RuntimeError(
            "WATCH_ID must not restrict automatic "
            "Live monitoring"
        )

    config = watcher.load_config()

    runtime_config = load_live_config(config)

    state = watcher.load_state()

    print(
        "Automatic Live Watches:",
        len(runtime_config["watches"]),
    )

    changes, completed = collect_updates(
        runtime_config,
        state,
    )

    persist_live_updates(
        repo_path=Path.cwd(),
        changes=changes,
        completed=completed,
        expected_state=state,
    )

    print(
        "Automatic Live execution completed"
    )


if __name__ == "__main__":
    main()
