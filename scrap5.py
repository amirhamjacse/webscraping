from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json
import time

def is_internal_link(base_url, link):
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    return (link_domain == "" or link_domain == base_domain)

def crawl_site(start_url, max_pages=30):
    visited = set()
    to_visit = [start_url]
    all_text = {}
    all_urls = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
            locale='en-US',
            java_script_enabled=True,
        )
        page = context.new_page()

        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue

            print(f"[INFO] Visiting: {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Wait for a key selector (adjust as per site)
                try:
                    page.wait_for_selector("div.card-jfy-title", timeout=15000)
                except:
                    print("[WARNING] Selector not found, continuing anyway.")

                time.sleep(3)  # wait for dynamic content

                visible_text = page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                        let text = '';
                        while(walker.nextNode()) {
                            const node = walker.currentNode;
                            if(node.nodeValue.trim().length > 0) {
                                text += node.nodeValue.trim() + '\\n';
                            }
                        }
                        return text;
                    }
                """)

                print(f"[DEBUG] Extracted {len(visible_text)} chars of visible text from {url}")

                page_urls = page.evaluate(f"""
                    () => {{
                        const urls = new Set();
                        document.querySelectorAll('a[href]').forEach(el => {{
                            const href = el.getAttribute('href');
                            if(href && !href.startsWith('javascript:')) {{
                                try {{
                                    const absUrl = new URL(href, "{url}").href;
                                    urls.add(absUrl);
                                }} catch(e) {{}}
                            }}
                        }});
                        return Array.from(urls);
                    }}
                """)

                all_text[url] = visible_text
                all_urls[url] = page_urls
                visited.add(url)

                for link in page_urls:
                    if is_internal_link(start_url, link) and link not in visited and link not in to_visit:
                        to_visit.append(link)

            except Exception as e:
                print(f"[ERROR] Failed to load {url}: {e}")
                visited.add(url)

        browser.close()

    with open("site_texts.json", "w", encoding="utf-8") as f:
        json.dump(all_text, f, indent=2, ensure_ascii=False)

    with open("site_urls.json", "w", encoding="utf-8") as f:
        json.dump(all_urls, f, indent=2, ensure_ascii=False)

    print(f"[DONE] Crawled {len(visited)} pages.")

if __name__ == "__main__":
    crawl_site("https://www.daraz.com.bd/", max_pages=30)
