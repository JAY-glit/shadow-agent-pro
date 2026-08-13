"""
download_real_dataset.py — pulls a real, publicly available labeled URL
dataset (420K+ URLs, sourced from a mix of threat feeds including
PhishTank-derived data, collected by github.com/faizann24) and converts it
into the url,label schema train.py expects.

This is real-world data, not synthetic — a legitimate improvement over
generate_sample_dataset.py for anything beyond quick pipeline testing.
Source: https://github.com/faizann24/Using-machine-learning-to-detect-malicious-URLs
(the dataset itself was assembled from multiple public sources; see that
repo's README for full provenance).

Known limitations worth stating in your report:
  - Collected ~2016 — many of the original domains have since expired,
    changed hands, or gone offline, so live signals (SSL, WHOIS) will
    often come back "unavailable" for older rows rather than "safe".
    This is realistic noise, not a bug — real detection systems have to
    handle stale threat intel too.
  - Labels are binary (malicious encompasses phishing, malware, and spam
    domains together, not phishing specifically) — mention this if your
    report claims phishing-specific accuracy.
  - Classes are imbalanced (~82% benign / ~18% malicious) — this script
    can balance/subsample; train.py's RandomizedSearchCV also tries
    class_weight="balanced" as a hyperparameter option.

Usage:
    python download_real_dataset.py --out datasets/urls_labeled_real.csv --max-per-class 3000
"""

import argparse
import csv
import random
import sys
from pathlib import Path

import requests

SOURCE_URL = (
    "https://raw.githubusercontent.com/faizann24/"
    "Using-machine-learning-to-detect-malicious-URLs/master/data/data.csv"
)


def download_raw(timeout: float = 30.0) -> str:
    print(f"Downloading real dataset from {SOURCE_URL} ...")
    resp = requests.get(SOURCE_URL, timeout=timeout)
    resp.raise_for_status()
    print(f"Downloaded {len(resp.content):,} bytes")
    # Decode explicitly as UTF-8 with a replace fallback rather than relying
    # on requests' charset auto-detection — a handful of rows in this
    # dataset contain stray non-UTF-8 bytes (accented characters in a few
    # international domains), and letting that raise mid-parse would kill
    # the whole download. Replacing those few bytes with U+FFFD is a
    # negligible loss against 420K rows.
    return resp.content.decode("utf-8", errors="replace")


def normalize_rows(raw_csv_text: str):
    """Source format is bare-domain-or-path,good|bad. Normalizes to a full
    URL (adds http:// scheme, which is what our feature extractor and the
    rest of the pipeline expect) and a 0/1 label."""
    reader = csv.reader(raw_csv_text.splitlines())
    header = next(reader, None)  # "url,label"

    benign, malicious = [], []
    for row in reader:
        if len(row) < 2:
            continue
        raw_url, label = row[0].strip(), row[1].strip().lower()
        if not raw_url or label not in ("good", "bad"):
            continue

        url = raw_url if raw_url.startswith(("http://", "https://")) else f"http://{raw_url}"
        target = benign if label == "good" else malicious
        target.append(url)

    return benign, malicious


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="datasets/urls_labeled_real.csv")
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=3000,
        help="cap on rows per class after shuffling, keeps feature extraction + "
        "training time reasonable while still using real data (set to 0 for no cap, "
        "i.e. the full ~345K/76K split)",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    try:
        raw_text = download_raw()
    except requests.RequestException as e:
        print(f"ERROR: could not download dataset ({e})", file=sys.stderr)
        print("Check your internet connection, or fall back to generate_sample_dataset.py", file=sys.stderr)
        sys.exit(1)

    benign, malicious = normalize_rows(raw_text)
    print(f"Parsed {len(benign):,} benign / {len(malicious):,} malicious rows")

    random.shuffle(benign)
    random.shuffle(malicious)

    if args.max_per_class > 0:
        benign = benign[: args.max_per_class]
        malicious = malicious[: args.max_per_class]

    rows = [(u, 0) for u in benign] + [(u, 1) for u in malicious]
    random.shuffle(rows)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # encoding="utf-8" is explicit here on purpose — Windows' default text-mode
    # encoding is the system locale (often cp1252), not UTF-8. Without this,
    # the file written here and the file train.py reads later can disagree
    # on encoding and pandas will throw a UnicodeDecodeError.
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "label"])
        writer.writerows(rows)

    print(f"\nWrote {len(rows):,} rows ({len(benign):,} benign, {len(malicious):,} malicious) to {out_path}")
    print("Source: faizann24/Using-machine-learning-to-detect-malicious-URLs (real-world, ~2016)")
    print("\nNext step:")
    print(f"  python train.py --data {out_path} --out ../backend/ml/artifacts")
    print("(consider --skip-whois on a first pass — many of these older domains")
    print(" are now expired, so WHOIS lookups will mostly return 'unknown' anyway)")


if __name__ == "__main__":
    main()
