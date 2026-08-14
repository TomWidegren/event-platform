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
