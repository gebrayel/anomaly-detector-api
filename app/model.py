import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.config import settings

FEATURE_NAMES = [
    "cpu_usage",
    "memory_usage",
    "latency_p95",
    "http_error_rate",
    "container_restarts",
    "network_traffic",
]


class AnomalyDetector:
    def __init__(self) -> None:
        self._model: IsolationForest | None = None
        self._load()

    def _load(self) -> None:
        path = Path(settings.model_path)
        if path.exists():
            self._model = joblib.load(path)

    def is_ready(self) -> bool:
        return self._model is not None

    def predict(self, features: list[float]) -> tuple[bool, float]:
        if not self.is_ready():
            raise RuntimeError("Modelo no cargado. Ejecuta /train primero.")
        X = np.array(features, dtype=float).reshape(1, -1)
        score = float(self._model.score_samples(X)[0])
        # predict() usa el offset_ derivado de contamination; devuelve -1 (anomalía) o 1 (normal).
        is_anomaly = int(self._model.predict(X)[0]) == -1
        return is_anomaly, score

    def classify_severity(self, is_anomaly: bool, features: list[float]) -> str:
        """
        Severidad híbrida: el IF detecta la anomalía; los umbrales por feature
        la gradúan. El IF satura el score para outliers extremos (limitación conocida),
        por lo que no es suficiente para distinguir low vs high.
        """
        if not is_anomaly:
            return "normal"
        cpu, memory, latency, error_rate, restarts, traffic = features
        # Criterios de alta severidad: al menos una condición crítica
        if (
            cpu > 0.85
            or memory > 0.85
            or latency > 500
            or error_rate > 0.15
            or restarts >= 5
            or traffic > 5_000_000
        ):
            return "high"
        return "low"

    def train(self, X: np.ndarray) -> None:
        # StandardScaler normaliza features con magnitudes muy distintas
        # (p.ej. network_traffic en millones vs cpu_usage en [0,1]).
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", IsolationForest(
                n_estimators=settings.n_estimators,
                contamination=settings.contamination,
                random_state=settings.random_state,
            )),
        ])
        pipeline.fit(X)
        out = Path(settings.model_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, out)
        self._model = pipeline


detector = AnomalyDetector()
