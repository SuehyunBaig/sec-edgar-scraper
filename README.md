# sec-edgar-scraper

A small, standalone project for pulling and cleaning SEC filing data using the public SEC EDGAR full-text search API (EFTS).

## Overview

This project scrapes 10-K filings for a handful of public companies directly from SEC EDGAR, then cleans and normalizes the results into an analysis-ready dataset. It was built as a solo project to practice end-to-end data engineering fundamentals: hitting a real-world API, handling messy/nested JSON, deduplication, type normalization, and structuring a repo the way a production data pipeline would be organized.

## Repository Structure

```
sec-edgar-scraper/
├── scraper/
│   └── sec_edgar_scraper.py   # Ticker → CIK lookup, scraping, cleaning, and save logic
├── data/
│   ├── raw/
│   │   └── filings_raw.csv     # Unprocessed API output
│   └── processed/
│       └── filings_clean.csv   # Deduped, typed, sorted dataset
├── requirements.txt
└── README.md
```

## Data Source

| Source | Type | Notes |
|---|---|---|
| SEC EDGAR (EFTS full-text search API) | 10-K filings | Public API, no auth required — only a descriptive `User-Agent` header |

## Getting Started

### Prerequisites
- Python 3.9+
- pip

### Setup

```bash
git clone https://github.com/<your-username>/sec-edgar-scraper.git
cd sec-edgar-scraper
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python scraper/sec_edgar_scraper.py
```

This will:
1. Look up CIK numbers for the configured list of tickers
2. Pull matching 10-K filings from SEC EDGAR
3. Save raw results to `data/raw/filings_raw.csv`
4. Clean and save the final dataset to `data/processed/filings_clean.csv`

## Workflow

1. **Ticker → CIK lookup** — resolves human-readable tickers (e.g. `AAPL`) to SEC's internal company IDs.
2. **Scrape** — queries the EFTS API per company, filtered by form type, and constructs a direct URL to each filing document.
3. **Clean** — removes duplicate filings, converts date fields to proper datetime types, drops incomplete records, and sorts the output.

## Notes

- Ticker list, form type, and result limits are configurable at the top of `sec_edgar_scraper.py`.
- SEC requests a descriptive `User-Agent` (name + email) on all requests — this is set in the script and should be updated if you fork this project.
- This project scrapes a small, fixed set of tickers by design — it's meant as a focused demonstration of the scrape → clean pipeline, not a production-scale crawler.

## Possible Extensions

- Add unit tests for the parsing/cleaning functions
- Support additional form types (10-Q, 8-K)
- Add basic text extraction from the filing documents themselves
