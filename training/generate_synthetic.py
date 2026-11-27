import numpy as np


def generate_normal(n_samples: int = 2000, random_state: int = 42) -> np.ndarray:
    """
    Comportamiento normal de un pod: uso moderado de recursos,
    latencia baja, pocos errores y sin reinicios.
    """
    rng = np.random.default_rng(random_state)
    return np.column_stack([
        rng.normal(0.30, 0.08, n_samples).clip(0.0, 1.0),    # cpu_usage
        rng.normal(0.40, 0.08, n_samples).clip(0.0, 1.0),    # memory_usage
        rng.normal(50.0, 12.0, n_samples).clip(1.0, None),   # latency_p95 (ms)
        rng.normal(0.01, 0.004, n_samples).clip(0.0, 1.0),   # http_error_rate
        rng.poisson(0.05, n_samples).astype(float),           # container_restarts
        rng.normal(1_000_000, 150_000, n_samples).clip(0.0, None),  # network_traffic (B/s)
    ])


def generate_anomalies(n_samples: int = 100, random_state: int = 99) -> np.ndarray:
    """
    Anomalías representativas: CPU spike, fuga de memoria,
    alta latencia, tasa de error elevada, reinicios continuos.
    """
    rng = np.random.default_rng(random_state)
    third = n_samples // 3

    # CPU + memoria disparados
    cpu_mem_spike = np.column_stack([
        rng.uniform(0.85, 1.0, third),
        rng.uniform(0.80, 1.0, third),
        rng.normal(60.0, 15.0, third).clip(1.0, None),
        rng.normal(0.012, 0.004, third).clip(0.0, 1.0),
        rng.poisson(0.05, third).astype(float),
        rng.normal(1_000_000, 150_000, third).clip(0.0, None),
    ])

    # Latencia alta + tasa de errores elevada
    latency_errors = np.column_stack([
        rng.normal(0.30, 0.08, third).clip(0.0, 1.0),
        rng.normal(0.40, 0.08, third).clip(0.0, 1.0),
        rng.uniform(800.0, 3000.0, third),
        rng.uniform(0.15, 0.50, third),
        rng.poisson(0.05, third).astype(float),
        rng.normal(1_000_000, 150_000, third).clip(0.0, None),
    ])

    # Reinicios continuos + picos de tráfico
    restarts_traffic = np.column_stack([
        rng.normal(0.30, 0.08, third).clip(0.0, 1.0),
        rng.normal(0.40, 0.08, third).clip(0.0, 1.0),
        rng.normal(55.0, 12.0, third).clip(1.0, None),
        rng.normal(0.012, 0.004, third).clip(0.0, 1.0),
        rng.randint(8, 25, third).astype(float),
        rng.uniform(6_000_000, 12_000_000, third),
    ])

    return np.vstack([cpu_mem_spike, latency_errors, restarts_traffic])
