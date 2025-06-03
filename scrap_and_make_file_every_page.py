from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json
import time
import os
import re

def is_internal_link(base_url, link):
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    return (link_domain == "" or link_domain == base_domain)

def safe_filename(url):
    parsed = urlparse(url)
    path = parsed.path if parsed.path else "root"
    # Replace all non-alphanumeric characters with underscores
    filename = re.sub(r'[^a-zA-Z0-9]', '_', parsed.netloc + path)
    return filename.strip('_')[:150] or "root"

def crawl_site(start_url, max_pages=30):
    visited = set()
    to_visit = [start_url]

    output_folder = "crawled_pages"
    os.makedirs(output_folder, exist_ok=True)

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

                try:
                    page.wait_for_selector("div.card-jfy-title", timeout=15000)
                except:
                    print("[WARNING] Selector not found, continuing anyway.")

                time.sleep(3)  # wait for dynamic content

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
                        while(walker.nextNode()) {
                            const node = walker.currentNode;
                            const line = node.nodeValue.trim();
                            if (line.length > 0 && isVisible(node.parentElement) && !looksLikeJS(line)) {
                                text += line + '\\n';
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

                # Save visible text and URLs for this page
                filename = safe_filename(url)
                text_file = os.path.join(output_folder, f"{filename}_text.txt")
                urls_file = os.path.join(output_folder, f"{filename}_urls.json")

                with open(text_file, "w", encoding="utf-8") as f_text:
                    f_text.write(visible_text)

                with open(urls_file, "w", encoding="utf-8") as f_urls:
                    json.dump(page_urls, f_urls, indent=2, ensure_ascii=False)

                print(f"[INFO] Saved data for {url}")

                visited.add(url)

                # Add new internal links
                for link in page_urls:
                    if is_internal_link(start_url, link) and link not in visited and link not in to_visit:
                        to_visit.append(link)

            except Exception as e:
                print(f"[ERROR] Failed to load {url}: {e}")
                visited.add(url)

        browser.close()

    print(f"[DONE] Crawled {len(visited)} pages. Data saved in folder '{output_folder}'.")

if __name__ == "__main__":
    crawl_site("https://www.daraz.com.bd/", max_pages=30)
