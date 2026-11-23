"""TMS — E-commerce Logistics.

A transport management system for e-commerce last-mile delivery, modelled on
how marketplaces like Lazada and Shopee and the carriers behind them
(Ninja Van, J&T, Delhivery) actually run their networks.

The package is organised as a pipeline:

    corpus -> risk -> dispatch -> routing -> eta -> delivery -> sla -> metrics

Every module is a pure function over data. The one piece of stateful
wiring lives in :mod:`tms.service`.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "audit",
    "config",
    "corpus",
    "delivery",
    "dispatch",
    "eta",
    "fraud",
    "lifecycle",
    "metrics",
    "models",
    "routing",
    "service",
    "sla",
]
