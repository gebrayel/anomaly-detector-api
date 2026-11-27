from pydantic import BaseModel, Field
from typing import Literal


class MetricsInput(BaseModel):
    pod_name: str = Field(..., description="Nombre del pod evaluado")
    namespace: str = Field(default="default", description="Namespace de Kubernetes")
    cpu_usage: float = Field(..., ge=0.0, le=1.0, description="Uso de CPU (ratio 0–1)")
    memory_usage: float = Field(..., ge=0.0, le=1.0, description="Uso de memoria (ratio 0–1)")
    latency_p95: float = Field(..., ge=0.0, description="Latencia P95 en milisegundos")
    http_error_rate: float = Field(..., ge=0.0, le=1.0, description="Tasa de errores HTTP (ratio 0–1)")
    container_restarts: int = Field(..., ge=0, description="Número de reinicios del contenedor")
    network_traffic: float = Field(..., ge=0.0, description="Tráfico de red en bytes/s")


class PredictionResult(BaseModel):
    pod_name: str
    namespace: str
    is_anomaly: bool
    anomaly_score: float = Field(..., description="Score de anomalía (más negativo = más anómalo)")
    severity: Literal["normal", "low", "high"]
    features: dict[str, float]


class ModelInfo(BaseModel):
    n_estimators: int
    contamination: float
    low_severity_threshold: float
    high_severity_threshold: float
    features: list[str]
    model_loaded: bool
