import csv
import hashlib
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BASE_URL = "https://www.techi.com/"
ROBOTS_URL = urljoin(BASE_URL, "robots.txt")

USER_AGENT = "TechAboutAssessmentBot/1.0"

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

REQUEST_DELAY = 1.0
TIMEOUT = 15

HEADERS = {
    "User-Agent": USER_AGENT
}

last_request_time = 0.0


# ---------------------------------------------------------
# 1. MAKE A POLITE HTTP REQUEST
# ---------------------------------------------------------

def polite_get(session, url):
    global last_request_time

    elapsed = time.monotonic() - last_request_time

    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)

    try:
        response = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        last_request_time = time.monotonic()

        return response

    except requests.RequestException as exc:
        print(f"[WARN] Request failed: {url} -> {exc}")
        return None


# ---------------------------------------------------------
# 2. READ ROBOTS.TXT
# ---------------------------------------------------------

def load_robots(session):
    response = polite_get(session, ROBOTS_URL)

    if response is None:
        return None

    if response.status_code != 200:
        print(
            f"[WARN] robots.txt returned HTTP "
            f"{response.status_code}"
        )
        return None

    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.parse(response.text.splitlines())

    return parser, response.text


# ---------------------------------------------------------
# 3. FIND SITEMAP URL INSIDE ROBOTS.TXT
# ---------------------------------------------------------

def extract_sitemap_url(robots_text):
    for line in robots_text.splitlines():

        line = line.strip()

        if line.lower().startswith("sitemap:"):
            return line.split(":", 1)[1].strip()

    return None


# ---------------------------------------------------------
# 4. DOWNLOAD A SITEMAP
# ---------------------------------------------------------

def fetch_sitemap(session, sitemap_url):
    response = polite_get(session, sitemap_url)

    if response is None:
        return None

    if response.status_code != 200:
        print(
            f"[WARN] Sitemap returned HTTP "
            f"{response.status_code}"
        )
        return None

    return response.text


# ---------------------------------------------------------
# 5. EXTRACT LINKS FROM A SITEMAP
# ---------------------------------------------------------

def extract_sitemap_links(xml_text):
    soup = BeautifulSoup(xml_text, "xml")

    links = []

    for loc in soup.find_all("loc"):
        links.append(loc.get_text(strip=True))

    return links


# ---------------------------------------------------------
# 6. FIND ARTICLE SITEMAPS
# ---------------------------------------------------------

def find_article_sitemaps(sitemap_links):
    article_sitemaps = []

    for url in sitemap_links:

        if "/post-sitemap" in url.lower():
            article_sitemaps.append(url)

    return article_sitemaps

# ---------------------------------------------------------
# 7. EXTRACT ARTICLE URLS
# ---------------------------------------------------------

def extract_article_urls(xml_text):
    soup = BeautifulSoup(xml_text, "xml")
    urls = []

    for loc in soup.find_all("loc"):
        url = loc.get_text(strip=True)

        # Only keep normal webpage URLs.
        # Ignore images, API files, feeds, etc.
        if not url.startswith(BASE_URL):
            continue

        path = url.replace(BASE_URL, "", 1)

        if path.startswith("api/"):
            continue

        if any(path.lower().endswith(extension) for extension in [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
            ".pdf"
        ]):
            continue

        urls.append(url)

    return urls

# ---------------------------------------------------------
# 8. CHECK ROBOTS PERMISSION
# ---------------------------------------------------------

def allowed_by_robots(robots_parser, url):
    return robots_parser.can_fetch(
        USER_AGENT,
        url
    )


# ---------------------------------------------------------
# 9. CREATE CACHE FILE NAME
# ---------------------------------------------------------

def cache_path(url):
    url_hash = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()

    return CACHE_DIR / f"{url_hash}.html"


# ---------------------------------------------------------
# 10. GET ARTICLE HTML
# ---------------------------------------------------------

def get_article_html(session, robots_parser, url):

    # Check robots.txt first
    if not allowed_by_robots(
        robots_parser,
        url
    ):
        print(f"[ROBOTS] Blocked: {url}")
        return None

    # Work out where cached HTML should live
    path = cache_path(url)

    # Use cached HTML if available
    if path.exists():

        print(f"[CACHE] {url}")

        return path.read_text(
            encoding="utf-8"
        )

    # Otherwise download the page
    response = polite_get(
        session,
        url
    )

    if response is None:
        return None

    # Handle 404
    if response.status_code == 404:

        print(f"[404] {url}")

        return None

    # Handle other HTTP errors
    if response.status_code != 200:

        print(
            f"[WARN] HTTP "
            f"{response.status_code}: {url}"
        )

        return None

    # Get HTML
    html = response.text

    # Save HTML to cache
    path.write_text(
        html,
        encoding="utf-8"
    )

    print(f"[DOWNLOADED] {url}")

    return html


