import os
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "threat_model.joblib")


@dataclass
class ThreatPrediction:
    label: str
    probability: float
    probabilities_by_label: Dict[str, float]


class ThreatModel:
    """Wrapper around a scikit-learn text classification pipeline."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.pipeline: Optional[Pipeline] = None
        self.labels: List[str] = []

    def is_available(self) -> bool:
        return os.path.exists(self.model_path)

    def load(self) -> bool:
        if not self.is_available():
            return False
        obj = joblib.load(self.model_path)
        self.pipeline = obj["pipeline"]
        self.labels = obj["labels"]
        return True

    def predict(self, texts: List[str]) -> List[ThreatPrediction]:
        if not self.pipeline:
            raise RuntimeError("ThreatModel not loaded")
        probs = self._predict_proba(texts)
        preds: List[ThreatPrediction] = []
        for p in probs:
            best_idx = int(max(range(len(p)), key=lambda i: p[i]))
            best_label = self.labels[best_idx]
            proba_map = {self.labels[i]: float(p[i]) for i in range(len(self.labels))}
            preds.append(ThreatPrediction(label=best_label, probability=float(p[best_idx]), probabilities_by_label=proba_map))
        return preds

    def _predict_proba(self, texts: List[str]):
        # LogisticRegression has predict_proba
        return self.pipeline.predict_proba(texts)


def build_default_pipeline(C: float = 2.0, max_features: int = 50000) -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=max_features,
            min_df=2,
            strip_accents="unicode"
        )),
        ("clf", LogisticRegression(
            C=C,
            max_iter=200,
            n_jobs=None,
            solver="liblinear",
            class_weight="balanced"
        ))
    ])


def save_model(pipeline: Pipeline, labels: List[str], path: str = DEFAULT_MODEL_PATH) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump({"pipeline": pipeline, "labels": labels}, path)
    return path


