#!/usr/bin/env python3
"""
Usage:
    python run_model.py --input "[5.1, 3.5, 1.4, 0.2]"
"""

import argparse
import json
from pathlib import Path
import numpy as np
import joblib

MODEL_PATH = Path("artifacts/model.pkl")

def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)   # <-- correct binary loading

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True,
                        help="Feature list as JSON string. Example: \"[5.1,3.5,1.4,0.2]\"")
    args = parser.parse_args()

    # Parse input
    try:
        features = json.loads(args.input)
    except json.JSONDecodeError:
        raise ValueError("Invalid input. Use JSON list, e.g. --input \"[5.1,3.5,1.4,0.2]\"")

    X = np.array(features).reshape(1, -1)

    model = load_model()
    pred = model.predict(X)

    print(json.dumps({"prediction": pred.tolist()}))

if __name__ == "__main__":
    main()

