
from typing import Callable


def display(value) -> str:
    value = "" if value is None else str(value)
    value = " ".join(value.split())
    return value if value else "-"


def format_sgf(fields: dict, player_name: str) -> str:
    return (
        f"{display(fields.get('name', player_name))}\n"
        f"Placering: {display(fields.get('position'))}\n"
        f"Födelseår: {display(fields.get('birth_year'))}\n"
        f"Klubb: {display(fields.get('club'))}\n"
        f"Distrikt: {display(fields.get('district'))}\n"
        f"Status: {display(fields.get('status'))}\n"
        f"Poäng: {display(fields.get('points'))}\n"
        f"Tävlingar: {display(fields.get('competitions'))}\n"
    )


def format_golfbox(fields: dict, player_name: str) -> str:
    return (
        f"{display(fields.get('name', player_name))}\n"
        f"Placering: {display(fields.get('position'))}\n"
        f"Klubb: {display(fields.get('club'))}\n"
        f"Till par: {display(fields.get('topar'))}\n"
        f"Hål: {display(fields.get('hole'))}\n"
        f"Idag: {display(fields.get('today'))}\n"
        f"Rond 1: {display(fields.get('r1'))}\n"
        f"Rond 2: {display(fields.get('r2'))}\n"
        f"Total: {display(fields.get('total'))}\n"
    )


def format_tournytt(fields: dict, player_name: str) -> str:
    return (
        f"{display(fields.get('name', player_name))}\n"
        f"Placering: {display(fields.get('position'))}\n"
        f"Klass: {display(fields.get('class'))}\n"
        f"Poäng/score: {display(fields.get('score'))}\n"
        f"Till par: {display(fields.get('to_par'))}\n"
        f"Spelade hål: {display(fields.get('played_holes'))}\n"
        f"Status: {display(fields.get('status'))}\n"
    )


def format_floorball(
    fields: dict,
    watch_name: str,
    previous_fields: dict | None = None,
    watch: dict | None = None,
) -> str:
    previous_fields = previous_fields or {}
    source = (watch or {}).get("source", {})

    followed_team_id = source.get("team_id")
    highlight_player_id = source.get("highlight_player_id")

    home_team = fields.get("home_team", "")
    away_team = fields.get("away_team", "")

    home_goals = fields.get("home_goals")
    away_goals = fields.get("away_goals")

    score = (
        f"{display(home_goals)} - {display(away_goals)}"
    )

    lines = [
        f"{home_team} - {away_team}",
        f"Resultat: {score}",
    ]

    previous_events = previous_fields.get("events") or []
    current_events = fields.get("events") or []

    previous_ids = {
        event.get("event_id")
        for event in previous_events
        if event.get("event_id") is not None
    }

    new_events = [
        event
        for event in current_events
        if event.get("event_id") not in previous_ids
    ]

    if not previous_fields:
        new_events = []

    previous_status = previous_fields.get("match_status")
    current_status = fields.get("match_status")

    if previous_fields and previous_status != current_status:
        lines.append("Matchstatus har ändrats.")

    if new_events:
        lines.append("")
        lines.append("Nya matchhändelser:")

    home_match_team_id = fields.get("home_match_team_id")
    away_match_team_id = fields.get("away_match_team_id")

    if followed_team_id == fields.get("home_team_id"):
        followed_match_team_id = home_match_team_id
    elif followed_team_id == fields.get("away_team_id"):
        followed_match_team_id = away_match_team_id
    else:
        followed_match_team_id = None

    for event in new_events:
        event_type = event.get("type", "Händelse")
        period = event.get("period")
        minute = event.get("minute")
        second = event.get("second")

        event_time = (
            f"P{display(period)} "
            f"{int(minute or 0):02d}:{int(second or 0):02d}"
        )

        event_team_id = event.get("match_team_id")
        is_followed_team = (
            followed_match_team_id is not None
            and event_team_id == followed_match_team_id
        )

        player_id = event.get("player_id")
        assist_id = event.get("assist_id")

        is_highlighted = (
            highlight_player_id is not None
            and highlight_player_id in (player_id, assist_id)
        )

        if event.get("type_id") == 1:
            event_score = (
                f"{display(event.get('home_goals'))}-"
                f"{display(event.get('away_goals'))}"
            )

            if is_followed_team:
                description = (
                    f"Mål: {display(event.get('player_name'))}"
                )

                if event.get("assist_name"):
                    description += (
                        f", assist: {event['assist_name']}"
                    )
            else:
                description = "Mål motståndarlaget"

            description += f" ({event_score})"

        elif event.get("type_id") == 2:
            if is_followed_team:
                description = (
                    f"Utvisning: "
                    f"{display(event.get('player_name'))}"
                )
            else:
                description = "Utvisning motståndarlaget"

            if event.get("penalty_name"):
                description += (
                    f", {event['penalty_name']}"
                )

        else:
            description = display(event_type)

        prefix = "⭐ " if is_highlighted else ""

        lines.append(
            f"{prefix}{event_time} - {description}"
        )

    previous_final = previous_fields.get("has_final_result")
    current_final = fields.get("has_final_result")

    if current_final and not previous_final:
        lines.append("")
        lines.append(f"SLUTRESULTAT: {score}")

    return "\n".join(lines)


FORMATTERS: dict[str, Callable] = {
    "sgf_ranking": format_sgf,
    "golfbox_leaderboard": format_golfbox,
    "tournytt_api": format_tournytt,
    "ibis_floorball": format_floorball,
}


def format_notification(
    watch: dict,
    fields: dict,
    previous_fields: dict | None = None,
) -> tuple[str, str]:
    connector_name = watch["connector"]

    player_name = watch.get("source", {}).get(
        "player",
        watch.get("name", ""),
    )

    formatter = FORMATTERS.get(connector_name)

    if formatter is None:
        raise ValueError(
            f"No notification formatter for connector: {connector_name}"
        )

    if connector_name == "ibis_floorball":
        title = "Innebandy - Matchuppdatering"
        message = formatter(
            fields,
            player_name,
            previous_fields,
            watch,
        )
    else:
        title = f"Golfuppdatering: {player_name}"
        message = formatter(
            fields,
            player_name,
        )

    return title, message
