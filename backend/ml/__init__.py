"""
ml — the detection core: feature extraction, the trained Random Forest +
character n-gram ensemble, and SHAP-based explainability.

See feature_extraction.py for the 25+ engineered features, predict.py for
the ThreatClassifier that ensembles both models, and char_ngram_model.py
for the independent second-opinion classifier trained directly on raw
URL text.
"""
