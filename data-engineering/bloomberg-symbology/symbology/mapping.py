"""Bloomberg-style identifier mapping.

The shape every market-data desk has to build at some point: given a
security, the same instrument has 6 different identifiers (BBG, FIGI,
ISIN, CUSIP, SEDOL, RIC) and 4 different tickers per exchange. You need
a canonical instrument_id and a deterministic mapping table that handles
corporate actions, ticker changes, and the "this used to be a different
company" problem.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Instrument:
    instrument_id: str          # canonical internal id (UUID)
    bbg: str                    # "AAPL US Equity"
    figi: str                   # "BBG000B9XRY4"
    isin: str                   # "US0378331005"
    cusip: str = ""             # US only
    sedol: str = ""             # UK only
    ric: str = ""               # "AAPL.OQ"
    name: str = ""
    active: bool = True


@dataclass
class Mapping:
    instruments: dict[str, Instrument] = field(default_factory=dict)        # by instrument_id
    by_bbg: dict[str, str] = field(default_factory=dict)
    by_figi: dict[str, str] = field(default_factory=dict)
    by_isin: dict[str, str] = field(default_factory=dict)
    by_cusip: dict[str, str] = field(default_factory=dict)
    by_sedol: dict[str, str] = field(default_factory=dict)
    by_ric: dict[str, str] = field(default_factory=dict)
    history: list[tuple[str, str, str, str, str]] = field(default_factory=list)
    # (seq, instrument_id, field, old_value, new_value)

    def add(self, ins: Instrument) -> None:
        self.instruments[ins.instrument_id] = ins
        for store, val in [
            (self.by_bbg, ins.bbg),
            (self.by_figi, ins.figi),
            (self.by_isin, ins.isin),
            (self.by_cusip, ins.cusip),
            (self.by_sedol, ins.sedol),
            (self.by_ric, ins.ric),
        ]:
            if val:
                store[val] = ins.instrument_id

    def update(self, instrument_id: str, field_name: str, new_value: str, seq: int) -> None:
        ins = self.instruments[instrument_id]
        old = getattr(ins, field_name)
        # remove old from index
        old_store = getattr(self, f"by_{field_name}")
        old_store.pop(old, None)
        # set new
        setattr(ins, field_name, new_value)
        old_store[new_value] = instrument_id
        self.history.append((seq, instrument_id, field_name, old, new_value))

    def resolve(self, **kwargs) -> Optional[Instrument]:
        """Resolve any identifier to the canonical instrument."""
        for field_name, val in kwargs.items():
            if not val:
                continue
            store = getattr(self, f"by_{field_name}", {})
            iid = store.get(val)
            if iid:
                return self.instruments.get(iid)
        return None

    def merge(self, other_iid: str, into_iid: str, reason: str, seq: int):
        """Merge two instrument records (corporate action restate)."""
        other = self.instruments.pop(other_iid)
        for field_name in ["bbg", "figi", "isin", "cusip", "sedol", "ric"]:
            val = getattr(other, field_name)
            if val:
                getattr(self, f"by_{field_name}").pop(val, None)
        self.history.append((seq, into_iid, "merged", other_iid, reason))


if __name__ == "__main__":
    m = Mapping()
    aapl = Instrument(
        instrument_id="i-001", bbg="AAPL US Equity", figi="BBG000B9XRY4",
        isin="US0378331005", cusip="037833100", sedol="2046251", ric="AAPL.OQ",
        name="Apple Inc",
    )
    m.add(aapl)

    # Resolve from each identifier
    for kwargs in [
        {"bbg": "AAPL US Equity"},
        {"figi": "BBG000B9XRY4"},
        {"isin": "US0378331005"},
        {"cusip": "037833100"},
        {"sedol": "2046251"},
        {"ric": "AAPL.OQ"},
    ]:
        ins = m.resolve(**kwargs)
        print(f"{kwargs} -> {ins.name if ins else None}")

    # Ticker change: AAPL used to be on NYSE, moved to NASDAQ
    m.update("i-001", "ric", "AAPL.O", seq=1)
    # After the ticker change, the old RIC should not resolve anymore
    print(f"old RIC AAPL.OQ resolves: {m.resolve(ric='AAPL.OQ')}")
    print(f"new RIC AAPL.O  resolves: {m.resolve(ric='AAPL.O').name}")
