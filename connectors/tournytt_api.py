import json
import requests


def fetch_leaderboard_json(competition_id: int):
    url = (
        f"https://tournytt.se/api/leaderboard/stream"
        f"?competitions={competition_id}"
    )

    response = requests.get(
        url,
        headers={
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0",
        },
        stream=True,
        timeout=60,
    )

    response.raise_for_status()

    event_name = None
    data_lines = []
    buffer = ""

    for chunk in response.iter_content(
        chunk_size=8192,
        decode_unicode=True,
    ):
        if not chunk:
            continue

        buffer += chunk

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.rstrip("\r")

            if line == "":
                if event_name == "leaderboard" and data_lines:
                    payload = "".join(data_lines).strip()
                    return json.loads(payload)

                event_name = None
                data_lines = []
                continue

            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()

            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].lstrip())

    return None

def extract_player_snapshot(data: dict, player_name: str):
    parts = player_name.strip().split(maxsplit=1)

    if len(parts) != 2:
        raise ValueError(
            "player_name must be in the format 'First Last'"
        )

    first_name, last_name = parts

    for leaderboard in data.get("leaderboards", []):
        classes = leaderboard.get("Classes", [])
        class_name = (
            classes[0]["Name"]
            if classes
            else ""
        )

        for entry in leaderboard.get("LeaderboardEntries", []):
            player = entry.get("Player", {})

            if (
                player.get("FirstName", "").strip() == first_name
                and player.get("LastName", "").strip() == last_name
            ):
                return {
                    "class": class_name,
                    "position": entry.get("Position", {}).get("Text", ""),
                    "score": entry.get("ScoreSum"),
                    "to_par": (
                        entry.get("ScoringToPar", {})
                        .get("ToPar", {})
                        .get("Text", "")
                    ),
                    "played_holes": entry.get("PlayedHoles"),
                    "status": entry.get("ScoringStatus"),
                }

    return None

def fetch_player_snapshot(competition_id, player_name)
    competition_id = watch["competition"]
    player_name = watch["player"]

    data = fetch_leaderboard_json(competition_id)

    if data is None:
        return None

    return extract_player_snapshot(data, player_name)
