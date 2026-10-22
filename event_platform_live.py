
"""
Event Platform - Automatic Live execution.

Uses existing connectors, notification formatting, match selection
and registry merging.

Persists changed Watch snapshots and completed floorball matches
together through Git.

IMPORTANT:
- Requires a dedicated disposable GitHub Actions checkout.
- Uses git reset --hard during persistence.
- Does not modify existing Daily execution.
- Does not activate scheduling.
- Notification delivery is at-least-once, not exactly-once.
"""

import json
import os
from copy import deepcopy
from pathlib import Path

import watcher
from floorball_live import load_live_config
from floorball_registry_merge import merge_registry_changes
from floorball_atomic_persistence import _git, _read_json, _write_json
from notification_formatters import format_notification


MAX_ATTEMPTS = 3
STATE_FILE = "state.json"
REGISTRY_FILE = "match_registry.json"


def collect_updates(config, existing_state):
    """
    Observe configured Live Watches.

    Return:
        changed Watch snapshots
        completed floorball MatchIDs

    Notifications are delivered before the corresponding state
    is persisted, matching the existing watcher behavior.
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
                previous_snapshot = watcher.snapshot_for(previous)

        if previous_snapshot == snapshot:
            print(f"{watch_id}: unchanged")
            continue

        # The first Floorball observation establishes a baseline.
        # If the first observation is already in progress, it must
        # not silently discard events. Fail safely until late-start
        # handling has been verified.
        if previous is None and connector == "ibis_floorball":
            if (
                fields.get("events")
                or fields.get("has_final_result")
                or fields.get("home_goals") not in (None, 0)
                or fields.get("away_goals") not in (None, 0)
            ):
                raise RuntimeError(
                    f"Late Floorball baseline requires review: {watch_id}"
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

            watcher.send_ntfy(topic, title, message)

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
):
    """
    Merge changes against latest origin/main.

    Both state.json and match_registry.json are committed
    together when match completion is involved.
    """

    repo_path = Path(repo_path)

    if not changes and not completed:
        print("No persistence required")
        return False

    for attempt in range(1, max_attempts + 1):
        print(f"Live persistence attempt {attempt}/{max_attempts}")

        _git(repo_path, "fetch", "origin", "main")
        _git(repo_path, "reset", "--hard", "origin/main")

        state = _read_json(repo_path, STATE_FILE)
        registry = _read_json(repo_path, REGISTRY_FILE)

        if not isinstance(state, dict):
            raise ValueError("Invalid state.json")

        if not isinstance(registry, dict):
            raise ValueError("Invalid match_registry.json")

        updated_state = deepcopy(state)

        for watch_id, entry in changes.items():
            current = updated_state.get(watch_id)

            # Never silently overwrite a different, already
            # persisted snapshot for the same Watch.
            if current is not None and current != entry:
                # Same-Watch conflicts require an explicit policy.
                # They must not be resolved by blindly replacing
                # the latest repository value.
                if current.get("fields", {}).get(
                    "has_final_result"
                ) is True:
                    if entry["fields"].get(
                        "has_final_result"
                    ) is not True:
                        raise RuntimeError(
                            f"Refusing to overwrite final state: {watch_id}"
                        )

            updated_state[watch_id] = deepcopy(entry)

        registry_changes = {}

        for match_id in completed:
            watch_id = f"floorball-match-{match_id}"
            entry = updated_state.get(watch_id)

            if (
                not entry
                or entry["fields"].get("has_final_result") is not True
                or entry["fields"].get("match_id") != match_id
            ):
                raise ValueError(
                    f"Missing final snapshot for match {match_id}"
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

        _write_json(repo_path, STATE_FILE, updated_state)
        _write_json(repo_path, REGISTRY_FILE, updated_registry)

        changed_files = []

        if updated_state != state:
            changed_files.append(STATE_FILE)

        if updated_registry != registry:
            changed_files.append(REGISTRY_FILE)

        _git(repo_path, "add", *changed_files)
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
            print("Live state persisted successfully")
            return True

        if attempt == max_attempts:
            raise RuntimeError(
                "Live persistence failed after retries: "
                + result.stderr.strip()
            )

        print("Push failed; refreshing and retrying")

    return False


def main():
    if os.getenv("RUN_MODE") != "live":
        raise RuntimeError("RUN_MODE must be live")

    if os.getenv("WATCH_ID"):
        raise RuntimeError(
            "WATCH_ID must not restrict automatic Live monitoring"
        )

    config = watcher.load_config()

    runtime_config = load_live_config(config)

    state = watcher.load_state()

    print("Automatic Live Watches:", len(runtime_config["watches"]))

    changes, completed = collect_updates(
        runtime_config,
        state,
    )

    persist_live_updates(
        Path.cwd(),
        changes,
        completed,
    )

    print("Automatic Live execution completed")


if __name__ == "__main__":
    main()
