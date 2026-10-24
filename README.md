# MillyBays

Turn a product photo into a price and a short Billy Mays ad.

You pass one image. The tool names the object, prices it, writes a 12-second spot that quotes that price, and saves a shot list. This version fills every stage with a deterministic stub, so the path from photo to output folder runs before any model is wired up. The sentences and the price are placeholders. The files have the shape a later classifier, pricer, writer, or studio will fill in.

The contracts live in [DESIGN.md](DESIGN.md).

## Install

Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The core package depends only on the standard library. `pytest` is a development extra.

## Run

```bash
millybays photo.png --location Sydney --currency AUD
```

A run prints the item name, the price, the transcript, and the output directory. The default directory is `out/<image-stem>/`. An existing directory at that path is replaced.

```bash
millybays photo.png --out runs/photo --now 2026-10-24T12:00:00Z
```

Accepted photos are `.jpg`, `.jpeg`, `.png`, `.webp`, and `.gif`. The check uses the file suffix and requires a non-empty file. This version reads the bytes and does not decode pixels.

`--currency` is a three-letter ISO 4217 code and defaults to `USD`. The stub quotes in that currency. `--location` is optional free text. `--now` is an ISO-8601 timestamp; a value with no timezone is read as UTC. The default clock is the current UTC time.

Exit `0` means the folder was written. Exit `2` means the invocation or the image is unusable. Exit `1` means a stage failed.

## Output

| File | Contents |
| --- | --- |
| `item.json` | Name, description, and confidence |
| `price.json` | Amount, currency, rationale, and pricing factors |
| `transcript.json` | Spoken text, duration, and the spoken price |
| `transcript.txt` | Spoken text alone |
| `ad.json` | Title, script, and timed shots |
| `run.json` | Backend id, source path, image hash, clock, location, and currency |

`run.json` records `"backend": "stub"`. Amounts are two-decimal strings. Confidence is `null` while classification is stubbed.

## Tests

```bash
pytest
```
