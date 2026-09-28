from playwright.sync_api import sync_playwright

RANKING_URL = "https://golfdata.se/sgfranking/Rankinglista_ind"


def fetch_snapshot(watch: dict):
    source = watch["source"]

    player_name = source["player"]
    ranking = source["ranking"]
    year = str(source["year"])
    club = source["club"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})

        try:
            page.goto(
                RANKING_URL,
                wait_until="domcontentloaded",
                timeout=120000,
            )
            page.wait_for_timeout(3000)

            # Rankinglista
            page.locator("select").nth(0).select_option(label=ranking)

            # År
            page.locator("select").nth(1).select_option(label=year)

            # Klubb
            page.locator("select").nth(4).select_option(label=club)

            # Visa listan
            page.get_by_role("button", name="Visa listan").click()
            page.wait_for_timeout(3000)

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

        finally:
            browser.close()
