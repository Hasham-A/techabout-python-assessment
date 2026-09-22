# TechAbout Python Developer Assessment

This repository contains my solution for the TechAbout Python Developer assessment.

The assessment contains two parts:

* Part A — PKHosting renewals data cleaning
* Part B — TECHi article metadata reader

---

# Requirements

* Python 3.10+
* Free/open-source Python libraries only
* No credentials or paid services

## Dependencies

Install the required packages with:

```bash
pip install -r requirements.txt
```

The project uses:

* `requests` — HTTP requests
* `beautifulsoup4` — HTML/XML parsing
* `lxml` — XML parsing backend
* `pytest` — automated tests

---

# Part B — TECHi Article Metadata Reader

## Overview

`techi_audit.py` discovers published TECHi article URLs through the site's `robots.txt` and sitemap structure, then collects metadata for up to 20 articles.

The output is written to:

```text
techi_articles.csv
```

## Output fields

The CSV contains:

```text
url
slug
title
category
author_handle
date_text
date_iso
```

### Field descriptions

| Field           | Description                            |
| --------------- | -------------------------------------- |
| `url`           | Article URL                            |
| `slug`          | Final URL path component               |
| `title`         | Article title                          |
| `category`      | Article category                       |
| `author_handle` | Author handle without `@`              |
| `date_text`     | Date text extracted from the article   |
| `date_iso`      | Normalized date in `YYYY-MM-DD` format |

## Running the scraper

From the project root:

```bash
python techi_audit.py
```

The scraper:

1. Reads `robots.txt`
2. Finds the site's sitemap
3. Discovers `post-sitemap` files
4. Extracts article URLs
5. Selects up to 20 unique URLs
6. Checks robots permissions
7. Uses cached HTML when available
8. Downloads uncached articles at a controlled rate
9. Extracts article metadata
10. Writes `techi_articles.csv`

## Polite crawling

The scraper uses the following measures:

* Identifying User-Agent
* `robots.txt` compliance
* Minimum one-second request delay
* Local disk caching
* Limited scope of 20 articles
* Graceful handling of request failures

---

# Testing

Tests are located in:

```text
tests/test_techi_audit.py
```

Run them with:

```bash
python -m pytest -v
```

Current test result:

```text
16 passed
```

The tests are offline and do not require network access.

---

# Part A — PKHosting Renewals

Part A depends on the supplied:

```text
renewals_raw.csv
```

The assessment brief refers to a 34-record input CSV. At the time of implementation, that input file was not available on the assessment page.

Therefore, the missing input data was not fabricated.

Once the supplied `renewals_raw.csv` is available, Part A will produce:

```text
clean.csv
issues.csv
```

and the corresponding cleaning script:

```text
clean.py
```

The cleaning logic will document decisions around:

* Dates
* Money values
* Domains
* Duplicates
* Ambiguous records
* Invalid records

---

# Project Structure

```text
techabout-assessment/
│
├── techi_audit.py
├── techi_articles.csv
│
├── tests/
│   ├── __init__.py
│   └── test_techi_audit.py
│
├── cache/
│
├── requirements.txt
├── NOTES.md
│
├── renewals_raw.csv
├── clean.py
├── clean.csv
└── issues.csv
```

The Part A files are dependent on the supplied assessment input.

---

# Design Decisions

The implementation favors explicit parsing and graceful failure over assumptions about every possible page structure.

For article metadata, multiple extraction fallbacks are used where practical because website HTML can vary between pages.

The scraper does not use private endpoints, authentication, or paid services.
