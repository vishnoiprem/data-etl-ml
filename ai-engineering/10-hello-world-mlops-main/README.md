# Hello-World MLOps

This repository demonstrates a tiny reproducible MLOps flow:
1. Train a small model (`train.py`) — writes `artifacts/model.pkl` and `artifacts/metrics.json`
2. Run predictions from the command line with `run_model.py --input "[5.1,3.5,1.4,0.2]"`
3. Start a minimal Flask app with `python src/app.py` that serves `/predict`
4. Build a Docker image with `docker build -t hello-mlops .`
5. CI trains the model and uploads artifacts

## Quick start (local)
1. Create and activate a venv (example using python 3.13 or 3.11):
    python -m venv .venv
    source .venv/bin/activate

2. Install dependencies:
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt

3. Train the model:
    python train.py

4. Run a single prediction from CLI:
    python run_model.py --input "[5.1, 3.5, 1.4, 0.2]"

5. Start the API:
    python src/app.py
   Then test:
    curl -X POST "http://127.0.0.1:5000/predict" -H "Content-Type: application/json" -d '{"features":[5.1,3.5,1.4,0.2]}'
