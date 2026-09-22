from datetime import datetime

from bs4 import BeautifulSoup

from techi_audit import (
    parse_date,
    extract_slug,
    extract_title,
    extract_author_handle,
    extract_category,
    parse_article,
)


# ---------------------------------------------------------
# Date tests
# ---------------------------------------------------------

def test_parse_full_date():

    result = parse_date(
        "September 22, 2026"
    )

    assert result == "2026-09-22"


def test_parse_published_date():

    result = parse_date(
        "Published September 22, 2026 · 2:19 AM EDT"
    )

    assert result == "2026-09-22"


def test_parse_updated_date():

    result = parse_date(
        "Updated September 20, 2026"
    )

    assert result == "2026-09-20"


def test_parse_relative_days():

    reference = datetime(
        2026,
        9,
        22
    )

    result = parse_date(
        "3 days ago",
        reference
    )

    assert result == "2026-09-19"


def test_parse_relative_hours():

    reference = datetime(
        2026,
        9,
        22,
        12,
        0
    )

    result = parse_date(
        "5 hours ago",
        reference
    )

    assert result == "2026-09-22"


def test_parse_invalid_date():

    result = parse_date(
        "not a real date"
    )

    assert result == ""


def test_parse_empty_date():

    result = parse_date("")

    assert result == ""


# ---------------------------------------------------------
# Slug tests
# ---------------------------------------------------------

def test_extract_slug():

    url = (
        "https://www.techi.com/"
        "google-gemini-hacked-three-companies-security-test/"
    )

    result = extract_slug(url)

    assert result == (
        "google-gemini-hacked-three-companies-security-test"
    )


def test_extract_slug_without_trailing_slash():

    url = (
        "https://www.techi.com/"
        "some-article"
    )

    result = extract_slug(url)

    assert result == "some-article"


# ---------------------------------------------------------
# Title tests
# ---------------------------------------------------------

def test_extract_title():

    html = """
    <html>
        <head>
            <title>Fallback Title</title>
        </head>
        <body>
            <h1>My Test Article</h1>
        </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    result = extract_title(soup)

    assert result == "My Test Article"


def test_extract_title_from_og():

    html = """
    <html>
        <head>
            <meta
                property="og:title"
                content="OpenGraph Article Title"
            >
        </head>
        <body>
        </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    result = extract_title(soup)

    assert result == "OpenGraph Article Title"


# ---------------------------------------------------------
# Author tests
# ---------------------------------------------------------

def test_extract_author_handle():

    html = """
    <html>
        <body>
            <a
                rel="author"
                href="/@umair-aslam/"
            >
                Umair Aslam
            </a>
        </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    result = extract_author_handle(soup)

    assert result == "umair-aslam"


def test_extract_author_handle_without_author():

    html = """
    <html>
        <body>
            <h1>Article</h1>
        </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    result = extract_author_handle(soup)

    assert result == ""


# ---------------------------------------------------------
# Category tests
# ---------------------------------------------------------

def test_extract_category():

    html = """
    <html>
        <body>
            <a href="/category/technology/">
                Technology
            </a>
        </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    result = extract_category(soup)

    assert result == "Technology"


def test_extract_category_from_meta():

    html = """
    <html>
        <head>
            <meta
                property="article:section"
                content="AI & Intelligence"
            >
        </head>
        <body>
        </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    result = extract_category(soup)

    assert result == "AI & Intelligence"


# ---------------------------------------------------------
# Full article parser test
# ---------------------------------------------------------

def test_parse_article():

    url = (
        "https://www.techi.com/"
        "test-article/"
    )

    html = """
    <html>
        <head>
            <meta
                property="article:section"
                content="Technology"
            >
        </head>

        <body>

            <h1>
                My Test Technology Article
            </h1>

            <a
                rel="author"
                href="/@test-author/"
            >
                Test Author
            </a>

            <time>
                Published September 22, 2026
            </time>

        </body>
    </html>
    """

    article = parse_article(
        url,
        html
    )

    assert article["url"] == url

    assert article["slug"] == "test-article"

    assert (
        article["title"]
        == "My Test Technology Article"
    )

    assert article["category"] == "Technology"

    assert article["author_handle"] == "test-author"

    assert (
        article["date_text"]
        == "Published September 22, 2026"
    )

    assert article["date_iso"] == "2026-09-22"