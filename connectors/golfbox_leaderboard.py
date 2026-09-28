import re
from typing import List

from playwright.sync_api import sync_playwright


GOLFBOX_BASE_URL = (
    "https://www.golfbox.dk/livescoring/tour/?language=1053"
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def candidate_names(player_name: str) -> List[str]:
    full = normalize(player_name)
    parts = full.split()

    candidates = [full]

    if len(parts) >= 2:
        first = parts[0]
        last = parts[-1]

        candidates.extend(
            [
                f"{last}, {first}",
                f"{last.upper()}, {first}",
                f"{last.upper()}, {first.upper()}",
            ]
        )

    seen = set()
    result = []

    for item in candidates:
        item = normalize(item).lower()

        if item and item not in seen:
            seen.add(item)
            result.append(item)

    return result


def safe_text(page, selector: str) -> str:
    try:
        locator = page.locator(selector)

        if locator.count() == 0:
            return ""

        return normalize(locator.first.inner_text())
    except Exception:
        return ""


def is_pre_start(snapshot: dict) -> bool:
    hole = snapshot.get("hole", "")

    start_time = bool(
        re.fullmatch(r"\d{1,2}:\d{2}", hole)
    )

    no_result = all(
        not snapshot.get(field)
        for field in (
            "position",
            "topar",
            "today",
            "r1",
            "r2",
            "total",
        )
    )

    return start_time and no_result


def build_leaderboard_url(source: dict) -> str:
    competition = source["competition"]
    leaderboard = source.get("leaderboard")

    url = (
        f"{GOLFBOX_BASE_URL}"
        f"#/competition/{competition}/leaderboard"
    )

    if leaderboard:
        url += f"/{leaderboard}"

    return url


def fetch_snapshot(watch: dict):
    source = watch["source"]

    player_name = source["player"]
    leaderboard_url = build_leaderboard_url(source)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1600, "height": 1200}
        )

        try:
            page.goto(
                leaderboard_url,
                wait_until="domcontentloaded",
                timeout=120000,
            )

            page.wait_for_timeout(5000)

            if page.get_by_text(
                "Inga resultat ännu",
                exact=False,
            ).count() > 0:
                print(f"{player_name}: inga resultat ännu")
                return None

            candidates = candidate_names(player_name)

            name_cells = page.locator(
                "[id^='list-item-'][id$='-name']"
            )

            for i in range(name_cells.count()):
                name_cell = name_cells.nth(i)

                text = normalize(name_cell.inner_text())
                text_lower = text.lower()

                if not any(
                    candidate in text_lower
                    for candidate in candidates
                ):
                    continue

                element_id = name_cell.get_attribute("id") or ""

                match = re.match(
                    r"list-item-(.+)-name$",
                    element_id,
                )

                if not match:
                    continue

                row_id = match.group(1)

                snapshot = {
                    "position": safe_text(
                        page,
                        f"#list-item-{row_id}-position",
                    ),
                    "name": text,
                    "club": safe_text(
                        page,
                        f"#list-item-{row_id}-club",
                    ),
                    "topar": safe_text(
                        page,
                        f"#list-item-{row_id}-topar",
                    ),
                    "hole": safe_text(
                        page,
                        f"#list-item-{row_id}-hole",
                    ),
                    "today": safe_text(
                        page,
                        f"#list-item-{row_id}-today",
                    ),
                    "r1": safe_text(
                        page,
                        f"#list-item-{row_id}-r1",
                    ),
                    "r2": safe_text(
                        page,
                        f"#list-item-{row_id}-r2",
                    ),
                    "total": safe_text(
                        page,
                        f"#list-item-{row_id}-total",
                    ),
                }

                print(
                    f"{player_name}: hittade GolfBox-rad {row_id}",
                    flush=True,
                )

                if is_pre_start(snapshot):
                    print(
                        f"{player_name}: har inte startat ännu "
                        f"(starttid {snapshot['hole']})",
                        flush=True,
                    )
                    return None

                return snapshot

            print(f"{player_name}: hittade ingen rad")
            return None

        finally:
            browser.close()
