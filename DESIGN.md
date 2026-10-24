# MillyBays

## Objective

Given an image, determine the object in the image, create an effective description of that object, determine its value, and produce a transcript for a short 10–15 second Billy Mays style advertisement.

The first implementation is a command-line tool. An HTTP API can sit in front of the same pipeline later. Every stage ships as a stub with the final input and output shape, so the product runs end to end while the internals are replaced one stage at a time.

## Pipeline

One image produces one primary item. Several objects in a frame are left for a later classifier, which still returns a single primary item.

`RunContext` carries the image, a timezone-aware clock reading, an optional location string, and the requested currency. Stages run in this order because the spoken spot quotes the price:

1. **Classifier** reads the context and returns an item.
2. **Pricer** reads the context and the item and returns a price quote.
3. **Writer** reads the context, the item, and the quote and returns a transcript.
4. **Studio** reads the context, the item, the quote, and the transcript and returns an ad package.

`run_pipeline(ctx, stages)` is the only orchestration entry point. The command-line tool parses arguments, loads the image, calls `run_pipeline`, and writes the folder. A future HTTP handler calls `run_pipeline` with the same context fields: an uploaded image, a location, a currency, and an optional timestamp.

A stage reports failure with `MillyBaysError(stage, message)`. The tool prints `stage: message` and exits 1. Unusable arguments and images raise `InputError` and exit 2.

## Types

Money is `decimal.Decimal` in memory and a two-decimal string in JSON. Timestamps are timezone-aware. A naive `--now` value is stored as UTC.

| Type | Fields |
| --- | --- |
| `ImageAsset` | `path`, `media_type`, `data`, `sha256` |
| `RunContext` | `image`, `captured_at`, `location`, `currency` |
| `Item` | `name`, `description`, `confidence` (`None` when the backend did not score it) |
| `PriceQuote` | `amount`, `currency`, `rationale`, `factors` |
| `Transcript` | `text`, `duration_seconds` (10 through 15), `spoken_price` |
| `Shot` | `start_seconds`, `end_seconds`, `visual`, `voiceover` |
| `AdPackage` | `title`, `duration_seconds`, `script`, `shots` |

`spoken_price` is `<amount> <currency>`, for example `19.95 USD`. The transcript text contains that phrase, the product name, one benefit, and a direct call to action.

Price factors, in this order:

| Key | Value |
| --- | --- |
| `captured_at` | ISO-8601 timestamp from the context |
| `location` | The location string, or `unspecified` when the caller omitted it |
| `currency` | Requested ISO 4217 code |
| `basis` | `stub` for this backend. A market pricer uses its own label |
| `item_name` | Item name the quote was built from |

The ad duration equals the transcript duration. Shots begin at 0, each shot starts where the previous one ends, and the last shot ends at the duration. Visuals may refer to the source image. This version writes no audio or video file.

## Ports

Each stage is a protocol. A replacement class implements one protocol and is passed to `run_pipeline` in a `Stages` value. The tool and the other stages stay as they are.

```text
Classifier.classify(ctx) -> Item
Pricer.price(ctx, item) -> PriceQuote
Writer.write(ctx, item, quote) -> Transcript
Studio.produce(ctx, item, quote, transcript) -> AdPackage
```

The installable core uses the Python standard library. Runtime dependencies stay empty until a replacement stage needs a library. The default backend id is `stub`.

## Command-line tool

```text
millybays <image> [--out DIR] [--location TEXT] [--currency CODE] [--now ISO-8601]
```

| Flag | Behavior |
| --- | --- |
| `image` | `.jpg`, `.jpeg`, `.png`, `.webp`, or `.gif`, compared case-insensitively. The file must exist, be a regular file, and be non-empty. The bytes are loaded as-is. |
| `--out` | Defaults to `out/<image-stem>/`. An existing directory at that path is replaced. |
| `--location` | Optional free text. Blank input is treated as omitted. |
| `--currency` | Three letters. Default `USD`. Stored in uppercase. The stub quotes in this currency and does no conversion. |
| `--now` | ISO-8601. A trailing `Z` means UTC. A value with no timezone is read as UTC. The default is the current UTC time. |

On success the process prints the item name, the spoken price, the transcript, and the output path, then exits 0.

The tool refuses to use the current directory, the home directory, a filesystem root, or any directory that contains the source image as the output directory. Replacing those paths would delete the photo or the working tree. A path that is an existing file is rejected too.

## Output

JSON is UTF-8, indented two spaces, with the field names from the types above. `transcript.txt` is the spoken text plus a trailing newline.

| File | Role |
| --- | --- |
| `item.json` | Classifier result |
| `price.json` | Pricer result. `amount` is a two-decimal string |
| `transcript.json` | Writer result |
| `transcript.txt` | Spoken text alone |
| `ad.json` | Studio result. `shots` is a list |
| `run.json` | `backend`, `source_path`, `image_sha256`, `captured_at`, `location`, `currency`, `artifacts` |

`run.json` stores `location` as JSON `null` when the flag was omitted. The price factors store `unspecified` for that same run, because that is the value the pricer used. `source_path` and the printed output path are absolute. `image_sha256` is the hex SHA-256 of the file bytes.

## Stub backend

Stubs are pure functions of their arguments. They leave the clock, the network, and the filesystem alone. The loader and the output writer are the only code that touches files.

**Classifier.** The name comes from the filename stem. Hyphens and underscores become spaces. A stem that is empty after that cleanup becomes `Untitled item`. The description states that classification is stubbed and includes the media type and the byte length. Confidence is `None`.

**Pricer.** The amount is one of `9.95`, `14.95`, … `49.95`, chosen by a SHA-256 of the image bytes and the item name, so the same bytes and name always produce the same amount. The rationale states that the figure is a stub and is not a market price. `basis` is `stub`.

**Writer.** A fixed template produces three sentences and a duration of 12 seconds: a hook that names the product, the item description as the benefit, and a close that speaks the price and says to call now. `spoken_price` is the amount and the currency code.

**Studio.** The three sentences become three shots over those 12 seconds. The first quarter is a title card with the hook. The middle half holds on the source image for the benefit. The last quarter is a price card with the close. `script` is the transcript text. The package title is `<name> with Billy Mays`.

## Later

Replace a stage by implementing its protocol. The command-line tool keeps calling `run_pipeline`.

- A classifier that reads pixels and returns a scored primary object.
- A pricer that uses the captured time, the location, and the history and current cost of the item. It still returns a `PriceQuote` in the requested currency.
- A writer that composes the spot, still 10–15 seconds, still quoting the price.
- A studio that renders audio or video from the shot list.
- An HTTP API whose request body matches `RunContext` and whose handler calls `run_pipeline`.
