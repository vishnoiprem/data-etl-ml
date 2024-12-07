from fastapi import FastAPI, Request
import joblib
import numpy as np

# Load pre-trained model (e.g., logistic regression)
model = joblib.load("ad_click_model.pkl")

app = FastAPI()

@app.post("/predict")
async def predict(request: Request):
    payload = await request.json()
    features = np.array(payload["features"]).reshape(1, -1)
    prediction = model.predict_proba(features)[0, 1]  # Probability of a click
    return {"click_probability": prediction}

# Example input:
# {
#     "features": [0.5, 0.3, 0.2, ...]
# }