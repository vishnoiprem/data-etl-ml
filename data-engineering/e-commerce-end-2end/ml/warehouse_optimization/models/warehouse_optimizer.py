"""
ML Module: Warehouse Inventory Optimization
============================================
Models:
  1. Demand Forecasting   - XGBoost time-series per SKU/warehouse
  2. Reorder Point Model  - Minimize stockout + holding cost
  3. Transfer Optimizer   - Which warehouse to ship from (minimize cost)
  4. Overstock Detector   - Flag slow-moving / dead stock

Input:  ecomm_ads.ads_warehouse_efficiency + fact_order_items
Output: Recommendations table → BI product API
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
import logging
import json
import os

from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
import xgboost as xgb
from scipy.optimize import linprog

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("warehouse-optimizer")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../training/saved_models")
os.makedirs(MODEL_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════
# 1. DEMAND FORECASTING
# ══════════════════════════════════════════════════════════════
class DemandForecaster:
    """
    Forecasts daily demand per SKU/warehouse for next 30 days.
    Uses XGBoost with lag features + calendar features.
    """

    def __init__(self):
        self.models = {}
        self.label_encoders = {}
        self.feature_cols = []

    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer time-series features."""
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"])
        df = df.sort_values(["sku_id", "warehouse_id", "order_date"])

        # Calendar features
        df["day_of_week"] = df["order_date"].dt.dayofweek
        df["day_of_month"] = df["order_date"].dt.day
        df["month"] = df["order_date"].dt.month
        df["quarter"] = df["order_date"].dt.quarter
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["week_of_year"] = df["order_date"].dt.isocalendar().week.astype(int)

        # Lag features per sku+warehouse
        group_cols = ["sku_id", "warehouse_id"]
        for lag in [1, 3, 7, 14, 21, 28]:
            df[f"demand_lag_{lag}"] = df.groupby(group_cols)["units_sold"].shift(lag)

        # Rolling features
        for window in [7, 14, 30]:
            df[f"demand_roll_mean_{window}"] = (
                df.groupby(group_cols)["units_sold"]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
            )
            df[f"demand_roll_std_{window}"] = (
                df.groupby(group_cols)["units_sold"]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).std())
            )
            df[f"demand_roll_max_{window}"] = (
                df.groupby(group_cols)["units_sold"]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).max())
            )

        # Encode categoricals
        for col in ["sku_id", "warehouse_id", "category_id"]:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[f"{col}_enc"] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    known = set(self.label_encoders[col].classes_)
                    df[f"{col}_enc"] = df[col].astype(str).apply(
                        lambda x: self.label_encoders[col].transform([x])[0] if x in known else -1
                    )

        return df.dropna()

    def train(self, df: pd.DataFrame):
        """Train XGBoost demand model."""
        logger.info("Training demand forecasting model...")
        df_feat = self._build_features(df)

        feature_cols = [c for c in df_feat.columns if c not in
                        ["order_date", "units_sold", "sku_id", "warehouse_id"]]
        self.feature_cols = feature_cols

        X = df_feat[feature_cols]
        y = df_feat["units_sold"]

        # Time-based split (last 30 days = test)
        cutoff = df_feat["order_date"].max() - timedelta(days=30)
        X_train = X[df_feat["order_date"] <= cutoff]
        X_test  = X[df_feat["order_date"] > cutoff]
        y_train = y[df_feat["order_date"] <= cutoff]
        y_test  = y[df_feat["order_date"] > cutoff]

        model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            early_stopping_rounds=20,
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=50,
        )

        y_pred = model.predict(X_test)
        y_pred_clipped = np.clip(y_pred, 0, None)

        mape = mean_absolute_percentage_error(y_test + 1, y_pred_clipped + 1)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred_clipped))
        logger.info(f"Demand Model | MAPE: {mape:.4f} | RMSE: {rmse:.2f}")

        self.models["demand"] = model

        # Feature importance
        importance = pd.DataFrame({
            "feature": feature_cols,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)
        logger.info(f"Top 10 features:\n{importance.head(10).to_string(index=False)}")

        # Save model
        joblib.dump(model, f"{MODEL_DIR}/demand_forecaster.pkl")
        joblib.dump(self.label_encoders, f"{MODEL_DIR}/label_encoders.pkl")
        logger.info("Model saved.")
        return model

    def forecast(self, df: pd.DataFrame, horizon_days: int = 30) -> pd.DataFrame:
        """Generate demand forecasts for next N days."""
        if "demand" not in self.models:
            model = joblib.load(f"{MODEL_DIR}/demand_forecaster.pkl")
            self.label_encoders = joblib.load(f"{MODEL_DIR}/label_encoders.pkl")
            self.models["demand"] = model

        df_feat = self._build_features(df)
        if not self.feature_cols:
            self.feature_cols = [c for c in df_feat.columns
                                 if c not in ["order_date", "units_sold", "sku_id", "warehouse_id"]]

        # Predict on latest data
        X = df_feat[self.feature_cols]
        predictions = self.models["demand"].predict(X)
        predictions = np.clip(predictions, 0, None)

        results = df_feat[["sku_id", "warehouse_id", "order_date"]].copy()
        results["predicted_demand"] = np.round(predictions, 1)
        results["forecast_date"] = datetime.utcnow().date()
        return results


# ══════════════════════════════════════════════════════════════
# 2. REORDER POINT OPTIMIZER
# ══════════════════════════════════════════════════════════════
class ReorderOptimizer:
    """
    Computes optimal reorder point (ROP) and Economic Order Quantity (EOQ).

    ROP  = (avg_daily_demand × lead_time_days) + safety_stock
    EOQ  = sqrt(2 × D × S / H)
    Safety Stock = Z × σ_d × sqrt(lead_time)
    """

    SERVICE_LEVEL_Z = {
        0.90: 1.28,
        0.95: 1.65,
        0.99: 2.33,
    }

    def __init__(self, service_level: float = 0.95, holding_cost_rate: float = 0.25):
        self.z = self.SERVICE_LEVEL_Z.get(service_level, 1.65)
        self.holding_cost_rate = holding_cost_rate  # 25% of unit cost per year

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        df columns: sku_id, warehouse_id, avg_daily_demand, std_daily_demand,
                    lead_time_days, unit_cost, ordering_cost, current_stock
        """
        df = df.copy()

        # Safety Stock: Z * σ_daily * sqrt(lead_time)
        df["safety_stock"] = np.ceil(
            self.z * df["std_daily_demand"] * np.sqrt(df["lead_time_days"])
        ).astype(int)

        # Reorder Point
        df["reorder_point"] = np.ceil(
            df["avg_daily_demand"] * df["lead_time_days"] + df["safety_stock"]
        ).astype(int)

        # EOQ = sqrt(2DS/H)
        annual_demand = df["avg_daily_demand"] * 365
        holding_cost = df["unit_cost"] * self.holding_cost_rate
        df["eoq"] = np.ceil(
            np.sqrt(2 * annual_demand * df["ordering_cost"] / holding_cost.replace(0, 1))
        ).astype(int)

        # Days of stock remaining
        df["days_of_stock"] = (df["current_stock"] / df["avg_daily_demand"].replace(0, 0.01)).round(1)

        # Needs reorder?
        df["needs_reorder"] = df["current_stock"] <= df["reorder_point"]
        df["stockout_risk_days"] = np.where(
            df["needs_reorder"],
            np.ceil((df["reorder_point"] - df["current_stock"]) / df["avg_daily_demand"].replace(0, 1)),
            0
        ).astype(int)

        # Priority score (lower = more urgent)
        df["reorder_urgency"] = (
            df["days_of_stock"] * (1 / (df["avg_daily_demand"] + 1))
        ).round(3)
        df["priority"] = pd.qcut(df["reorder_urgency"], q=5, labels=["Critical", "High", "Medium", "Low", "None"])

        return df[[
            "sku_id", "warehouse_id", "current_stock", "avg_daily_demand",
            "safety_stock", "reorder_point", "eoq", "days_of_stock",
            "needs_reorder", "stockout_risk_days", "priority"
        ]]


# ══════════════════════════════════════════════════════════════
# 3. TRANSFER OPTIMIZER (which warehouse to fulfill from)
# ══════════════════════════════════════════════════════════════
class TransferOptimizer:
    """
    Linear programming to minimize total fulfillment cost.
    Minimize: sum(cost[i][j] * x[i][j])
    Subject to:
      - demand[j] satisfied for each destination j
      - supply[i] not exceeded for each source warehouse i
      - x[i][j] >= 0
    """

    def optimize(self, supply: dict, demand: dict, cost_matrix: dict) -> pd.DataFrame:
        """
        supply: {warehouse_id: available_units}
        demand: {city_zone: required_units}
        cost_matrix: {(warehouse_id, city_zone): shipping_cost_per_unit}

        Returns allocation plan.
        """
        warehouses = list(supply.keys())
        cities = list(demand.keys())
        n_w = len(warehouses)
        n_c = len(cities)

        # Build cost vector (flatten)
        c = [cost_matrix.get((w, city), 999.0) for w in warehouses for city in cities]

        # Inequality constraints: supply[i] >= sum_j x[i][j]
        A_ub = []
        b_ub = []
        for i, w in enumerate(warehouses):
            row = [0] * (n_w * n_c)
            for j in range(n_c):
                row[i * n_c + j] = 1
            A_ub.append(row)
            b_ub.append(supply[w])

        # Equality constraints: sum_i x[i][j] = demand[j]
        A_eq = []
        b_eq = []
        for j, city in enumerate(cities):
            row = [0] * (n_w * n_c)
            for i in range(n_w):
                row[i * n_c + j] = 1
            A_eq.append(row)
            b_eq.append(demand[city])

        bounds = [(0, None)] * (n_w * n_c)

        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                         bounds=bounds, method="highs")

        if result.success:
            allocations = []
            for idx, val in enumerate(result.x):
                if val > 0.01:
                    i, j = divmod(idx, n_c)
                    allocations.append({
                        "source_warehouse": warehouses[i],
                        "destination_city": cities[j],
                        "units_allocated": round(val, 0),
                        "unit_cost": cost_matrix.get((warehouses[i], cities[j]), 999),
                        "total_cost": round(val * cost_matrix.get((warehouses[i], cities[j]), 999), 2)
                    })
            return pd.DataFrame(allocations)
        else:
            logger.warning(f"Optimization failed: {result.message}")
            return pd.DataFrame()


# ══════════════════════════════════════════════════════════════
# DEMO: Run with Synthetic Data
# ══════════════════════════════════════════════════════════════
def generate_synthetic_demand_data(n_skus=50, n_warehouses=5, days=180) -> pd.DataFrame:
    """Generate synthetic historical demand data."""
    np.random.seed(42)
    records = []
    sku_ids = range(1, n_skus + 1)
    warehouse_ids = range(1, n_warehouses + 1)
    base_date = datetime.now() - timedelta(days=days)

    for sku in sku_ids:
        for wh in warehouse_ids:
            base_demand = np.random.randint(2, 30)
            for d in range(days):
                date = base_date + timedelta(days=d)
                # Trend + seasonality + noise
                trend = d * 0.02
                seasonality = 5 * np.sin(2 * np.pi * d / 7)  # weekly
                noise = np.random.normal(0, 2)
                demand = max(0, int(base_demand + trend + seasonality + noise))
                records.append({
                    "sku_id": sku,
                    "warehouse_id": wh,
                    "category_id": (sku % 10) + 1,
                    "order_date": date.date(),
                    "units_sold": demand,
                })
    return pd.DataFrame(records)


if __name__ == "__main__":
    logger.info("=== Warehouse Optimizer Demo ===")

    # 1. Demand Forecasting
    df = generate_synthetic_demand_data(n_skus=20, n_warehouses=3, days=120)
    forecaster = DemandForecaster()
    model = forecaster.train(df)
    forecasts = forecaster.forecast(df)
    logger.info(f"Forecast sample:\n{forecasts.head(10).to_string(index=False)}")

    # 2. Reorder Optimization
    reorder_df = pd.DataFrame({
        "sku_id": range(1, 11),
        "warehouse_id": [1] * 10,
        "avg_daily_demand": np.random.uniform(2, 20, 10),
        "std_daily_demand": np.random.uniform(0.5, 5, 10),
        "lead_time_days": np.random.randint(2, 10, 10),
        "unit_cost": np.random.uniform(50, 2000, 10),
        "ordering_cost": [150.0] * 10,
        "current_stock": np.random.randint(0, 200, 10),
    })
    optimizer = ReorderOptimizer(service_level=0.95)
    reorder_plan = optimizer.calculate(reorder_df)
    logger.info(f"Reorder plan:\n{reorder_plan.to_string(index=False)}")

    # 3. Transfer Optimization
    transfer = TransferOptimizer()
    supply = {"BKK-01": 500, "BKK-02": 300, "CNX-01": 200}
    demand = {"Bangkok": 400, "Chiang Mai": 150, "Phuket": 200}
    costs = {
        ("BKK-01", "Bangkok"): 20, ("BKK-01", "Chiang Mai"): 80, ("BKK-01", "Phuket"): 120,
        ("BKK-02", "Bangkok"): 25, ("BKK-02", "Chiang Mai"): 70, ("BKK-02", "Phuket"): 130,
        ("CNX-01", "Bangkok"): 85, ("CNX-01", "Chiang Mai"): 15, ("CNX-01", "Phuket"): 200,
    }
    allocation = transfer.optimize(supply, demand, costs)
    logger.info(f"Transfer allocation:\n{allocation.to_string(index=False)}")

    logger.info("✅ Warehouse Optimizer Demo complete!")
