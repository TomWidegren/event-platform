import json
import os
from pathlib import Path

import requests
import yaml

from notification_formatters import format_notification


CONFIG_FILE = Path("config.yml")
STATE_FILE = Path("state.json")


def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_ntfy(topic: str, title: str, message: str):
    url = f"https://ntfy.sh/{topic}"

    resp = requests.post(
        url,
        data=message.encode("utf-8"),
        headers={"Title": title},
        timeout=30,
    )

    resp.raise_for_status()


def get_fetcher(connector_name: str):
    if connector_name == "golfbox_leaderboard":
        from connectors.golfbox_leaderboard import fetch_snapshot
        return fetch_snapshot

    if connector_name == "tournytt_api":
        from connectors.tournytt_api import fetch_snapshot
        return fetch_snapshot

    if connector_name == "sgf_ranking":
        from connectors.sgf_ranking import fetch_snapshot
        return fetch_snapshot

    raise ValueError(f"Unknown connector: {connector_name}")


def snapshot_for(fields: dict) -> str:
    return json.dumps(
        fields,
        ensure_ascii=False,
        sort_keys=True,
    )


def main():
    config = load_config()
    state = load_state()

    topic = config["ntfy"]["topic"]
    updates = []

    run_mode = os.getenv("RUN_MODE")

    if run_mode:
        print(f"RUN_MODE: {run_mode}")

    for watch in config["watches"]:
        watch_mode = watch.get("mode", "daily")

        if run_mode and watch_mode != run_mode:
            continue

        watch_id = watch["id"]
        watch_name = watch["name"]
        connector_name = watch["connector"]

        fetch_snapshot = get_fetcher(connector_name)

        current_fields = fetch_snapshot(watch)

        if not current_fields:
            print(f"{watch_name}: ingen aktuell observation")
            continue

        current_snapshot = snapshot_for(current_fields)

        previous = state.get(watch_id)

        if isinstance(previous, dict):
            previous_snapshot = previous.get("snapshot")

            if previous_snapshot is None:
                previous_snapshot = snapshot_for(previous)
        else:
            previous_snapshot = None

        if previous is None:
            state[watch_id] = {
                "snapshot": current_snapshot,
                "fields": current_fields,
            }

            if watch_mode == "live":
                title, message = format_notification(
                    watch,
                    current_fields,
                )

                send_ntfy(
                    topic,
                    title,
                    message,
                )

                updates.append(
                    f"Första live-resultat notifierat för {watch_name}"
                )
            else:
                updates.append(
                    f"Baslinje sparad för {watch_name}"
                )

            continue

        if previous_snapshot != current_snapshot:
            title, message = format_notification(
                watch,
                current_fields,
            )

            send_ntfy(
                topic,
                title,
                message,
            )

            state[watch_id] = {
                "snapshot": current_snapshot,
                "fields": current_fields,
            }

            updates.append(
                f"Uppdaterad: {watch_name}"
            )

    save_state(state)

    print(
        "\n".join(updates)
        if updates
        else "Ingen ändring."
    )


if __name__ == "__main__":
    main()
