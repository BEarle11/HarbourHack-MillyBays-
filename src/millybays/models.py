"""Records that move between the four stages."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Mapping

# Pricing factors, in the order they are written to price.json.
PRICE_FACTOR_KEYS = (
    "captured_at",
    "location",
    "currency",
    "basis",
    "item_name",
)


@dataclass(frozen=True)
class ImageAsset:
    path: Path
    media_type: str
    data: bytes
    sha256: str


@dataclass(frozen=True)
class RunContext:
    """Everything a stage may use besides the records from earlier stages."""

    image: ImageAsset
    captured_at: datetime
    location: str | None
    currency: str


@dataclass(frozen=True)
class Item:
    name: str
    description: str
    confidence: float | None = None


@dataclass(frozen=True)
class PriceQuote:
    amount: Decimal
    currency: str
    rationale: str
    factors: Mapping[str, str]


@dataclass(frozen=True)
class Transcript:
    text: str
    duration_seconds: int
    spoken_price: str


@dataclass(frozen=True)
class Shot:
    start_seconds: float
    end_seconds: float
    visual: str
    voiceover: str


@dataclass(frozen=True)
class AdPackage:
    title: str
    duration_seconds: int
    script: str
    shots: tuple[Shot, ...]


@dataclass(frozen=True)
class PipelineResult:
    item: Item
    quote: PriceQuote
    transcript: Transcript
    ad: AdPackage


def money_string(amount: Decimal) -> str:
    """Two-decimal text for an amount. JSON stores this string."""
    return f"{amount.quantize(Decimal('0.01')):.2f}"


def spoken_price(amount: Decimal, currency: str) -> str:
    return f"{money_string(amount)} {currency}"


def format_timestamp(value: datetime) -> str:
    return value.isoformat()


def item_payload(item: Item) -> dict[str, object]:
    return {
        "name": item.name,
        "description": item.description,
        "confidence": item.confidence,
    }


def price_payload(quote: PriceQuote) -> dict[str, object]:
    return {
        "amount": money_string(quote.amount),
        "currency": quote.currency,
        "rationale": quote.rationale,
        "factors": {key: quote.factors[key] for key in PRICE_FACTOR_KEYS},
    }


def transcript_payload(transcript: Transcript) -> dict[str, object]:
    return {
        "text": transcript.text,
        "duration_seconds": transcript.duration_seconds,
        "spoken_price": transcript.spoken_price,
    }


def ad_payload(ad: AdPackage) -> dict[str, object]:
    return {
        "title": ad.title,
        "duration_seconds": ad.duration_seconds,
        "script": ad.script,
        "shots": [
            {
                "start_seconds": shot.start_seconds,
                "end_seconds": shot.end_seconds,
                "visual": shot.visual,
                "voiceover": shot.voiceover,
            }
            for shot in ad.shots
        ],
    }