# ---------------------------------------------------------
# 11. GET SLUG FROM URL
# ---------------------------------------------------------

def extract_slug(url):

    url = url.rstrip("/")

    return url.split("/")[-1]


# ---------------------------------------------------------
# 12. EXTRACT TITLE
# ---------------------------------------------------------

def extract_title(soup):

    # First try the main H1
    heading = soup.find("h1")

    if heading:
        title = heading.get_text(
            " ",
            strip=True
        )

        if title:
            return title

    # Fallback: Open Graph title
    meta = soup.find(
        "meta",
        property="og:title"
    )

    if meta and meta.get("content"):
        return meta["content"].strip()

    # Final fallback: HTML title
    if soup.title:
        return soup.title.get_text(
            " ",
            strip=True
        )

    return ""


# ---------------------------------------------------------
# 13. EXTRACT CATEGORY
# ---------------------------------------------------------

def extract_category(soup):
    """
    Extract article category from common WordPress metadata.
    """

    # 1. Try article:section metadata
    meta_category = soup.find(
        "meta",
        attrs={"property": "article:section"}
    )

    if meta_category:
        content = meta_category.get("content", "").strip()

        if content:
            return content

    # 2. Try category links
    for link in soup.find_all("a", href=True):

        href = link.get("href", "").lower()

        if "/category/" in href:

            category = link.get_text(
                " ",
                strip=True
            )

            if category:
                return category

    # 3. Try JSON-LD articleSection
    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        text = script.get_text(
            " ",
            strip=True
        )

        match = re.search(
            r'"articleSection"\s*:\s*"([^"]+)"',
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return ""


# ---------------------------------------------------------
# 14. EXTRACT AUTHOR HANDLE
# ---------------------------------------------------------

def extract_author_handle(soup):
    author_link = soup.find("a", rel="author")

    if author_link:
        href = author_link.get("href", "")
        handle = href.rstrip("/").split("/")[-1]

        if handle.startswith("@"):
            return handle[1:]

    return ""

# ---------------------------------------------------------
# 15. EXTRACT DATE TEXT
# ---------------------------------------------------------

def extract_date_text(soup):

    # Check time element first
    time_element = soup.find("time")

    if time_element:

        text = time_element.get_text(
            " ",
            strip=True
        )

        if text:
            return text

        if time_element.get("datetime"):
            return time_element["datetime"]

    # Search meta tags
    for property_name in [
        "article:published_time",
        "article:modified_time"
    ]:

        meta = soup.find(
            "meta",
            property=property_name
        )

        if meta and meta.get("content"):
            return meta["content"].strip()

    # Fallback: search visible page text
    text = soup.get_text(
        " ",
        strip=True
    )

    patterns = [
        r"Updated\s+\d+\s+(?:day|days|hour|hours|minute|minutes)\s+ago",
        r"Published\s+\d+\s+(?:day|days|hour|hours|minute|minutes)\s+ago",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(0)

    return ""


# ---------------------------------------------------------
# 16. CONVERT DATE TO ISO FORMAT
# ---------------------------------------------------------

def parse_date(date_text, reference_date=None):
    if not date_text:
        return ""

    if reference_date is None:
        reference_date = datetime.now()

    cleaned = date_text.strip()

    # Remove Published/Updated prefix
    cleaned = re.sub(
        r"^(Published|Updated)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    # Handle relative dates such as:
    # "6 days ago"
    # "1 day ago"
    match = re.fullmatch(
        r"(\d+)\s+(day|days)\s+ago",
        cleaned,
        flags=re.IGNORECASE
    )

    if match:
        days = int(match.group(1))
        result = reference_date - timedelta(days=days)
        return result.date().isoformat()

    # Handle hours ago
    match = re.fullmatch(
        r"(\d+)\s+(hour|hours)\s+ago",
        cleaned,
        flags=re.IGNORECASE
    )

    if match:
        hours = int(match.group(1))
        result = reference_date - timedelta(hours=hours)
        return result.date().isoformat()

    # Remove time and timezone after the date.
    # Example:
    # September 22, 2026 · 2:19 AM EDT
    # becomes:
    # September 22, 2026
    match = re.search(
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        cleaned
    )

    if match:
        cleaned = match.group(1)

    formats = [
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for date_format in formats:
        try:
            result = datetime.strptime(cleaned, date_format)
            return result.date().isoformat()
        except ValueError:
            continue

    return ""


# ---------------------------------------------------------
# 17. EXTRACT ALL ARTICLE DATA
# ---------------------------------------------------------

def parse_article(url, html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    date_text = extract_date_text(soup)

    article = {
        "url": url,
        "slug": extract_slug(url),
        "title": extract_title(soup),
        "category": extract_category(soup),
        "author_handle": extract_author_handle(soup),
        "date_text": date_text,
        "date_iso": parse_date(date_text),
    }

    return article


# ---------------------------------------------------------
# 18. SAVE CSV
# ---------------------------------------------------------

def save_csv(rows, filename):

    fieldnames = [
        "url",
        "slug",
        "title",
        "category",
        "author_handle",
        "date_text",
        "date_iso",
    ]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)


# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------

def main():

    session = requests.Session()

    # ---------------------------------------------
    # STEP 1: READ ROBOTS.TXT
    # ---------------------------------------------

    result = load_robots(session)

    if result is None:
        raise SystemExit(
            "Could not load robots.txt"
        )

    robots_parser, robots_text = result

    # ---------------------------------------------
    # STEP 2: FIND SITEMAP
    # ---------------------------------------------

    sitemap_url = extract_sitemap_url(
        robots_text
    )

    if not sitemap_url:
        raise SystemExit(
            "No sitemap found in robots.txt"
        )

    print(
        f"Sitemap: {sitemap_url}"
    )

    # ---------------------------------------------
    # STEP 3: DOWNLOAD SITEMAP INDEX
    # ---------------------------------------------

    sitemap_text = fetch_sitemap(
        session,
        sitemap_url
    )

    if sitemap_text is None:
        raise SystemExit(
            "Could not load sitemap"
        )

    # ---------------------------------------------
    # STEP 4: FIND ARTICLE SITEMAPS
    # ---------------------------------------------

    sitemap_links = extract_sitemap_links(
        sitemap_text
    )
    print("\nAll sitemap links discovered:")

    for link in sitemap_links:
        print(link)

    article_sitemaps = find_article_sitemaps(
        sitemap_links
    )

    print(
        f"Article sitemaps found: "
        f"{len(article_sitemaps)}"
    )

    # ---------------------------------------------
    # STEP 5: GET ARTICLE URLS
    # ---------------------------------------------

    article_urls = []

    for article_sitemap in article_sitemaps:

        print(
            f"Reading: {article_sitemap}"
        )

        article_sitemap_text = fetch_sitemap(
            session,
            article_sitemap
        )

        if article_sitemap_text is None:
            continue

        urls = extract_article_urls(
            article_sitemap_text
        )

        article_urls.extend(urls)

    # Remove duplicate URLs
    article_urls = list(
        dict.fromkeys(article_urls)
    )

    # Requirement: maximum 20
    article_urls = article_urls[:20]

    print(
        f"Article URLs selected: "
        f"{len(article_urls)}"
    )

    # ---------------------------------------------
    # STEP 6: DOWNLOAD + PARSE ARTICLES
    # ---------------------------------------------

    articles = []

    for index, url in enumerate(
        article_urls,
        start=1
    ):

        print(
            f"\n[{index}/{len(article_urls)}] "
            f"{url}"
        )

        html = get_article_html(
            session,
            robots_parser,
            url
        )

        if html is None:
            continue

        try:

            article = parse_article(
                url,
                html
            )

            articles.append(article)

            print(
                f"Title: {article['title']}"
            )

            print(
                f"Category: "
                f"{article['category']}"
            )

            print(
                f"Author: "
                f"{article['author_handle']}"
            )

            print(
                f"Date: "
                f"{article['date_text']}"
            )

            print(
                f"ISO date: "
                f"{article['date_iso']}"
            )

        except Exception as exc:

            print(
                f"[WARN] Could not parse "
                f"{url}: {exc}"
            )

    # ---------------------------------------------
    # STEP 7: SAVE CSV
    # ---------------------------------------------

    save_csv(
        articles,
        "techi_articles.csv"
    )

    print(
        f"\nSaved {len(articles)} articles "
        f"to techi_articles.csv"
    )


if __name__ == "__main__":
    main()