"""
allowlist.py — a small, curated set of globally well-known legitimate
domains, checked by EXACT registered-domain match.

Why this exists: character n-gram models (and to a lesser extent the RF's
brand-keyword features) learn from data where popular brands are heavily
over-represented in the *malicious* class, because attackers disproportion-
ately impersonate popular brands (see ml/char_ngram_model.py's docstring
for a concrete measurement — in one 3000-per-class real-data sample, 24
malicious URLs contained "goog" versus only 9 legitimate Google URLs).
A model trained on that data correctly learns the statistical pattern in
front of it, but the pattern itself is a trap: it means the exact domains
most worth getting right (the ones users actually visit constantly) are
the ones a naive text classifier is most likely to flag.

This allowlist is intentionally small and boring — global top-traffic
domains only, not a general safety mechanism. It is checked by EXACT
match against tldextract's registered_domain (e.g. "mail.google.com"
matches via its registered_domain "google.com", but "google-secure-
login.tk" does NOT match, since its registered_domain is "google-secure-
login.tk") — so it cannot be defeated by a phishing domain merely
containing a brand name, only by controlling one of these exact domains
outright, which is a fundamentally different threat model (and one no
URL-based classifier could catch anyway).
"""

KNOWN_LEGITIMATE_DOMAINS = {
    "google.com", "youtube.com", "gmail.com", "googleusercontent.com",
    "facebook.com", "instagram.com", "whatsapp.com", "messenger.com",
    "microsoft.com", "live.com", "office.com", "outlook.com", "bing.com",
    "apple.com", "icloud.com",
    "amazon.com", "amazonaws.com",
    "wikipedia.org", "wikimedia.org",
    "twitter.com", "x.com",
    "linkedin.com",
    "netflix.com", "spotify.com",
    "github.com", "gitlab.com", "stackoverflow.com", "stackexchange.com",
    "reddit.com",
    "yahoo.com",
    "paypal.com", "ebay.com",
    "dropbox.com", "adobe.com", "salesforce.com", "zoom.us", "slack.com",
    "cloudflare.com",
    "nytimes.com", "bbc.com", "cnn.com", "espn.com",
    "wordpress.com", "shopify.com",
    "mozilla.org",
}


def is_known_legitimate(registered_domain: str) -> bool:
    return registered_domain.lower() in KNOWN_LEGITIMATE_DOMAINS
