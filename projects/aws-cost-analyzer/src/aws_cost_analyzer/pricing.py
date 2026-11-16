"""The S3 rate card, and the measured/modelled split.

Every dollar figure in this project comes from one of three places, and
the report says which:

``measured``
    The number is in a cost record. It came off the bill.

``modelled``
    The number is a volume multiplied by a rate from the card below. The
    volume must be attached as evidence — a modelled figure with no
    volume behind it is a guess wearing a number.

``upper_bound``
    The quantity itself could not be measured (per-prefix bytes without
    S3 Inventory, for instance), so the figure is a ceiling on it.

The card below is **illustrative**: rounded, hand-checked against AWS's
published us-east-1 pricing, and declared as belonging to one region.
Analysing ap-southeast-1 with us-east-1 rates means the report says so
rather than quietly pretending the numbers transfer.

Nothing here is fetched from the Pricing API by default. The price list is
large, the download is slow, and the numbers move often enough that a
stale hardcoded card with a visible "checked on" date is more honest than
a card that silently changes under the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# The card
# --------------------------------------------------------------------------- #

#: The region these rates describe.
RATE_CARD_REGION = "us-east-1"

#: When the rates below were last hand-checked against AWS's pricing pages.
RATE_CARD_CHECKED_ON = "2026-11-16"

#: ILLUSTRATIVE 2026 us-east-1 S3 storage rates, USD per GB-month.
STORAGE_USD_PER_GB_MONTH = {
    "STANDARD": 0.023,
    "STANDARD_IA": 0.0125,
    "ONEZONE_IA": 0.010,
    "GLACIER_IR": 0.004,
    "GLACIER": 0.0036,
    "DEEP_ARCHIVE": 0.00099,
}

#: ILLUSTRATIVE 2026 us-east-1 S3 request rates, USD per 1,000 requests.
REQUESTS_USD_PER_1000 = {
    "GET": 0.0004,
    "PUT": 0.005,
    "POST": 0.005,
    "LIST": 0.005,
    "DELETE": 0.0,
    "HEAD": 0.0004,
}

#: ILLUSTRATIVE 2026 us-east-1 retrieval charges, USD per GB retrieved.
RETRIEVAL_USD_PER_GB = {
    "GLACIER_IR": 0.03,
    "GLACIER": 0.01,
    "DEEP_ARCHIVE": 0.0002,
}

#: The storage classes a lifecycle rule may transition *to*.
TARGET_CLASSES = ("STANDARD_IA", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")


# --------------------------------------------------------------------------- #
# The card object
# --------------------------------------------------------------------------- #


@dataclass(slots=True, frozen=True)
class RateCard:
    """A rate card with a declared region.

    The region is part of the card, not a footnote, because using
    us-east-1 rates on an ap-southeast-1 account is a mistake the report
    must surface — not a detail the reader has to remember.
    """

    region: str = RATE_CARD_REGION
    checked_on: str = RATE_CARD_CHECKED_ON
    storage: dict[str, float] = None  # type: ignore[assignment]
    requests: dict[str, float] = None  # type: ignore[assignment]
    retrieval: dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.storage is None:
            object.__setattr__(self, "storage", dict(STORAGE_USD_PER_GB_MONTH))
        if self.requests is None:
            object.__setattr__(self, "requests", dict(REQUESTS_USD_PER_1000))
        if self.retrieval is None:
            object.__setattr__(self, "retrieval", dict(RETRIEVAL_USD_PER_GB))

    # -- storage ----------------------------------------------------------- #

    def storage_rate(self, storage_class: str) -> float:
        """The monthly storage rate for a class, in USD per GB-month."""
        return self.storage.get(storage_class.upper(), self.storage["STANDARD"])

    def storage_cost(self, gb: float, storage_class: str) -> float:
        """The monthly storage cost of ``gb`` gigabytes in a class."""
        return gb * self.storage_rate(storage_class)

    # -- requests ---------------------------------------------------------- #

    def request_rate(self, request_type: str) -> float:
        """The rate for a request type, in USD per 1,000 requests."""
        return self.requests.get(request_type.upper(), self.requests["GET"])

    def request_cost(self, count: float, request_type: str) -> float:
        """The cost of ``count`` requests of a type."""
        return (count / 1000.0) * self.request_rate(request_type)

    # -- retrieval --------------------------------------------------------- #

    def retrieval_rate(self, storage_class: str) -> float:
        """The retrieval charge per GB for a class."""
        return self.retrieval.get(storage_class.upper(), 0.0)

    def retrieval_cost(self, gb: float, storage_class: str) -> float:
        """The one-off retrieval cost of pulling ``gb`` back out."""
        return gb * self.retrieval_rate(storage_class)

    # -- transitions ------------------------------------------------------- #

    def transition_saving(
        self,
        gb: float,
        from_class: str,
        to_class: str,
        monthly_retrieval_gb: float = 0.0,
    ) -> float:
        """The monthly net saving from moving objects between classes.

        The retrieval charge is subtracted because a transition is only
        free if the objects are never read back. A glacier transition on
        data that is read every month is a cost, not a saving, and the
        arithmetic here is what makes that visible instead of leaving it
        as a footnote.

        Returns ``0.0`` when the move would not pay for itself.
        """
        current = self.storage_cost(gb, from_class)
        proposed = self.storage_cost(gb, to_class)
        retrieval = self.retrieval_cost(monthly_retrieval_gb, to_class)
        net = current - proposed - retrieval
        return net if net > 0 else 0.0

    # -- region ------------------------------------------------------------ #

    def matches_region(self, region: str) -> bool:
        """Whether the card's region is the region being analysed."""
        return self.region.upper() == region.upper()

    def region_mismatch_note(self, region: str) -> str:
        """A sentence stating the mismatch, or an empty string."""
        if self.matches_region(region):
            return ""
        return (
            f"Rates are the {self.region} card (checked {self.checked_on}) "
            f"but the analysis region is {region}. Figures marked 'modelled' "
            f"are therefore indicative, not authoritative."
        )


def default_card() -> RateCard:
    """The illustrative card."""
    return RateCard()


# --------------------------------------------------------------------------- #
# Request classification
# --------------------------------------------------------------------------- #

#: The request types the access-log classifier emits.
OP_GET = "GET"
OP_PUT = "PUT"
OP_POST = "POST"
OP_LIST = "LIST"
OP_DELETE = "DELETE"
OP_HEAD = "HEAD"


def classify_request(operation: str, key: str = "") -> str:
    """Classify an S3 request into a billable request type.

    The subtlety is ``REST.GET.BUCKET``. A ``GET`` on a *bucket* is a
    LIST — the console's "list objects" — and it is billed at the LIST
    rate, which is roughly ten times the GET rate. Classifying it as a
    GET understates the cost of a scanner by an order of magnitude, so
    the bucket form is checked before the object form.

    A ``GET`` with no key at all is also a list (ListObjectsV2).
    """
    op = operation.upper().strip()

    if op == "REST.GET.BUCKET":
        return OP_LIST

    if op.startswith("REST."):
        op = op.removeprefix("REST.")

    # "GET.OBJECT" -> "GET", "PUT.OBJECT" -> "PUT", "DELETE.OBJECT" -> "DELETE".
    op = op.split(".", 1)[0]

    if op == "GET":
        # A GET with no object key is a list of the bucket.
        return OP_LIST if not key or key in ("", "/") else OP_GET
    if op.startswith("PUT"):
        return OP_PUT
    if op.startswith("POST"):
        return OP_POST
    if op.startswith("DELETE"):
        return OP_DELETE
    if op.startswith("HEAD"):
        return OP_HEAD
    return OP_GET
