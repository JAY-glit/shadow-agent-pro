"""
typosquatting.py — flags domains that are suspiciously close (by edit
distance) to a curated list of high-value brand domains, catching classic
typosquats like paypa1.com, arnazon.com, micros0ft.com.
"""

import tldextract

KNOWN_BRANDS = [
    "paypal.com", "google.com", "microsoft.com", "apple.com", "amazon.com",
    "netflix.com", "facebook.com", "instagram.com", "bankofamerica.com",
    "chase.com", "wellsfargo.com", "linkedin.com", "github.com", "dropbox.com",
]

MAX_SUSPICIOUS_DISTANCE = 2  # edit distance <= this is considered a likely typosquat


def levenshtein(a: str, b: str) -> int:
    """Classic DP edit distance, no external deps needed."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr_row = [i]
        for j, cb in enumerate(b, 1):
            insert_cost = curr_row[j - 1] + 1
            delete_cost = prev_row[j] + 1
            replace_cost = prev_row[j - 1] + (ca != cb)
            curr_row.append(min(insert_cost, delete_cost, replace_cost))
        prev_row = curr_row
    return prev_row[-1]


def check_typosquatting(url: str) -> dict:
    """Returns the closest known brand and distance, if within threshold."""
    ext = tldextract.extract(url)
    candidate = ext.registered_domain.lower()

    if not candidate or candidate in KNOWN_BRANDS:
        return {"is_typosquat": False, "closest_brand": None, "distance": None}

    best_brand, best_distance = None, 999
    for brand in KNOWN_BRANDS:
        d = levenshtein(candidate, brand)
        if d < best_distance:
            best_brand, best_distance = brand, d

    is_typosquat = best_distance <= MAX_SUSPICIOUS_DISTANCE and best_distance > 0

    return {
        "is_typosquat": is_typosquat,
        "closest_brand": best_brand if is_typosquat else None,
        "distance": best_distance if is_typosquat else None,
    }
