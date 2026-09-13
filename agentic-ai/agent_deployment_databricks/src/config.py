from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    serving_endpoint: str
    mlflow_experiment_id: str | None
    environment: str

    @classmethod
    def from_env(cls) -> "Settings":
        endpoint = os.getenv("SERVING_ENDPOINT")
        if not endpoint:
            raise RuntimeError("SERVING_ENDPOINT is required. Bind a serving-endpoint resource in app.yaml.")
        return cls(
            serving_endpoint=endpoint,
            mlflow_experiment_id=os.getenv("MLFLOW_EXPERIMENT_ID"),
            environment=os.getenv("APP_ENV", "development"),
        )
