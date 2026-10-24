"""Command-line entry point. Parsing and printing stay here; stages stay behind run_pipeline."""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from millybays.errors import InputError, MillyBaysError
from millybays.image_io import ACCEPTED_TYPES, load_image
from millybays.models import RunContext, spoken_price
from millybays.output import write_run
from millybays.pipeline import run_pipeline
from millybays.stubs import BACKEND_ID, stub_stages

_CURRENCY = re.compile(r"^[A-Za-z]{3}$")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        currency = _currency(args.currency)
        captured_at = _captured_at(args.now)
        location = _location(args.location)
        image_path = Path(args.image)
        image = load_image(image_path)
        if args.out is not None:
            destination = Path(args.out)
        else:
            destination = Path("out") / (image_path.stem or "untitled")
        context = RunContext(
            image=image,
            captured_at=captured_at,
            location=location,
            currency=currency,
        )
        result = run_pipeline(context, stub_stages())
        written = write_run(destination, context, result, backend=BACKEND_ID)
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except MillyBaysError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    price = spoken_price(result.quote.amount, result.quote.currency)
    print(result.item.name)
    print(price)
    print(result.transcript.text)
    print(written)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="millybays",
        description="Turn a product photo into a price and a short Billy Mays ad.",
    )
    parser.add_argument("image", help=f"Product photo ({ACCEPTED_TYPES})")
    parser.add_argument(
        "--out",
        type=Path,
        help="Output directory. Defaults to out/<image-stem>/ and replaces an existing directory.",
    )
    parser.add_argument("--location", help="Free-text place used by the pricer, such as a city.")
    parser.add_argument(
        "--currency",
        default="USD",
        help="ISO 4217 currency code (default: USD).",
    )
    parser.add_argument(
        "--now",
        help="ISO-8601 timestamp for the quote. A value with no timezone is read as UTC.",
    )
    return parser


def _currency(value: str) -> str:
    if not _CURRENCY.fullmatch(value):
        raise InputError("Currency must be a three-letter ISO 4217 code.")
    return value.upper()


def _location(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _captured_at(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise InputError(f"Invalid --now timestamp: {value}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
