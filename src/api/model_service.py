"""Loads the model ONCE at startup and exposes a batch prediction function."""
import os
from pathlib import Path
import joblib
import numpy as np
from src.utils.text import clean_text

NAMES = {-1: "negative", 0: "neutral", 1: "positive"}


class ModelService:
    def __init__(self, model_dir: str | None = None):
        d = Path(model_dir or os.getenv("MODEL_DIR", "models"))
        self.vectorizer = joblib.load(d / "tfidf_vectorizer.joblib")
        self.model = joblib.load(d / "sentiment_model.joblib")

    def predict(self, texts: list[str]):
        X = self.vectorizer.transform([clean_text(t) for t in texts])
        proba = self.model.predict_proba(X)
        idx = proba.argmax(axis=1)
        labels = self.model.classes_[idx]
        conf = proba[np.arange(len(idx)), idx]
        return labels.astype(int).tolist(), conf.tolist()
