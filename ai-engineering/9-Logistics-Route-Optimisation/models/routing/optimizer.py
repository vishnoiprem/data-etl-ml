"""
Route Optimisation Engine — Multi-Driver Last-Mile VRP

Implements a progressive stack of algorithms, each building on the previous:

  NN   Nearest-Neighbour greedy construction          (baseline)
  CW   Clarke-Wright Savings + capacity constraints   (+15–25% dist reduction)
  2OPT 2-opt local search applied to each CW route   (+5–10% further)
  ETA  ML-guided stop reordering using ETA model      (time-optimal, not just distance)

Usage:
    opt = RoutingOptimizer(eta_model_fn=predict_eta)   # pass None to skip ETA
    routes = opt.optimize(orders, drivers, traffic, mode="eta")
    comparison = opt.compare_algorithms(orders, drivers, traffic)
"""

import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import sys

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))
from data.generate_data import HUBS, ZONE_IDS, haversine


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class Stop:
    order_id:    str
    lat:         float
    lon:         float
    zone:        str
    weight_kg:   float
    urgency:     str
    sla_minutes: int
    order_time:  str


@dataclass
class Route:
    driver_id:          str
    hub_id:             str
    stops:              List[Stop] = field(default_factory=list)
    total_distance_km:  float = 0.0
    estimated_time_min: float = 0.0

    @property
    def n_stops(self) -> int:
        return len(self.stops)


# ── Distance utilities ─────────────────────────────────────────────────────────

def build_distance_matrix(locations: List[Tuple[float, float]]) -> np.ndarray:
    """N×N symmetric haversine distance matrix (km)."""
    n = len(locations)
    D = np.zeros((n, n))
    lats = np.array([p[0] for p in locations])
    lons = np.array([p[1] for p in locations])
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(lats[i], lons[i], lats[j], lons[j])
            D[i, j] = D[j, i] = d
    return D


def route_cost(indices: List[int], D: np.ndarray) -> float:
    """Total distance for an ordered sequence of matrix indices."""
    return sum(D[indices[k], indices[k + 1]] for k in range(len(indices) - 1))


# ── Algorithm primitives ───────────────────────────────────────────────────────

def nearest_neighbor(depot: int, customers: List[int], D: np.ndarray) -> List[int]:
    """Greedy NN tour: depot → nearest unvisited → … → depot."""
    unvisited = set(customers)
    tour = [depot]
    cur  = depot
    while unvisited:
        nxt = min(unvisited, key=lambda j: D[cur, j])
        tour.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    tour.append(depot)
    return tour


def two_opt(tour: List[int], D: np.ndarray, max_iter: int = 150) -> List[int]:
    """2-opt improvement: swap sub-segment reversals that reduce total cost."""
    best = tour[:]
    improved, it = True, 0
    while improved and it < max_iter:
        improved = False
        it += 1
        n = len(best)
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                before = D[best[i - 1], best[i]] + D[best[j], best[j + 1]]
                after  = D[best[i - 1], best[j]] + D[best[i], best[j + 1]]
                if after < before - 1e-9:
                    best[i: j + 1] = best[i: j + 1][::-1]
                    improved = True
    return best


def clarke_wright(
    depot: int,
    customers: List[int],
    D: np.ndarray,
    capacity: int,
    n_vehicles: int,
) -> List[List[int]]:
    """
    Clarke-Wright Savings Algorithm (parallel variant).

    Returns a list of tours, each starting and ending at depot.
    Merges routes by decreasing savings until capacity or vehicle count is satisfied.
    """
    if not customers:
        return []

    n_v = min(n_vehicles, len(customers))

    # Initialize: one route per customer
    routes     = {c: [depot, c, depot] for c in customers}
    membership = {c: c                  for c in customers}   # customer → route-key
    loads      = {c: 1                  for c in customers}   # packages per route

    # Savings matrix
    savings: List[Tuple[float, int, int]] = []
    for i in range(len(customers)):
        for j in range(i + 1, len(customers)):
            ci, cj = customers[i], customers[j]
            s = D[depot, ci] + D[depot, cj] - D[ci, cj]
            savings.append((s, ci, cj))
    savings.sort(reverse=True)

    for s, ci, cj in savings:
        ki = membership.get(ci)
        kj = membership.get(cj)
        if ki is None or kj is None or ki == kj:
            continue
        if loads[ki] + loads[kj] > capacity:
            continue

        ri, rj = routes[ki], routes[kj]

        # ci must be at the tail of ri, cj at the head of rj (or handle reversals)
        merged = None
        ri_body = ri[1:-1]
        rj_body = rj[1:-1]

        if ri_body[-1] == ci and rj_body[0] == cj:
            merged = [depot] + ri_body + rj_body + [depot]
        elif ri_body[-1] == cj and rj_body[0] == ci:
            merged = [depot] + ri_body + rj_body[::-1] + [depot]
        elif ri_body[0] == ci and rj_body[-1] == cj:
            merged = [depot] + ri_body[::-1] + rj_body + [depot]
        elif ri_body[0] == cj and rj_body[-1] == ci:
            merged = [depot] + rj_body + ri_body + [depot]

        if merged is None:
            continue

        # Commit merge
        new_load = loads[ki] + loads[kj]
        routes[ki] = merged
        loads[ki]  = new_load
        for c in rj_body:
            membership[c] = ki
        del routes[kj], loads[kj]

        if len(routes) <= n_v:
            break

    return list(routes.values())


