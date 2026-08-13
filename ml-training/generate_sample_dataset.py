"""
generate_sample_dataset.py — produces a synthetic-but-realistic labeled
URL dataset so you can run train.py and get a working model end-to-end
*today*, without waiting on PhishTank/URLhaus API access or downloading
the full Alexa Top 1M.

This is NOT a substitute for the real dataset in your final report — your
report should describe training on PhishTank + Alexa + URLhaus as
documented. But this lets you verify the whole pipeline (feature
extraction -> training -> serialization -> Flask serving -> dashboard)
works before you invest time in real data collection, and gives you a
demo-able model in the meantime.

Usage:
    python generate_sample_dataset.py --n 3000 --out datasets/urls_labeled.csv
"""

import argparse
import csv
import random

BENIGN_DOMAINS = [
    "google.com", "youtube.com", "wikipedia.org", "amazon.com", "reddit.com",
    "github.com", "stackoverflow.com", "linkedin.com", "microsoft.com", "apple.com",
    "netflix.com", "twitter.com", "instagram.com", "nytimes.com", "bbc.com",
    "cnn.com", "espn.com", "spotify.com", "dropbox.com", "adobe.com",
    "salesforce.com", "shopify.com", "zoom.us", "slack.com", "notion.so",
]
BENIGN_PATHS = ["", "/about", "/products", "/blog/2024/update", "/login", "/search?q=news", "/api/v2/users", "/docs/guide"]

BRANDS = ["paypal", "google", "microsoft", "apple", "amazon", "netflix", "bankofamerica", "chase", "facebook"]
SUSPICIOUS_TLDS = ["tk", "ml", "ga", "cf", "xyz", "top", "click", "loan", "work"]
SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "goo.gl"]
URGENT_PATHS = ["/verify-account", "/secure-login", "/update-billing", "/confirm-identity", "/account-suspended"]


def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def make_benign_url():
    domain = random.choice(BENIGN_DOMAINS)
    path = random.choice(BENIGN_PATHS)
    return f"https://www.{domain}{path}"


def make_malicious_url():
    strategy = random.choice(["typosquat", "ip_url", "shortener", "suspicious_tld", "long_subdomain"])
    brand = random.choice(BRANDS)

    if strategy == "typosquat":
        variants = [
            brand.replace("o", "0"), brand.replace("l", "1"), brand + "-secure",
            brand + "verify", "secure-" + brand, brand[:-1] + brand[-1] * 2,
        ]
        domain = random.choice(variants)
        tld = random.choice(["com", "net", random.choice(SUSPICIOUS_TLDS)])
        path = random.choice(URGENT_PATHS)
        return f"http://{domain}.{tld}{path}"

    if strategy == "ip_url":
        path = random.choice(URGENT_PATHS)
        return f"http://{random_ip()}{path}"

    if strategy == "shortener":
        shortener = random.choice(SHORTENERS)
        token = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=7))
        return f"http://{shortener}/{token}"

    if strategy == "suspicious_tld":
        word = brand + random.choice(["-login", "-support", "-account"])
        tld = random.choice(SUSPICIOUS_TLDS)
        path = random.choice(URGENT_PATHS)
        return f"http://{word}.{tld}{path}"

    # long_subdomain: brand buried in a long, unrelated registered domain
    filler = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))
    return f"http://{brand}.{filler}-secure-portal.info{random.choice(URGENT_PATHS)}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=3000, help="total rows (split ~50/50)")
    parser.add_argument("--out", default="datasets/urls_labeled.csv")
    args = parser.parse_args()

    rows = []
    for _ in range(args.n // 2):
        rows.append((make_benign_url(), 0))
    for _ in range(args.n // 2):
        rows.append((make_malicious_url(), 1))
    random.shuffle(rows)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "label"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows ({args.n // 2} benign, {args.n // 2} malicious) to {args.out}")
    print("Note: this is synthetic data for pipeline testing only — see the")
    print("docstring for why your final report should use real PhishTank/")
    print("URLhaus/Alexa data instead.")


if __name__ == "__main__":
    main()
