# ml/artifacts/

Trained model files live here — created by `ml-training/train.py`, loaded
by the Flask API at startup (`ml/predict.py`, `ml/char_ngram_model.py`).
Empty in the repository on purpose: these are large binary files
regenerated from data, not source code, and shouldn't be committed
(see `.gitignore`).

## What gets written here

| File | Produced by | Loaded by |
|---|---|---|
| `random_forest_model.joblib` | `train.py` | `ml/predict.py` |
| `feature_scaler.joblib` | `train.py` | `ml/predict.py` |
| `char_ngram_model.joblib` | `train.py` | `ml/char_ngram_model.py` |
| `model_metadata.json` | `train.py` | `routes/model.py` (`/api/model/version`, `/api/model/drift`) |

## If this folder is empty

The API will start, but log a warning and every scan will fail — this is
the single most common source of confusion after a fresh clone/extraction
of this project (see the main README's troubleshooting section). Fix it
with:

```bash
python scripts/bootstrap.py
```

or manually:

```bash
cd ml-training
python download_real_dataset.py --out datasets/urls_labeled_real.csv --max-per-class 3000
python train.py --data datasets/urls_labeled_real.csv --out ../backend/ml/artifacts --skip-whois
```

Check `GET /api/status` or `GET /api/model/version` after starting the
server to confirm the model actually loaded.
