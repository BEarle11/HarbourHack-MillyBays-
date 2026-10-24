import hashlib
import json
from pathlib import Path

from millybays.cli import main
from millybays.errors import MillyBaysError
from millybays.pipeline import Stages
from millybays.stubs import stub_stages


def test_cli_writes_artifacts_and_replaces_an_existing_directory(tmp_path, capsys):
    image = tmp_path / "widget.PNG"
    image.write_bytes(b"\x89PNG\r\ncli-image")
    destination = tmp_path / "run"
    destination.mkdir()
    (destination / "old.txt").write_text("junk", encoding="utf-8")

    code = main(
        [
            str(image),
            "--out",
            str(destination),
            "--now",
            "2026-10-24T15:30:00",
            "--currency",
            "aud",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    assert not (destination / "old.txt").exists()

    item = _read(destination / "item.json")
    price = _read(destination / "price.json")
    transcript = _read(destination / "transcript.json")
    ad = _read(destination / "ad.json")
    run = _read(destination / "run.json")
    spoken = (destination / "transcript.txt").read_text(encoding="utf-8")

    assert item["name"] == "widget"
    assert item["confidence"] is None
    assert price["currency"] == "AUD"
    assert price["amount"].endswith(".95")
    assert price["factors"]["location"] == "unspecified"
    assert price["factors"]["captured_at"] == "2026-10-24T15:30:00+00:00"
    assert price["factors"]["basis"] == "stub"
    assert transcript["spoken_price"] == f"{price['amount']} AUD"
    assert spoken == transcript["text"] + "\n"
    assert ad["script"] == transcript["text"]
    assert ad["duration_seconds"] == 12
    assert run["backend"] == "stub"
    assert run["source_path"] == str(image.resolve())
    assert run["image_sha256"] == hashlib.sha256(image.read_bytes()).hexdigest()
    assert run["location"] is None
    assert run["currency"] == "AUD"
    assert set(run["artifacts"]) == {
        "item",
        "price",
        "transcript",
        "transcript_text",
        "ad",
    }

    lines = captured.out.splitlines()
    assert lines[0] == "widget"
    assert lines[1] == f"{price['amount']} AUD"
    assert lines[2] == transcript["text"]
    assert lines[3] == str(destination.resolve())


def test_cli_defaults_to_out_stem(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    image = tmp_path / "hammer.PNG"
    image.write_bytes(b"\x89PNG\r\ndefault")

    code = main([str(image), "--now", "2026-10-24T12:00:00Z"])

    assert code == 0
    capsys.readouterr()
    run = _read(tmp_path / "out" / "hammer" / "run.json")
    assert run["captured_at"] == "2026-10-24T12:00:00+00:00"
    assert run["backend"] == "stub"


def test_cli_records_location_and_now(tmp_path, capsys):
    image = tmp_path / "widget.png"
    image.write_bytes(b"\x89PNG\r\nlocated")
    destination = tmp_path / "located"

    code = main(
        [
            str(image),
            "--out",
            str(destination),
            "--location",
            " Sydney ",
            "--now",
            "2026-10-24T09:00:00+11:00",
        ]
    )

    assert code == 0
    capsys.readouterr()
    price = _read(destination / "price.json")
    run = _read(destination / "run.json")
    assert price["factors"]["location"] == "Sydney"
    assert price["factors"]["captured_at"] == "2026-10-24T09:00:00+11:00"
    assert run["location"] == "Sydney"
    assert run["captured_at"] == "2026-10-24T09:00:00+11:00"


def test_cli_rejects_a_missing_image(tmp_path, capsys):
    destination = tmp_path / "missing-out"
    code = main([str(tmp_path / "nope.png"), "--out", str(destination)])
    captured = capsys.readouterr()
    assert code == 2
    assert "Image not found" in captured.err
    assert captured.out == ""
    assert not destination.exists()


def test_cli_rejects_an_unsupported_suffix(tmp_path, capsys):
    notes = tmp_path / "notes.txt"
    notes.write_text("hello", encoding="utf-8")
    destination = tmp_path / "notes-out"
    code = main([str(notes), "--out", str(destination)])
    captured = capsys.readouterr()
    assert code == 2
    assert "Unsupported image type .txt" in captured.err
    assert not destination.exists()


def test_cli_rejects_an_empty_image(tmp_path, capsys):
    image = tmp_path / "empty.png"
    image.write_bytes(b"")
    destination = tmp_path / "empty-out"
    code = main([str(image), "--out", str(destination)])
    captured = capsys.readouterr()
    assert code == 2
    assert "empty" in captured.err
    assert not destination.exists()


def test_cli_rejects_a_bad_currency(tmp_path, capsys):
    image = tmp_path / "widget.png"
    image.write_bytes(b"\x89PNG\r\ncurrency")
    destination = tmp_path / "currency-out"
    code = main([str(image), "--out", str(destination), "--currency", "US"])
    captured = capsys.readouterr()
    assert code == 2
    assert "three-letter" in captured.err
    assert not destination.exists()


def test_stage_failure_exits_1_and_writes_nothing(tmp_path, monkeypatch, capsys):
    image = tmp_path / "widget.png"
    image.write_bytes(b"\x89PNG\r\nboom")
    destination = tmp_path / "boom-out"
    healthy = stub_stages()

    class Boom:
        def classify(self, ctx):
            raise MillyBaysError("classifier", "model unavailable")

    def failing_stages():
        return Stages(
            classifier=Boom(),
            pricer=healthy.pricer,
            writer=healthy.writer,
            studio=healthy.studio,
        )

    monkeypatch.setattr("millybays.cli.stub_stages", failing_stages)
    code = main([str(image), "--out", str(destination)])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.err == "classifier: model unavailable\n"
    assert captured.out == ""
    assert not destination.exists()


def test_cli_refuses_to_replace_the_working_directory(tmp_path, monkeypatch, capsys):
    work = tmp_path / "work"
    pics = tmp_path / "pics"
    work.mkdir()
    pics.mkdir()
    image = pics / "widget.png"
    image.write_bytes(b"\x89PNG\r\nkeep")
    sentinel = work / "keep.txt"
    sentinel.write_text("stay", encoding="utf-8")
    monkeypatch.chdir(work)

    code = main([str(image), "--out", str(work)])
    captured = capsys.readouterr()
    assert code == 2
    assert "Refusing to replace" in captured.err
    assert sentinel.read_text(encoding="utf-8") == "stay"
    assert image.read_bytes().startswith(b"\x89PNG")


def test_cli_refuses_to_replace_the_image_directory(tmp_path, capsys):
    image = tmp_path / "widget.png"
    image.write_bytes(b"\x89PNG\r\nstay")
    code = main([str(image), "--out", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "Refusing to replace" in captured.err
    assert image.read_bytes().startswith(b"\x89PNG")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
