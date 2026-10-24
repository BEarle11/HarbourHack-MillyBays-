"""Deterministic placeholder price. The same image bytes and name always match."""

import hashlib
from decimal import Decimal

from millybays.models import PRICE_FACTOR_KEYS, Item, PriceQuote, RunContext, format_timestamp

# Retail-looking anchors. Step 0 is 9.95 and step 8 is 49.95.
_PRICE_ANCHORS = tuple(
    Decimal("9.95") + (Decimal(step) * Decimal("5.00")) for step in range(9)
)


def location_label(location: str | None) -> str:
    if location is None:
        return "unspecified"
    stripped = location.strip()
    return stripped or "unspecified"


class StubPricer:
    """Pick a stable .95 price from the image bytes and the item name.

    A real pricer uses the time, the location, and market history. This one
    records those inputs and sets basis to "stub".
    """

    def price(self, ctx: RunContext, item: Item) -> PriceQuote:
        amount = _PRICE_ANCHORS[_anchor_index(ctx.image.data, item.name)]
        factors = {
            "captured_at": format_timestamp(ctx.captured_at),
            "location": location_label(ctx.location),
            "currency": ctx.currency,
            "basis": "stub",
            "item_name": item.name,
        }
        factors = {key: factors[key] for key in PRICE_FACTOR_KEYS}
        return PriceQuote(
            amount=amount,
            currency=ctx.currency,
            rationale=f"Stub price for {item.name}. This amount is not a market price.",
            factors=factors,
        )


def _anchor_index(data: bytes, name: str) -> int:
    digest = hashlib.sha256(data + b"\0" + name.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % len(_PRICE_ANCHORS)
