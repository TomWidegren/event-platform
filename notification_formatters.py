import json
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


FORMATTERS: dict[str, Callable[[dict, str], str]] = {
    "sgf_ranking": format_sgf,
    "golfbox_leaderboard": format_golfbox,
    "tournytt_api": format_tournytt,
}


def format_notification(watch: dict, fields: dict) -> tuple[str, str]:
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

    title = f"Golfuppdatering: {player_name}"
    message = formatter(fields, player_name)

    return title, message
