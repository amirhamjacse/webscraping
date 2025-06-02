from playwright.sync_api import sync_playwright
import time
import sys

# ANSI colors for logs
class Log:
    INFO = "\033[94m[INFO]\033[0m"
    SUCCESS = "\033[92m[SUCCESS]\033[0m"
    WARNING = "\033[93m[WARNING]\033[0m"
    ERROR = "\033[91m[ERROR]\033[0m"

def stealthy_scrape(url):
    print(f"{Log.INFO} Starting Playwright stealth scraper...")
    
    with sync_playwright() as p:
        print(f"{Log.INFO} Launching Chromium browser...")

        browser = p.chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-gpu"
        ])

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1280, "height": 720}
        )

        context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not=A?Brand";v="99"',
            "Sec-Ch-Ua-Platform": '"Windows"',
        })

        page = context.new_page()

        try:
            print(f"{Log.INFO} Navigating to {url}")
            page.goto(url, timeout=90000, wait_until="domcontentloaded")

            print(f"{Log.INFO} Waiting for page scripts to complete rendering...")
            time.sleep(3)

            title = page.title()
            print(f"{Log.SUCCESS} Page loaded: \033[1m{title}\033[0m")

            with open("daraz.html", "w", encoding="utf-8") as f:
                f.write(page.content())
                print(f"{Log.SUCCESS} HTML content saved as: daraz.html")

            page.screenshot(path="daraz_screenshot.png", full_page=True)
            print(f"{Log.SUCCESS} Screenshot saved as: daraz_screenshot.png")

        except Exception as e:
            print(f"{Log.ERROR} Failed to scrape: {e}")
        finally:
            browser.close()
            print(f"{Log.INFO} Browser closed. Scraping finished.\n")

if __name__ == "__main__":
    target_url = "https://daraz.com.bd/"
    stealthy_scrape(target_url)
