"""Zillow-style real-estate listings service with geolocation search."""

from __future__ import annotations

import math
import time
from typing import Any, Optional

from common.ids import Snowflake
from common.storage import KeyValueStore

EARTH_RADIUS_KM = 6371.0088


def _now_ms() -> int:
    return int(time.time() * 1000)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two (lat, lng) points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _validate_listing(body: dict) -> None:
    if not isinstance(body.get("lat"), (int, float)):
        raise ValueError("lat required (number)")
    if not isinstance(body.get("lng"), (int, float)):
        raise ValueError("lng required (number)")
    if not (-90 <= body["lat"] <= 90):
        raise ValueError("lat out of range")
    if not (-180 <= body["lng"] <= 180):
        raise ValueError("lng out of range")
    if not isinstance(body.get("price"), (int, float)) or body["price"] < 0:
        raise ValueError("price required (non-negative number)")


class ZillowService:
    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        snowflake: Optional[Snowflake] = None,
    ):
        self.store = store or KeyValueStore("zillow", persist_path=None)
        self.id_gen = snowflake or Snowflake(machine_id=4)

    # ---- CRUD ---------------------------------------------------------

    def create_listing(
        self,
        lat: float,
        lng: float,
        price: float,
        beds: int = 0,
        baths: float = 0.0,
        sqft: int = 0,
        address: str = "",
    ) -> dict:
        body = {
            "lat": lat, "lng": lng, "price": price,
            "beds": beds, "baths": baths, "sqft": sqft, "address": address,
        }
        _validate_listing(body)
        lid = str(self.id_gen.next_id())
        rec = {
            "id": lid,
            "lat": float(lat),
            "lng": float(lng),
            "price": float(price),
            "beds": int(beds),
            "baths": float(baths),
            "sqft": int(sqft),
            "address": address or "",
            "created_at_ms": _now_ms(),
        }
        self.store.set(f"listing:{lid}", rec)
        idx = list(self.store.get("listings:index") or [])
        idx.append(lid)
        self.store.set("listings:index", idx)
        return rec

    def get_listing(self, listing_id: str) -> Optional[dict]:
        return self.store.get(f"listing:{listing_id}")

    # ---- Search -------------------------------------------------------

    def search(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0,
        max_price: Optional[float] = None,
        min_beds: Optional[int] = None,
        min_baths: Optional[float] = None,
        min_sqft: Optional[int] = None,
        limit: int = 50,
    ) -> dict:
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValueError("lat/lng out of range")
        idx = list(self.store.get("listings:index") or [])
        results: list[tuple[float, dict]] = []
        for lid in idx:
            rec = self.store.get(f"listing:{lid}")
            if not rec:
                continue
            if max_price is not None and rec["price"] > max_price:
                continue
            if min_beds is not None and rec["beds"] < min_beds:
                continue
            if min_baths is not None and rec["baths"] < min_baths:
                continue
            if min_sqft is not None and rec["sqft"] < min_sqft:
                continue
            d = haversine_km(lat, lng, rec["lat"], rec["lng"])
            if d > radius_km:
                continue
            out = dict(rec)
            out["distance_km"] = round(d, 3)
            results.append((d, out))
        results.sort(key=lambda t: t[0])
        top = results[:limit]
        return {
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
            "total": len(results),
            "results": [r for _, r in top],
        }

    # ---- Stats --------------------------------------------------------

    def stats(self) -> dict:
        return {
            "listings": len(self.store.get("listings:index") or []),
        }
