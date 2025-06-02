from playwright.sync_api import sync_playwright
import json
import time

def scrape_daraz_products(url):
    print("[INFO] Starting Playwright stealth scraper...")

    with sync_playwright() as p:
        print("[INFO] Launching Chromium browser...")
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"[INFO] Navigating to {url}")
        page.goto(url, timeout=90000, wait_until="domcontentloaded")

        print("[INFO] Waiting for page to render fully...")
        time.sleep(5)

        product_cards = page.query_selector_all("div.card-jfy-item-desc")
        print(f"[INFO] Found {len(product_cards)} product cards.")

        products = []

        for card in product_cards:
            try:
                title = card.query_selector("div.card-jfy-title").inner_text().strip()
                price = card.query_selector("span.price").inner_text().strip()
                discount_elem = card.query_selector("span.hp-mod-discount")
                discount = discount_elem.inner_text().strip() if discount_elem else "N/A"

                rating_layer = card.query_selector("div.card-jfy-rating-layer.top-layer")
                rating_style = rating_layer.get_attribute("style") if rating_layer else "width: 0%;"
                rating_percent = rating_style.replace("width:", "").replace(";", "").strip()

                comments_elem = card.query_selector("div.card-jfy-ratings-comment")
                comments = comments_elem.inner_text().strip() if comments_elem else "(0)"

                products.append({
                    "title": title,
                    "price": f"৳{price}",
                    "discount": discount,
                    "rating": rating_percent,
                    "comments": comments
                })
            except Exception as e:
                print(f"[ERROR] Failed to extract a product card: {e}")

        with open("daraz_products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] {len(products)} products extracted and saved to daraz_products.json")
        page.screenshot(path="daraz_screenshot.png", full_page=True)
        print("[SUCCESS] Screenshot saved as daraz_screenshot.png")

        browser.close()
        print("[INFO] Browser closed. Done.")

if __name__ == "__main__":
    scrape_daraz_products("https://www.daraz.com.bd/")
