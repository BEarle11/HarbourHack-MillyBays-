from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from millybays.image_io import load_image
from millybays.models import PRICE_FACTOR_KEYS, RunContext, money_string
from millybays.pipeline import run_pipeline
from millybays.stubs import stub_stages
from millybays.stubs.classifier import name_from_filename


def test_pipeline_quotes_the_price_in_a_twelve_second_spot(context):
    result = run_pipeline(context, stub_stages())

    assert result.item.name == "widget"
    assert result.item.confidence is None
    assert "image/png" in result.item.description
    assert str(len(context.image.data)) in result.item.description

    amount = money_string(result.quote.amount)
    assert amount.endswith(".95")
    assert Decimal("9.95") <= result.quote.amount <= Decimal("49.95")
    assert result.quote.currency == "USD"
    assert result.quote.factors["basis"] == "stub"
    assert tuple(result.quote.factors) == PRICE_FACTOR_KEYS

    assert result.transcript.duration_seconds == 12
    assert result.transcript.spoken_price == f"{amount} USD"
    assert result.transcript.spoken_price in result.transcript.text
    assert result.item.name in result.transcript.text
    assert "call now" in result.transcript.text.lower()

    ad = result.ad
    assert ad.duration_seconds == result.transcript.duration_seconds
    assert ad.script == result.transcript.text
    assert ad.shots[0].start_seconds == 0
    assert ad.shots[-1].end_seconds == ad.duration_seconds
    for earlier, later in zip(ad.shots, ad.shots[1:]):
        assert earlier.end_seconds == later.start_seconds
        assert earlier.end_seconds > earlier.start_seconds
    assert result.transcript.spoken_price in ad.shots[-1].voiceover


def test_stub_price_is_stable_for_the_same_image(context):
    first = run_pipeline(context, stub_stages())
    second = run_pipeline(context, stub_stages())
    assert first.quote.amount == second.quote.amount
    assert first.transcript.text == second.transcript.text


def test_currency_is_passed_through_to_the_spoken_price(context):
    usd = run_pipeline(context, stub_stages())
    eur = run_pipeline(replace(context, currency="EUR"), stub_stages())

    assert usd.quote.amount == eur.quote.amount
    assert eur.quote.currency == "EUR"
    assert eur.quote.factors["currency"] == "EUR"
    assert eur.transcript.spoken_price.endswith(" EUR")
    assert "USD" not in eur.transcript.spoken_price


def test_missing_location_is_unspecified(context):
    result = run_pipeline(context, stub_stages())
    assert result.quote.factors["location"] == "unspecified"
    assert result.quote.factors["captured_at"] == "2026-10-24T12:00:00+00:00"


def test_explicit_location_is_recorded(context):
    result = run_pipeline(replace(context, location="Sydney"), stub_stages())
    assert result.quote.factors["location"] == "Sydney"


def test_item_name_comes_from_the_filename(tmp_path):
    path = tmp_path / "my-cool_hammer.png"
    path.write_bytes(b"\x89PNG\r\nhammer")
    named = replace_image(path)
    result = run_pipeline(named, stub_stages())
    assert result.item.name == "my cool hammer"
    assert result.item.name in result.transcript.text


def test_blank_filename_stem_uses_the_fallback_name(tmp_path):
    path = tmp_path / "---.png"
    assert name_from_filename(path) == "Untitled item"


def replace_image(path):
    return RunContext(
        image=load_image(path),
        captured_at=datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc),
        location=None,
        currency="USD",
    )
