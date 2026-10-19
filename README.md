# Web Crawler

An asynchronous Python web crawler that stays within the starting website's
domain, extracts useful page metadata, and saves the results as JSON.

## Features

- Crawls pages asynchronously with configurable concurrency.
- Limits the total number of pages visited.
- Extracts the first `h1` or `h2` heading.
- Extracts the first paragraph, prioritizing paragraphs inside `<main>`.
- Collects outgoing links and image URLs.
- Resolves relative links and image paths to absolute URLs.
- Writes a sorted JSON report to `report.json`.

## Requirements

- Python 3.14 or newer
- [`uv`](https://docs.astral.sh/uv/) for dependency and environment management

The project depends on:

- [aiohttp](https://docs.aiohttp.org/) for asynchronous HTTP requests
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) for HTML parsing
- [Requests](https://requests.readthedocs.io/) for HTTP tooling

## Installation

Clone the repository and install its locked dependencies:

```bash
git clone https://github.com/abdellatifmht/Web-Crawler.git
cd Web-Crawler
uv sync
```

If you do not use `uv`, create a Python 3.14 virtual environment and install
the dependencies listed in `pyproject.toml`:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install aiohttp==3.12.12 beautifulsoup4==4.13.4 requests==2.32.4
```

## Usage

Run the crawler with a starting URL, maximum concurrency, and maximum number of
pages:

```bash
uv run python main.py <url> <max-concurrency> <max-pages>
```

Example:

```bash
uv run python main.py https://example.com 5 20
```

The crawler prints progress to the terminal and creates `report.json` in the
project root. The report contains one object per successfully fetched page:

```json
[
  {
    "url": "https://example.com",
    "heading": "Example Domain",
    "first_paragraph": "This domain is for use in illustrative examples...",
    "outgoing_links": [],
    "image_urls": []
  }
]
```

Only links on the starting URL's domain are crawled. Links and images found on
each page are still included in that page's extracted data, even when they
point to another domain.

## Running the tests

Run the test suite with:

```bash
uv run python -m unittest
```

## Project structure

| File | Description |
| --- | --- |
| `main.py` | Command-line entry point |
| `crawl.py` | Crawler, URL normalization, fetching, and HTML extraction |
| `json_report.py` | JSON report writer |
| `test_crawl.py` | Unit tests for URL and HTML extraction behavior |
| `pyproject.toml` | Project metadata and dependencies |
| `uv.lock` | Locked dependency versions |

## Publishing to GitHub

Create an empty repository on GitHub, then connect this local repository and
push the current branch:

```bash
git remote add origin https://github.com/<your-username>/Web-Crawler.git
git add .
git commit -m "Document project usage"
git push -u origin crawl
```

If your GitHub repository should use `main` as its default branch instead:

```bash
git branch -M main
git push -u origin main
```

Do not commit local virtual environments, Python cache files, or generated
reports; these are excluded by `.gitignore`.

## License

No license has been specified yet. Add a `LICENSE` file before distributing
this project if you want to grant others explicit rights to use, modify, or
redistribute it.
