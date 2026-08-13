"""
download_live_dataset.py — builds a labeled URL dataset from two live,
independently-maintained, no-registration-required threat intelligence
feeds:

  - URLhaus (abuse.ch): currently-active malicious URLs, updated every
    5 minutes. https://urlhaus.abuse.ch/downloads/csv_online/
  - Tranco: a research-grade top-domains ranking, purpose-built as the
    academic replacement for the discontinued Alexa Top 1M (used by
    URLhaus itself, and cited in 600+ academic papers).
    https://tranco-list.eu/top-1m.csv.zip

This is a stronger methodology than a single static CSV: both sources
are live and independently reputable, closely matching the
PhishTank/Alexa/URLhaus combination originally documented for this
project (Tranco stands in for the now-discontinued Alexa list).

IMPORTANT: this script could not be end-to-end network-tested in the
environment that built it (sandboxed network access doesn't reach
abuse.ch or tranco-list.eu). The CSV parsing logic was verified against
real sample rows from both sources' documented formats, but the live
HTTP requests themselves have not been executed. Run this yourself and
report back if either download fails — the fix is almost certainly a
small format change on their end, not a logic error.

Usage:
    python download_live_dataset.py --out datasets/urls_labeled_live.csv --max-per-class 3000
"""

import argparse
import csv
import io
import random
import sys
import zipfile
from pathlib import Path

import requests

URLHAUS_URL = "https://urlhaus.abuse.ch/downloads/csv_online/"
TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"


def download_malicious(timeout: float = 30.0) -> list[str]:
    print(f"Downloading URLhaus (currently-active malicious URLs) from {URLHAUS_URL} ...")
    try:
        resp = requests.get(URLHAUS_URL, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: could not download URLhaus feed ({e})", file=sys.stderr)
        sys.exit(1)

    text = resp.content.decode("utf-8", errors="replace")

    # URLhaus CSVs lead with several '#' comment lines before the real
    # header row (id,dateadded,url,url_status,threat,tags,urlhaus_link,reporter)
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    reader = csv.reader(lines)

    urls = []
    for row in reader:
        if len(row) < 3:
            continue
        url = row[2].strip().strip('"')
        if url and url.startswith(("http://", "https://")):
            urls.append(url)

    print(f"Parsed {len(urls):,} malicious URLs from URLhaus")
    return urls


def download_benign(timeout: float = 30.0) -> list[str]:
    print(f"Downloading Tranco top-1M domain list from {TRANCO_URL} ...")
    try:
        resp = requests.get(TRANCO_URL, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: could not download Tranco list ({e})", file=sys.stderr)
        sys.exit(1)

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            # The zip contains a single top-1m.csv with unheaded rows: rank,domain
            inner_name = zf.namelist()[0]
            with zf.open(inner_name) as f:
                text = f.read().decode("utf-8", errors="replace")
    except zipfile.BadZipFile as e:
        print(f"ERROR: Tranco response wasn't a valid zip ({e}) — the endpoint may have changed", file=sys.stderr)
        sys.exit(1)

    domains = []
    for line in text.splitlines():
        parts = line.strip().split(",")
        if len(parts) == 2 and parts[1]:
            domains.append(parts[1].strip())

    print(f"Parsed {len(domains):,} domains from Tranco")
    return domains


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="datasets/urls_labeled_live.csv")
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=3000,
        help="cap on rows per class after shuffling (set to 0 for no cap)",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    malicious_urls = download_malicious()
    benign_domains = download_benign()
    # Tranco entries are bare domains; add a scheme so they match the same
    # url shape as the malicious set (and what feature_extraction.py expects)
    benign_urls = [f"http://{d}" for d in benign_domains]

    random.shuffle(malicious_urls)
    random.shuffle(benign_urls)

    if args.max_per_class > 0:
        malicious_urls = malicious_urls[: args.max_per_class]
        benign_urls = benign_urls[: args.max_per_class]

    rows = [(u, 1) for u in malicious_urls] + [(u, 0) for u in benign_urls]
    random.shuffle(rows)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "label"])
        writer.writerows(rows)

    print(f"\nWrote {len(rows):,} rows ({len(benign_urls):,} benign, {len(malicious_urls):,} malicious) to {out_path}")
    print("Sources: URLhaus (abuse.ch, live) + Tranco (research-grade top-domains ranking)")
    print("\nNext step:")
    print(f"  python train.py --data {out_path} --out ../backend/ml/artifacts")
    print("(WHOIS lookups are meaningful here since these are live domains — consider")
    print(" dropping --skip-whois if you want the domain-age feature populated, though")
    print(" it will take longer)")


if __name__ == "__main__":
    main()
