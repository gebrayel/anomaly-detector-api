# Anomaly Detector API

Microservicio REST de detección de anomalías multivariante para clústeres Kubernetes, desarrollado como parte del TFM *"Plataforma de Observabilidad Inteligente con Auto-Remediación en Kubernetes"* (UNIR, 2026).

Implementa el algoritmo **Isolation Forest** (scikit-learn) sobre un vector de seis métricas extraídas de Prometheus y expone el modelo como una API HTTP lista para ser consumida por el motor de remediación automática.

---

## Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Especificaciones técnicas](#especificaciones-técnicas)
- [Endpoints](#endpoints)
- [Levantamiento local](#levantamiento-local)
- [Demo visual](#demo-visual)
- [Despliegue en Kubernetes](#despliegue-en-kubernetes)
- [Variables de entorno](#variables-de-entorno)
- [Estructura del proyecto](#estructura-del-proyecto)

---

## Arquitectura

```
Prometheus ──► Anomaly Detector API ──► severity: normal  →  sin acción
                (Isolation Forest)   ├── severity: low    →  auto-remediar
                                     └── severity: high   →  HITL (operador)
```

El modelo recibe un vector de métricas de un pod, calcula el *anomaly score* y devuelve una clasificación en tres niveles que el motor de remediación (Fase 3) usa para decidir si actuar automáticamente o notificar al operador.

---

## Especificaciones técnicas

| Componente | Detalle |
|---|---|
| Lenguaje | Python 3.12 |
| Framework | FastAPI 0.115 |
| Algoritmo | Isolation Forest (scikit-learn 1.5) |
| Normalización | StandardScaler (Pipeline) |
| Muestras de entrenamiento | 2 000 (datos sintéticos de comportamiento normal) |
| Contaminación (`contamination`) | 0.05 (5 % de anomalías esperadas) |
| Servidor ASGI | Uvicorn |

### Vector de features

| Feature | Descripción | Unidad |
|---|---|---|
| `cpu_usage` | Uso de CPU del pod | ratio 0–1 |
| `memory_usage` | Uso de memoria del pod | ratio 0–1 |
| `latency_p95` | Latencia en el percentil 95 | milisegundos |
| `http_error_rate` | Tasa de errores HTTP | ratio 0–1 |
| `container_restarts` | Número de reinicios del contenedor | entero |
| `network_traffic` | Tráfico de red | bytes/s |

### Clasificación de severidad

| Severidad | Condición | Acción esperada |
|---|---|---|
| `normal` | Isolation Forest no detecta anomalía | Ninguna |
| `low` | Anomalía detectada, sin feature crítica | Motor de remediación actúa automáticamente |
| `high` | Anomalía + al menos un feature crítico* | Notificación HITL al operador |

*Criterios de feature crítico: CPU > 85 %, memoria > 85 %, latencia > 500 ms, error rate > 15 %, reinicios ≥ 5, tráfico > 5 MB/s.

---

## Endpoints

### `POST /predict`
Clasifica el estado de un pod.

**Request**
```json
{
  "pod_name": "frontend-7d9f",
  "namespace": "production",
  "cpu_usage": 0.25,
  "memory_usage": 0.38,
  "latency_p95": 42.0,
  "http_error_rate": 0.005,
  "container_restarts": 0,
  "network_traffic": 850000
}
```

**Response**
```json
{
  "pod_name": "frontend-7d9f",
  "namespace": "production",
  "is_anomaly": false,
  "anomaly_score": -0.406,
  "severity": "normal",
  "features": { "cpu_usage": 0.25, "memory_usage": 0.38, "..." : "..." }
}
```

### `GET /health`
Liveness probe para Kubernetes.
```bash
curl http://localhost:8001/health
# {"status":"ok","model_loaded":true}
```

### `GET /model/info`
Hiperparámetros del modelo activo.
```bash
curl http://localhost:8001/model/info
```

### `POST /train`
Re-entrena el modelo con datos sintéticos frescos. Requiere API key.
```bash
curl -X POST http://localhost:8001/train \
  -H "x-api-key: changeme"
```

### `GET /docs`
Documentación Swagger interactiva generada automáticamente por FastAPI.

---

## Levantamiento local

### Requisitos previos
- Python 3.12+
- Git

### Pasos

**1. Clonar el repositorio**
```bash
git clone https://github.com/gebrayel/anomaly-detector-api.git
cd anomaly-detector-api
```

**2. Crear entorno virtual e instalar dependencias**
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**3. Entrenar el modelo**
```bash
.venv/bin/python -m training.train
```
Genera `models/isolation_forest.pkl` con 2 000 muestras sintéticas.

**4. Arrancar el servidor**
```bash
.venv/bin/uvicorn app.main:app --reload --port 8001
```

| URL | Descripción |
|---|---|
| http://localhost:8001/demo | Demo visual interactivo |
| http://localhost:8001/docs | Swagger UI |
| http://localhost:8001/health | Estado del servicio |

### Curls de ejemplo

```bash
# Pod en estado normal
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "pod_name": "frontend-7d9f",
    "namespace": "production",
    "cpu_usage": 0.25,
    "memory_usage": 0.38,
    "latency_p95": 42.0,
    "http_error_rate": 0.005,
    "container_restarts": 0,
    "network_traffic": 850000
  }'

# Anomalía leve → auto-remediación
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "pod_name": "backend-api-3x7k",
    "namespace": "production",
    "cpu_usage": 0.62,
    "memory_usage": 0.68,
    "latency_p95": 380.0,
    "http_error_rate": 0.07,
    "container_restarts": 3,
    "network_traffic": 2200000
  }'

# Anomalía grave → HITL
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "pod_name": "db-proxy-9p2m",
    "namespace": "production",
    "cpu_usage": 0.92,
    "memory_usage": 0.89,
    "latency_p95": 1800.0,
    "http_error_rate": 0.28,
    "container_restarts": 12,
    "network_traffic": 8500000
  }'
```

---

## Demo visual

Abre **http://localhost:8001/demo** en el browser con el servidor corriendo.

La demo incluye:
- Sliders para ajustar los 6 features en tiempo real
- Presets de un clic: Normal / Anomalía leve / Anomalía grave
- Gauge animado del anomaly score
- Banner de severidad con la acción esperada
- Llamadas en vivo a todos los endpoints

---

## Despliegue en Kubernetes

```bash
# Construir la imagen (el modelo se entrena durante el build)
docker build -t anomaly-detector-api:latest .

# Crear el secreto para el endpoint /train
kubectl create secret generic anomaly-detector-secret \
  --from-literal=train-api-key=<tu-api-key> \
  -n monitoring

# Aplicar los manifiestos
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

El servicio queda disponible dentro del clúster en:
```
http://anomaly-detector.monitoring.svc.cluster.local/predict
```

---

## Variables de entorno

Todas tienen el prefijo `IF_`.

| Variable | Default | Descripción |
|---|---|---|
| `IF_MODEL_PATH` | `models/isolation_forest.pkl` | Ruta del modelo serializado |
| `IF_CONTAMINATION` | `0.05` | Proporción de anomalías esperadas |
| `IF_LOW_SEVERITY_THRESHOLD` | `0.0` | Umbral de score para clasificar anomalía |
| `IF_HIGH_SEVERITY_THRESHOLD` | `-0.1` | Umbral secundario (no usado actualmente) |
| `IF_N_ESTIMATORS` | `100` | Número de árboles del Isolation Forest |
| `IF_TRAIN_API_KEY` | `changeme` | API key para el endpoint `/train` |

---

## Estructura del proyecto

```
anomaly-detector-api/
├── app/
│   ├── config.py              # Configuración por variables de entorno
│   ├── main.py                # FastAPI: rutas y middleware
│   ├── model.py               # Pipeline StandardScaler + Isolation Forest
│   └── schemas.py             # Modelos Pydantic (request / response)
├── training/
│   ├── generate_synthetic.py  # Generador de datos sintéticos
│   └── train.py               # Script de entrenamiento
├── models/
│   └── isolation_forest.pkl   # Modelo serializado (generado por train.py)
├── k8s/
│   ├── deployment.yaml        # Deployment de Kubernetes
│   └── service.yaml           # ClusterIP Service
├── demo.html                  # Demo visual interactivo
├── Dockerfile
└── requirements.txt
```

---

## Contexto del TFM

Este módulo corresponde a la **Fase 2** del TFM:

| Fase | Descripción | Estado |
|---|---|---|
| 1 | Pila de observabilidad (Prometheus, Loki, Jaeger, Grafana) | Pendiente |
| **2** | **API de detección con Isolation Forest** | **En curso** |
| 3 | Motor de remediación automática + flujo HITL | Pendiente |
| 4 | Validación experimental (chaos engineering) | Pendiente |
| 5 | Análisis de resultados y documentación | Pendiente |
