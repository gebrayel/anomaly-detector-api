"""
Script de entrenamiento del modelo Isolation Forest.
Puede ejecutarse directamente (python -m training.train)
o ser invocado desde el endpoint POST /train.
"""
import sys
from pathlib import Path

# Permite ejecutar como script standalone desde la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from training.generate_synthetic import generate_normal
from app.model import detector


def run_training(n_samples: int = 2000) -> int:
    X = generate_normal(n_samples=n_samples)
    detector.train(X)
    print(f"[train] Modelo entrenado con {len(X)} muestras. Guardado en {detector._model}")
    return len(X)


if __name__ == "__main__":
    run_training()
