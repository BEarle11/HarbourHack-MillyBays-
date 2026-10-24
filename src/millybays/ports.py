"""Stage interfaces. A replacement backend implements these and nothing else changes."""

from typing import Protocol

from millybays.models import AdPackage, Item, PriceQuote, RunContext, Transcript


class Classifier(Protocol):
    def classify(self, ctx: RunContext) -> Item:
        """Name and describe the primary object in the image."""


class Pricer(Protocol):
    def price(self, ctx: RunContext, item: Item) -> PriceQuote:
        """Recommend a price for the item in the context currency."""


class Writer(Protocol):
    def write(self, ctx: RunContext, item: Item, quote: PriceQuote) -> Transcript:
        """Write a 10–15 second Billy Mays spot that quotes the price."""


class Studio(Protocol):
    def produce(
        self,
        ctx: RunContext,
        item: Item,
        quote: PriceQuote,
        transcript: Transcript,
    ) -> AdPackage:
        """Turn the spot into a timed shot list. Media files are a later studio."""
