# NOTES

## Part B — TECHi Article Metadata Reader

### Approach

The scraper starts from `robots.txt` and uses the site's published sitemap to discover article URLs. It processes the WordPress post sitemaps and collects up to 20 unique article URLs.

For each article, the scraper extracts:

* URL
* Slug
* Title
* Category
* Author handle
* Date text
* Normalized ISO date

### Robots.txt Compliance

The scraper reads `robots.txt` before crawling and uses `RobotFileParser.can_fetch()` to determine whether a URL may be requested.

The scraper does not request URLs that are disallowed by the site's robots rules.

### Request Rate

A minimum delay of one second is maintained between HTTP requests.

This is implemented to avoid sending requests too quickly to the website.

### User-Agent

The scraper identifies itself with the following User-Agent:

`TechAboutAssessmentBot/1.0`

### Disk Cache

Downloaded article HTML is stored locally in the `cache/` directory.

Each cached page uses a SHA-256 hash of its URL as the filename.

The cache allows previously downloaded pages to be reused on subsequent runs and reduces unnecessary requests.

The `cache/` directory is excluded from Git through `.gitignore`.

### Error Handling

The scraper handles common request failures gracefully, including:

* Connection/request exceptions
* HTTP 404 responses
* Other non-success HTTP status codes
* Missing article metadata
* Unparseable dates

An individual article failure does not terminate the complete scraping process.

### Date Handling

Article dates are normalized to:

`YYYY-MM-DD`

The date parser supports several formats, including:

* Full dates such as `September 22, 2026`
* Published date strings
* Updated date strings
* ISO date/datetime values
* Relative dates such as `2 days ago`
* Relative times such as `5 hours ago`

Relative dates are calculated using the reference date supplied to the parser.

If a date cannot be parsed reliably, the normalized date field is left empty rather than guessing.

### Metadata Extraction

The scraper uses multiple fallbacks because website HTML structures can change.

#### Title

The title is extracted using the following order:

1. `<h1>`
2. OpenGraph `og:title`
3. HTML `<title>`

#### Category

The category is extracted using:

1. `article:section` metadata
2. Category links
3. JSON-LD `articleSection`

#### Author Handle

The scraper looks for an author link and extracts the handle from the URL when it follows the expected `@handle` format.

If no suitable author handle is found, the field is left empty.

### Article Selection

The assessment requires collecting up to 20 published TECHi articles.

The scraper therefore collects up to 20 unique article URLs discovered from the post sitemaps.

Duplicate URLs are removed before processing.

The scraper does not attempt to crawl the entire website.

### Testing

Offline pytest tests were created for the date parser and article metadata extraction.

The test suite covers:

* Normal dates
* Published dates
* Updated dates
* Relative dates
* Invalid dates
* Empty dates
* Slug extraction
* Title extraction
* Author extraction
* Category extraction
* Complete article parsing

The current test suite contains 16 tests, all of which pass.

### Limitations

The scraper depends on the publicly available HTML structure of TECHi.com. If the website changes its metadata structure, additional extraction rules may be required.

Some articles may not contain every requested metadata field. In such cases, the corresponding CSV field is left empty rather than guessed.

The scraper intentionally avoids private APIs, authentication, credentials, or restricted resources.

No production systems or private data are accessed.

### Scope

This implementation focuses on the requirements of Part B of the asse
