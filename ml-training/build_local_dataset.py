"""
build_local_dataset.py — same URLhaus + Tranco merge as
download_live_dataset.py, but reads from local files you already have
instead of downloading them. Useful if you downloaded them manually
(e.g. via a browser, where abuse.ch's CSV sometimes saves with a .txt
extension) or want to reuse a snapshot rather than re-fetching.

Usage:
    python build_local_dataset.py \\
        --urlhaus path/to/urlhaus.csv \\
        --tranco path/to/top-1m.csv \\
        --out datasets/urls_labeled_live.csv \\
        --max-per-class 3000
"""

import argparse
import csv
import random
import sys
from pathlib import Path


def parse_urlhaus_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    reader = csv.reader(lines)

    urls = []
    for row in reader:
        if len(row) < 3:
            continue
        url = row[2].strip().strip('"')
        if url and url.startswith(("http://", "https://")):
            urls.append(url)
    return urls


def parse_tranco_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    domains = []
    for line in text.splitlines():
        parts = line.strip().split(",")
        if len(parts) == 2 and parts[1]:
            domains.append(parts[1].strip())
    return domains


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--urlhaus", required=True, help="path to the local URLhaus CSV dump")
    parser.add_argument("--tranco", required=True, help="path to the local Tranco top-1m.csv")
    parser.add_argument("--out", default="datasets/urls_labeled_live.csv")
    parser.add_argument("--max-per-class", type=int, default=3000, help="0 for no cap")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    urlhaus_path = Path(args.urlhaus)
    tranco_path = Path(args.tranco)

    if not urlhaus_path.exists():
        print(f"ERROR: {urlhaus_path} not found", file=sys.stderr)
        sys.exit(1)
    if not tranco_path.exists():
        print(f"ERROR: {tranco_path} not found", file=sys.stderr)
        sys.exit(1)

    malicious_urls = parse_urlhaus_file(urlhaus_path)
    print(f"Parsed {len(malicious_urls):,} malicious URLs from {urlhaus_path.name}")

    benign_domains = parse_tranco_file(tranco_path)
    print(f"Parsed {len(benign_domains):,} domains from {tranco_path.name}")
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


if __name__ == "__main__":
    main()
