import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

API = "https://en.wikiquote.org/w/api.php"
HEADERS = {"User-Agent": "QuoteScraperAssignment/1.0 (student project; zeghadaya41@gmail.com)"}
MIN_ROWS = 1000
CATEGORIES = ["Philosophers", "Physicists", "Poets", "Novelists",
              "Scientists", "Politicians", "Writers", "Mathematicians"]


def get_category_pages(category, limit=100):
    """Discover page titles inside a Wikiquote category."""
    params = {"action": "query", "list": "categorymembers",
              "cmtitle": f"Category:{category}", "cmlimit": limit,
              "cmnamespace": 0, "format": "json"}
    r = requests.get(API, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return [m["title"] for m in r.json()["query"]["categorymembers"]]


def fetch_page_html(title):
    params = {"action": "parse", "page": title, "prop": "text",
              "format": "json", "redirects": 1}
    r = requests.get(API, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()["parse"]["text"]["*"]


def extract_quotes(html, author):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for li in soup.select("div.mw-parser-output > ul > li"):
        for sub in li.select("ul"):      # nested lists = citations/sources
            sub.decompose()
        text = li.get_text(" ", strip=True)
        if 30 < len(text) < 500:
            rows.append({"quote": text, "author": author,
                         "source_url": f"https://en.wikiquote.org/wiki/{author.replace(' ', '_')}"})
    return rows


def main():
    all_rows, seen_pages = [], set()

    for cat in CATEGORIES:
        if len(all_rows) >= MIN_ROWS:
            break
        try:
            titles = get_category_pages(cat)
        except Exception as e:
            print(f"[warn] category {cat}: {e}")
            continue
        print(f"[info] category {cat}: {len(titles)} pages found")

        for title in titles:
            if len(all_rows) >= MIN_ROWS:
                break
            if title in seen_pages:
                continue
            seen_pages.add(title)
            try:
                html = fetch_page_html(title)

                # Task 1: display HTML source (first 1000 chars per page)
                print(f"\n===== {title} =====")
                print(html[:1000] + "\n...[truncated]")

                # Task 2: extract quotes
                all_rows += extract_quotes(html, title)
                print(f"[info] total quotes: {len(all_rows)}")
            except Exception as e:
                print(f"[warn] {title}: {e}")
            time.sleep(1)  # be polite

    # Task 3: save with pandas
    df = pd.DataFrame(all_rows).drop_duplicates(subset="quote")
    df.to_csv("quotes.csv", index=False, encoding="utf-8-sig")

    # Task 4: verify row count
    print(f"\n[done] saved {len(df)} rows to quotes.csv")
    if len(df) < MIN_ROWS:
        print("[warn] under 1000 rows, add more categories to CATEGORIES")


if __name__ == "__main__":
    main()