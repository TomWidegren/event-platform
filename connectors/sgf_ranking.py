from playwright.sync_api import Page

RANKING_URL = "https://golfdata.se/sgfranking/Rankinglista_ind"


def fetch_player_snapshot(page: Page, player_name: str):
    print("SGF: goto", flush=True)
    page.goto(RANKING_URL, wait_until="domcontentloaded", timeout=120000)

    print("SGF: page loaded", flush=True)
    page.wait_for_timeout(3000)

    # Rankinglista
    print("SGF: selecting ranking", flush=True)
    page.locator("select").nth(0).select_option(label="Pojkar (juniorer)")

    # År
    print("SGF: selecting year", flush=True)
    page.locator("select").nth(1).select_option(label="2026")

    # Klubb
    print("SGF: selecting club", flush=True)
    page.locator("select").nth(4).select_option(label="Haninge Golfklubb")

    # Visa listan
    print("SGF: clicking button", flush=True)
    page.get_by_role("button", name="Visa listan").click()
    
    print("SGF: waiting for results", flush=True)
    page.wait_for_timeout(3000)
    
    print("SGF: reading rows", flush=True)
    rows = page.locator("tr")

    for i in range(rows.count()):
        row = rows.nth(i)

        text = row.inner_text().strip()

        if player_name in text:

            cols = [c.strip() for c in text.split("\t")]

            if len(cols) < 8:
                continue

            return {
                "position": cols[0],
                "name": cols[1],
                "birth_year": cols[2],
                "club": cols[3],
                "district": cols[4],
                "status": cols[5],
                "points": cols[6],
                "competitions": cols[7],
            }

    print(f"{player_name}: hittade ingen rankingrad")

    return None
