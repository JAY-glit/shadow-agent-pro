# Datasets

This folder is where labeled URL datasets live for training. It's empty in
the repository on purpose — datasets are either generated or downloaded,
not committed (they're large and, in the real-data case, not ours to
redistribute).

## Getting a dataset here

**Synthetic (instant, for pipeline testing):**
```bash
python generate_sample_dataset.py --n 3000
```
Produces `urls_labeled.csv` — typosquats, IP-literal URLs, shorteners,
suspicious TLDs vs. real benign domains. Good for verifying the pipeline
works end-to-end in under a minute, not for a real accuracy claim.

**Real (recommended for anything beyond a quick test):**
```bash
python download_real_dataset.py --out datasets/urls_labeled_real.csv --max-per-class 3000
```
Pulls a real, public 420K-row labeled URL dataset and converts it to the
schema `train.py` expects. See that script's docstring for full source
attribution and known limitations (it's ~2016-era data with a binary
malicious label, not phishing-specific).

**Live threat intelligence (strongest methodology, recommended if you want current data):**
```bash
python download_live_dataset.py --out datasets/urls_labeled_live.csv --max-per-class 3000
```
Combines URLhaus (currently-active malicious URLs) with Tranco (a
research-grade top-domains ranking, the academic replacement for the
discontinued Alexa list). Both sources are live and independently
maintained — see that script's docstring for details, including an
honest note about what was and wasn't network-testable when it was built.

## Expected format

Whatever ends up here must be a CSV with exactly two columns:

| Column | Type | Meaning |
|---|---|---|
| `url`   | string | Full URL including scheme (`http://` or `https://`) |
| `label` | int    | `0` = benign, `1` = malicious |

If you're sourcing your own data (e.g. real PhishTank/URLhaus/Alexa
exports as originally documented in the project report), convert it to
this schema before pointing `train.py --data` at it.
