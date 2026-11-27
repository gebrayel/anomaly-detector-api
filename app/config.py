from pathlib import Path
from pydantic_settings import BaseSettings

_DEFAULT_MODEL_PATH = str(Path(__file__).resolve().parents[1] / "models" / "isolation_forest.pkl")


class Settings(BaseSettings):
    # En Docker se sobreescribe con IF_MODEL_PATH=/app/models/isolation_forest.pkl
    if_model_path: str = _DEFAULT_MODEL_PATH
    contamination: float = 0.05
    # Threshold sobre score_samples(): negativo = más anómalo.
    # Scores < low_severity_threshold → low; < high_severity_threshold → high.
    low_severity_threshold: float = 0.0
    high_severity_threshold: float = -0.1
    n_estimators: int = 100
    random_state: int = 42
    train_api_key: str = "changeme"

    model_config = {"env_prefix": "IF_", "protected_namespaces": ()}

    @property
    def model_path(self) -> str:
        return self.if_model_path


settings = Settings()
