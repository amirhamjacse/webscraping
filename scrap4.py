from playwright.sync_api import sync_playwright
import json
import re

def extract_visible_text_and_urls(url):
    print("[INFO] Launching Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"[INFO] Navigating to: {url}")
        # page.goto(, timeout=90000, wait_until="load")
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_selector("div.card-jfy-title", timeout=30000)  # wait for product titles to appear


        # Wait a bit for rendering
        page.wait_for_timeout(3000)

        # Extract visible text (excluding script/style tags)
        visible_text = page.evaluate("""
            () => {
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                let text = '';
                while (walker.nextNode()) {
                    const value = walker.currentNode.nodeValue.trim();
                    if (value.length > 0) {
                        text += value + '\\n';
                    }
                }
                return text;
            }
        """)

        # Extract all URLs (from a[href], img[src], script[src], link[href], etc.)
        all_urls = page.evaluate("""
            () => {
                const urls = new Set();
                document.querySelectorAll('[href], [src]').forEach(el => {
                    const attr = el.getAttribute('href') || el.getAttribute('src');
                    if (attr && !attr.startsWith('javascript:')) {
                        urls.add(attr);
                    }
                });
                return Array.from(urls);
            }
        """)

        # Save to files
        with open("daraz_visible_text.txt", "w", encoding="utf-8") as f:
            f.write(visible_text)

        with open("daraz_urls.json", "w", encoding="utf-8") as f:
            json.dump(all_urls, f, indent=2)

        print("[SUCCESS] Text and URLs extracted.")
        print("[INFO] Files saved: daraz_visible_text.txt, daraz_urls.json")
        browser.close()

if __name__ == "__main__":
    extract_visible_text_and_urls("https://www.daraz.com.bd/")
