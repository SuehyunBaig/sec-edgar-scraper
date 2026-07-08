"""
SEC EDGAR Scraper + Cleaner
----------------------------
Pulls 10-K filings for a small list of tickers using the public EFTS
full-text search API, then cleans/normalizes the results into a
ready-to-use dataset.

Usage:
    python sec_edgar_scraper.py

Output:
    data/raw/filings_raw.csv        <- everything the API returned, untouched
    data/processed/filings_clean.csv <- deduped, normalized, analysis-ready

Author: Suehyun Baig
"""

import requests
import pandas as pd
import time
import os

# ---------------------------------------------------------------------------
# CONFIG — edit these to change what gets pulled
# ---------------------------------------------------------------------------

TICKERS = ["AAPL", "MSFT", "TSLA"]   # <-- pick your own handful of tickers
FORM_TYPE = "10-K"
MAX_RESULTS_PER_TICKER = 20

HEADERS = {"User-Agent": "Suehyun Baig suehyun210@gmail.com"}  # SEC requires this

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


# ---------------------------------------------------------------------------
# STEP 1: Ticker -> CIK lookup
# ---------------------------------------------------------------------------

def get_ticker_to_cik_map():
    """
    SEC publishes a single JSON file mapping every ticker to its CIK number.
    We download it once and use it to look up CIKs for our ticker list.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    raw = response.json()

    # raw looks like {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    ticker_to_cik = {}
    for entry in raw.values():
        ticker_to_cik[entry["ticker"].upper()] = str(entry["cik_str"]).zfill(10)

    return ticker_to_cik


# ---------------------------------------------------------------------------
# STEP 2: Scrape filings for one CIK
# ---------------------------------------------------------------------------

def search_filings_for_cik(cik, forms=FORM_TYPE, size=MAX_RESULTS_PER_TICKER):
    """
    Hits the EFTS full-text search API, filtered to a single company (by CIK)
    and a single form type. Returns the raw list of filing hits.
    """
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "forms": forms,
        "ciks": cik,
    }

    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    return data.get("hits", {}).get("hits", [])


# ---------------------------------------------------------------------------
# STEP 3: Build a clean record (and the real document URL) from one hit
# ---------------------------------------------------------------------------

def parse_filing_hit(hit, ticker):
    source = hit["_source"]

    ciks = source.get("ciks", [])
    cik = ciks[0] if ciks else None

    accession_and_file = hit["_id"]
    accession_no, filename = accession_and_file.split(":")
    accession_no_clean = accession_no.replace("-", "")

    doc_url = None
    if cik:
        doc_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{int(cik)}/{accession_no_clean}/{filename}"
        )

    return {
        "ticker": ticker,
        "cik": cik,
        "company_name": source.get("display_names", [None])[0],
        "form": source.get("form"),
        "file_date": source.get("file_date"),
        "period_ending": source.get("period_ending"),
        "accession_no": accession_no,
        "filename": filename,
        "doc_url": doc_url,
    }


# ---------------------------------------------------------------------------
# STEP 4: Scrape everything and save raw output
# ---------------------------------------------------------------------------

def scrape_all_tickers(tickers):
    ticker_to_cik = get_ticker_to_cik_map()
    all_records = []

    for ticker in tickers:
        cik = ticker_to_cik.get(ticker.upper())
        if not cik:
            print(f"[WARN] No CIK found for ticker '{ticker}', skipping.")
            continue

        print(f"Fetching {FORM_TYPE} filings for {ticker} (CIK {cik})...")
        hits = search_filings_for_cik(cik)

        for hit in hits:
            all_records.append(parse_filing_hit(hit, ticker))

        time.sleep(0.2)  # be polite to SEC's servers (rate-limit friendly)

    return pd.DataFrame(all_records)


# ---------------------------------------------------------------------------
# STEP 5: Clean the raw data
# ---------------------------------------------------------------------------

def clean_filings(df):
    """
    - Removes duplicate filings (same accession number)
    - Converts date columns to proper datetime type
    - Drops rows with no usable document URL
    - Sorts by ticker and filing date
    """
    df = df.drop_duplicates(subset=["accession_no", "filename"])
    df = df.dropna(subset=["doc_url"])

    df["file_date"] = pd.to_datetime(df["file_date"], errors="coerce")
    df["period_ending"] = pd.to_datetime(df["period_ending"], errors="coerce")

    df = df.sort_values(["ticker", "file_date"], ascending=[True, False])
    df = df.reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    raw_df = scrape_all_tickers(TICKERS)
    raw_path = os.path.join(RAW_DIR, "filings_raw.csv")
    raw_df.to_csv(raw_path, index=False)
    print(f"\nSaved {len(raw_df)} raw records to {raw_path}")

    clean_df = clean_filings(raw_df)
    clean_path = os.path.join(PROCESSED_DIR, "filings_clean.csv")
    clean_df.to_csv(clean_path, index=False)
    print(f"Saved {len(clean_df)} cleaned records to {clean_path}")


if __name__ == "__main__":
    main()