import os
import re
import json
import time
import argparse
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright


def is_internal_link(base_url, link):
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    return link_domain == "" or link_domain == base_domain


def safe_filename(url):
    parsed = urlparse(url)
    path = parsed.path if parsed.path else "root"
    filename = re.sub(r'[^a-zA-Z0-9]', '_', parsed.netloc + path)
    return filename.strip('_')[:150] or "root"


def crawl_site(start_url, max_pages=30, delay_seconds=3, optional_selector=None,
               exclude_extensions=None, user_agent=None):

    if exclude_extensions is None:
        exclude_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.zip', '.rar', '.exe', '.svg', '.mp4']

    if user_agent is None:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"

    visited = set()
    to_visit = [start_url]
    output_folder = "crawled_pages"
    os.makedirs(output_folder, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent, locale='en-US', java_script_enabled=True)
        page = context.new_page()

        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue

            print(f"[INFO] Visiting: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                if optional_selector:
                    try:
                        page.wait_for_selector(optional_selector, timeout=15000)
                    except:
                        print("[WARNING] Optional selector not found, continuing.")

                page.wait_for_load_state("networkidle")
                time.sleep(delay_seconds)

                visible_text = page.evaluate("""
                    () => {
                        function isVisible(elem) {
                            if (!elem) return false;
                            const style = window.getComputedStyle(elem);
                            return style && style.visibility !== 'hidden' && style.display !== 'none' && elem.offsetParent !== null;
                        }
                        function looksLikeJS(line) {
                            const jsKeywords = ['var ', 'function(', 'function ', '=', '{', '}', ';', '//', '/*', '=>', 'const ', 'let ', 'import ', 'export '];
                            return jsKeywords.some(keyword => line.includes(keyword));
                        }
                        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                        let text = '';
                        while (walker.nextNode()) {
                            const node = walker.currentNode;
                            const line = node.nodeValue.trim();
                            if (line.length > 0 && isVisible(node.parentElement) && !looksLikeJS(line)) {
                                text += line + '\\n';
                            }
                        }
                        return text;
                    }
                """)

                print(f"[DEBUG] Extracted {len(visible_text)} characters")

                page_urls = page.evaluate(f"""
                    () => {{
                        const urls = new Set();
                        document.querySelectorAll('a[href]').forEach(el => {{
                            const href = el.getAttribute('href');
                            if (href && !href.startsWith('javascript:') && !href.startsWith('#')) {{
                                try {{
                                    const absUrl = new URL(href, "{url}").href;
                                    urls.add(absUrl);
                                }} catch (e) {{}}
                            }}
                        }});
                        return Array.from(urls);
                    }}
                """)

                filename = safe_filename(url)
                with open(os.path.join(output_folder, f"{filename}_text.txt"), "w", encoding="utf-8") as f_text:
                    f_text.write(visible_text)

                with open(os.path.join(output_folder, f"{filename}_urls.json"), "w", encoding="utf-8") as f_urls:
                    json.dump(page_urls, f_urls, indent=2, ensure_ascii=False)

                visited.add(url)

                for link in page_urls:
                    if (
                        is_internal_link(start_url, link)
                        and link not in visited
                        and link not in to_visit
                        and not any(link.lower().endswith(ext) for ext in exclude_extensions)
                    ):
                        to_visit.append(link)

            except Exception as e:
                print(f"[ERROR] Failed to load {url}: {e}")
                visited.add(url)

        browser.close()
    print(f"[DONE] Crawled {len(visited)} pages. Output saved to '{output_folder}'")


# Entry point with CLI support
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Playwright Web Crawler")
    parser.add_argument("--url", type=str, required=True, help="Start URL to crawl")
    parser.add_argument("--max", type=int, default=30, help="Max pages to crawl")
    parser.add_argument("--delay", type=int, default=3, help="Delay in seconds between pages")
    parser.add_argument("--selector", type=str, default=None, help="Optional CSS selector to wait for")
    args = parser.parse_args()

    crawl_site(
        start_url=args.url,
        max_pages=args.max,
        delay_seconds=args.delay,
        optional_selector=args.selector,
    )