# ── Optimizer class ────────────────────────────────────────────────────────────

class RoutingOptimizer:
    """
    Multi-driver route optimiser.

    Args:
        eta_model_fn: callable(features_df) → np.ndarray of predicted minutes.
                      Pass None to skip ETA-guided reordering.
    """

    def __init__(self, eta_model_fn: Optional[Callable] = None):
        self.eta_fn = eta_model_fn

    # ── Public API ─────────────────────────────────────────────────────────────

    def optimize(
        self,
        orders: pd.DataFrame,
        drivers: pd.DataFrame,
        traffic: pd.DataFrame,
        mode: str = "cw",
        current_hour: int = 9,
    ) -> Dict[str, Route]:
        """
        Compute optimised routes for all drivers.

        mode: "nn" | "cw" | "eta"
        Returns: {driver_id: Route}
        """
        tlookup = {
            (r.zone, r.hour): r.congestion_level
            for r in traffic[traffic.hour == current_hour].itertuples()
        }
        all_routes: Dict[str, Route] = {}
        for hub_id, hub_info in HUBS.items():
            h_ord = orders[orders["pickup_hub_id"] == hub_id].copy()
            h_drv = drivers[drivers["home_hub_id"] == hub_id].copy()
            if h_ord.empty or h_drv.empty:
                continue
            hub_routes = self._solve_hub(hub_id, hub_info, h_ord, h_drv, tlookup, mode, current_hour)
            all_routes.update(hub_routes)
        return all_routes

    def compare_algorithms(
        self,
        orders: pd.DataFrame,
        drivers: pd.DataFrame,
        traffic: pd.DataFrame,
        current_hour: int = 9,
    ) -> pd.DataFrame:
        """Run NN, CW, and ETA modes; return comparison DataFrame."""
        rows = []
        baseline_dist = None

        labels = {"nn": "Nearest-Neighbour", "cw": "Clarke-Wright + 2-opt", "eta": "CW + 2-opt + ETA-guided"}
        for mode, label in labels.items():
            t0 = time.time()
            routes = self.optimize(orders, drivers, traffic, mode=mode, current_hour=current_hour)
            elapsed = time.time() - t0

            total_dist  = sum(r.total_distance_km  for r in routes.values())
            total_time  = sum(r.estimated_time_min for r in routes.values())
            n_active    = sum(1 for r in routes.values() if r.n_stops > 0)
            n_orders    = sum(r.n_stops for r in routes.values())

            if baseline_dist is None:
                baseline_dist = total_dist

            saved_pct = (1 - total_dist / baseline_dist) * 100 if baseline_dist else 0

            rows.append({
                "Algorithm":            label,
                "Total Distance (km)":  round(total_dist,  1),
                "Total Time (h)":       round(total_time / 60, 2),
                "Distance Saved (%)":   round(saved_pct,   1),
                "Drivers Used":         n_active,
                "Orders Routed":        n_orders,
                "Runtime (s)":          round(elapsed,     3),
            })

        return pd.DataFrame(rows)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _solve_hub(self, hub_id, hub_info, orders, drivers, tlookup, mode, hour) -> Dict[str, Route]:
        # Build location list: index 0 = depot, 1..N = orders
        locations = [(hub_info["lat"], hub_info["lon"])]
        stops_list: List[Stop] = []
        for _, row in orders.iterrows():
            locations.append((row["dropoff_lat"], row["dropoff_lon"]))
            stops_list.append(Stop(
                order_id    = row["order_id"],
                lat         = row["dropoff_lat"],
                lon         = row["dropoff_lon"],
                zone        = row.get("dropoff_zone", "CENTRAL"),
                weight_kg   = float(row.get("package_weight_kg", 2.0)),
                urgency     = row.get("urgency", "standard"),
                sla_minutes = int(row.get("sla_minutes", 240)),
                order_time  = row.get("order_time", ""),
            ))

        D = build_distance_matrix(locations)
        depot   = 0
        cust    = list(range(1, len(stops_list) + 1))
        n_drv   = len(drivers)
        # Per-driver capacity: ceil(orders/drivers) + small slack for rounding
        import math
        cap     = math.ceil(len(cust) / max(n_drv, 1)) + 2

        # ── Build tours ────────────────────────────────────────────────────────
        if mode == "nn":
            # Split customers evenly, NN per driver
            chunks = np.array_split(cust, n_drv)
            raw_tours = [nearest_neighbor(depot, list(ch), D) for ch in chunks if len(ch) > 0]
        else:
            raw_tours = clarke_wright(depot, cust, D, capacity=cap, n_vehicles=n_drv)
            raw_tours = [two_opt(t, D) for t in raw_tours]

        # ── Assign tours to drivers ────────────────────────────────────────────
        result: Dict[str, Route] = {}
        drivers_reset = drivers.reset_index(drop=True)

        for i, (_, drv_row) in enumerate(drivers_reset.iterrows()):
            if i >= len(raw_tours):
                break
            tour = raw_tours[i]
            tour_stops = [stops_list[idx - 1] for idx in tour if idx > 0]

            if mode == "eta" and self.eta_fn and tour_stops:
                tour_stops = self._eta_reorder(tour_stops, drv_row, hour, tlookup)

            total_dist = route_cost(tour, D)
            result[drv_row["driver_id"]] = Route(
                driver_id          = drv_row["driver_id"],
                hub_id             = hub_id,
                stops              = tour_stops,
                total_distance_km  = round(total_dist, 3),
                estimated_time_min = self._estimate_time(total_dist, tour_stops, hour, tlookup),
            )
        return result

    def _eta_reorder(self, stops: List[Stop], drv_row, hour: int, tlookup: dict) -> List[Stop]:
        """Sort stops by ascending ML-predicted ETA so fastest deliveries come first."""
        if not self.eta_fn:
            return stops
        try:
            rows = [
                {
                    "distance_km":        haversine(HUBS["hub_central"]["lat"], HUBS["hub_central"]["lon"], s.lat, s.lon),
                    "hub_to_dropoff_km":  haversine(HUBS["hub_central"]["lat"], HUBS["hub_central"]["lon"], s.lat, s.lon) * 1.1,
                    "hour_of_day":        hour,
                    "day_of_week":        1,
                    "is_weekend":         0,
                    "is_peak_hour":       int(7 <= hour <= 9 or 17 <= hour <= 19),
                    "zone_id":            ZONE_IDS.get(s.zone, 0),
                    "hub_id_enc":         0,
                    "congestion_at_time": tlookup.get((s.zone, hour), 0.40),
                    "weather_severity":   0.0,
                    "package_weight_kg":  s.weight_kg,
                    "stop_number":        i,
                    "log_experience":     np.log1p(int(drv_row.get("experience_days", 365))),
                    "speed_factor":       float(drv_row.get("speed_factor", 1.0)),
                    "urgency_enc":        {"same_day": 2, "express": 1, "standard": 0}.get(s.urgency, 0),
                }
                for i, s in enumerate(stops)
            ]
            etas = self.eta_fn(pd.DataFrame(rows))
            # Sort key: urgency priority first (same_day < express < standard),
            # then ascending ETA within urgency class
            urg_order = {"same_day": 0, "express": 1, "standard": 2}
            return [
                s for _, s in sorted(
                    zip(etas, stops),
                    key=lambda x: (urg_order.get(x[1].urgency, 2), x[0]),
                )
            ]
        except Exception:
            return stops

    @staticmethod
    def _estimate_time(dist_km: float, stops: List[Stop], hour: int, tlookup: dict) -> float:
        if not stops:
            return 0.0
        avg_cong  = np.mean([tlookup.get((s.zone, hour), 0.40) for s in stops])
        eff_speed = max(25.0 * (1 - 0.75 * avg_cong), 5.0)
        return round((dist_km / eff_speed) * 60 + len(stops) * 5.0, 1)
