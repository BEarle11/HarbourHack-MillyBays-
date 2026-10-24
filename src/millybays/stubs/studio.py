"""Shot list for a 12-second spot. This stage writes no media."""

import re

from millybays.errors import MillyBaysError
from millybays.models import AdPackage, Item, PriceQuote, RunContext, Shot, Transcript, spoken_price

_SENTENCE = re.compile(r".+?[.!](?:\s+|$)")


class StubStudio:
    """Split the transcript into a hook, a hold on the source image, and a price card.

    A real studio renders audio or video from this shot list. Shots cover the
    transcript duration from 0, each one starting where the previous one ends.
    """

    def produce(
        self,
        ctx: RunContext,
        item: Item,
        quote: PriceQuote,
        transcript: Transcript,
    ) -> AdPackage:
        opening, middle, close = _voiceover_chunks(transcript.text)
        duration = transcript.duration_seconds
        hook_end = duration / 4
        hold_end = duration * 3 / 4
        end = float(duration)
        return AdPackage(
            title=f"{item.name} with Billy Mays",
            duration_seconds=duration,
            script=transcript.text,
            shots=(
                Shot(
                    start_seconds=0.0,
                    end_seconds=hook_end,
                    visual=f"Title card: {item.name}.",
                    voiceover=opening,
                ),
                Shot(
                    start_seconds=hook_end,
                    end_seconds=hold_end,
                    visual=f"Hold on the source image {ctx.image.path.name}.",
                    voiceover=middle,
                ),
                Shot(
                    start_seconds=hold_end,
                    end_seconds=end,
                    visual=f"Price card: {spoken_price(quote.amount, quote.currency)}.",
                    voiceover=close,
                ),
            ),
        )


def _voiceover_chunks(text: str) -> tuple[str, str, str]:
    sentences = [part.strip() for part in _SENTENCE.findall(text.strip())]
    sentences = [part for part in sentences if part]
    if len(sentences) < 3:
        raise MillyBaysError(
            "studio",
            "transcript needs a hook, a benefit, and a close",
        )
    return sentences[0], " ".join(sentences[1:-1]), sentences[-1]
