"""Template spot. Three sentences: hook, benefit, close."""

from millybays.models import Item, PriceQuote, RunContext, Transcript, spoken_price

DURATION_SECONDS = 12


class StubWriter:
    """Fill a Billy Mays template that quotes the price.

    A real writer composes the spot from the item and the quote. The stub
    keeps three sentences so the stub studio can map them onto three shots:
    a hook, the item description as the benefit, and a price plus a call to action.
    """

    def write(self, ctx: RunContext, item: Item, quote: PriceQuote) -> Transcript:
        price = spoken_price(quote.amount, quote.currency)
        hook = f"Hi, Billy Mays here for {item.name}!"
        benefit = item.description.strip()
        close = f"Yours for only {price}, so call now!"
        return Transcript(
            text=" ".join((hook, benefit, close)),
            duration_seconds=DURATION_SECONDS,
            spoken_price=price,
        )
