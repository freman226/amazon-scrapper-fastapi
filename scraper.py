from playwright.sync_api import sync_playwright

def scrape_amazon(url: str):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="es-ES",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"
        )
        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("div.s-main-slot")

        cards = page.query_selector_all('div.s-main-slot > div[data-component-type="s-search-result"]')
        for card in cards:
            sponsored_badge = card.query_selector('span[data-component-type="s-status-badge-component"]')
            badge_text = any(
                "Sponsored" in span.inner_text() or "Patrocinado" in span.inner_text()
                for span in card.query_selector_all("span")
            )
            if sponsored_badge or badge_text:
                continue

            attrs = {}
            attr_list = card.evaluate("el => Array.from(el.attributes).map(a => a.name)")
            for attr in attr_list:
                attrs[attr] = card.get_attribute(attr)

            children_text = {}
            for child in card.query_selector_all(":scope > *"):
                tag = child.evaluate("el => el.tagName.toLowerCase()")
                text = child.inner_text().strip()
                if text:
                    children_text[tag] = text

            results.append({
                "attrs": attrs,
                "children_text": children_text,
                "raw_html": card.inner_html()
            })

        browser.close()
    return results
