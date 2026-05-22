"""
ETA Prediction — inference module.

Lazy-loads the trained model on first call; subsequent calls are fast.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import joblib

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))
from features.feature_engineering import FEATURE_COLS

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

_model         = None
_feature_names = None


def load_model():
    global _model, _feature_names
    if _model is None:
        mp = ARTIFACTS_DIR / "eta_model.pkl"
        if not mp.exists():
            raise FileNotFoundError(f"No trained model at {mp}. Run models/eta/train.py first.")
        _model         = joblib.load(mp)
        _feature_names = joblib.load(ARTIFACTS_DIR / "feature_names.pkl")
    return _model, _feature_names


def predict_eta(features: pd.DataFrame) -> np.ndarray:
    """Predict delivery leg time (minutes) for each row."""
    model, names = load_model()
    X = features.reindex(columns=names, fill_value=0.0)
    return np.maximum(model.predict(X), 1.0)


def predict_single(
    *,
    distance_km: float,
    hour_of_day: int,
    day_of_week: int = 1,
    zone_id: int = 0,
    hub_id_enc: int = 0,
    congestion: float = 0.40,
    weight_kg: float = 2.0,
    stop_number: int = 0,
    experience_days: int = 365,
    speed_factor: float = 1.0,
    is_weekend: int = 0,
    weather: float = 0.0,
    urgency_enc: int = 0,
) -> float:
    """Convenience wrapper for a single delivery prediction."""
    row = {
        "distance_km":       distance_km,
        "hub_to_dropoff_km": distance_km * 1.2,
        "hour_of_day":       hour_of_day,
        "day_of_week":       day_of_week,
        "is_weekend":        is_weekend,
        "is_peak_hour":      int(7 <= hour_of_day <= 9 or 17 <= hour_of_day <= 19),
        "zone_id":           zone_id,
        "hub_id_enc":        hub_id_enc,
        "congestion_at_time": congestion,
        "weather_severity":  weather,
        "package_weight_kg": weight_kg,
        "stop_number":       stop_number,
        "log_experience":    np.log1p(experience_days),
        "speed_factor":      speed_factor,
        "urgency_enc":       urgency_enc,
    }
    return float(predict_eta(pd.DataFrame([row]))[0])
