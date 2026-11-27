from fastapi import FastAPI, HTTPException, Header
from contextlib import asynccontextmanager

from app.model import detector, FEATURE_NAMES
from app.schemas import MetricsInput, PredictionResult, ModelInfo
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # El modelo se carga en AnomalyDetector.__init__; nada más que hacer aquí.
    yield


app = FastAPI(
    title="Anomaly Detector API",
    description="Detección de anomalías multivariante con Isolation Forest para clústeres Kubernetes.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "model_loaded": detector.is_ready()}


@app.get("/model/info", response_model=ModelInfo, tags=["ops"])
def model_info():
    return ModelInfo(
        n_estimators=settings.n_estimators,
        contamination=settings.contamination,
        low_severity_threshold=settings.low_severity_threshold,
        high_severity_threshold=settings.high_severity_threshold,
        features=FEATURE_NAMES,
        model_loaded=detector.is_ready(),
    )


@app.post("/predict", response_model=PredictionResult, tags=["inference"])
def predict(metrics: MetricsInput):
    if not detector.is_ready():
        raise HTTPException(status_code=503, detail="Modelo no disponible. Ejecuta POST /train primero.")

    features = [
        metrics.cpu_usage,
        metrics.memory_usage,
        metrics.latency_p95,
        metrics.http_error_rate,
        float(metrics.container_restarts),
        metrics.network_traffic,
    ]

    is_anomaly, score = detector.predict(features)
    severity = detector.classify_severity(is_anomaly, features)

    return PredictionResult(
        pod_name=metrics.pod_name,
        namespace=metrics.namespace,
        is_anomaly=is_anomaly,
        anomaly_score=score,
        severity=severity,
        features=dict(zip(FEATURE_NAMES, features)),
    )


@app.post("/train", tags=["ops"])
def train(x_api_key: str = Header(...)):
    if x_api_key != settings.train_api_key:
        raise HTTPException(status_code=403, detail="API key inválida.")

    from training.train import run_training
    n_samples = run_training()

    return {
        "status": "ok",
        "samples_used": n_samples,
        "model_path": settings.model_path,
    }
