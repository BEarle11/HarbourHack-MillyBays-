# HarbourHack-MillyBays-

Upload a photo of something in your house. Milly Bays identifies it, estimates
its resale value, writes a Facebook Marketplace listing, and produces a Billy
Mays-style ad.

## Setup

Create a virtual environment, activate it, and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The `.venv` directory already exists in this checkout. Skip the first command and activate it.

## Run the web app

```bash
.venv/bin/python server.py
```

Open http://localhost:5000, upload a photo, hit SELL IT.

## Print EXIF data from an image

From the repository root, with the virtual environment active:

```bash
python milly_bays.py --image examples/images/chair.jpeg
```

To run the script without activating the environment, call the interpreter inside `.venv` directly:

```bash
.venv/bin/python milly_bays.py --image examples/images/chair.jpeg
```

The script prints one EXIF tag per line. A missing file exits with status 1. A readable image with no EXIF prints a short message and exits with status 0.

## Configuration

| Env var | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | MiniMax API key (required). |
| `ANTHROPIC_BASE_URL` | Defaults to MiniMax's Anthropic-compatible endpoint. |
| `MILLY_MODEL` | Chat model, default `MiniMax-M3.1-Flash`. |
| `ELEVENLABS_API_KEY` | Optional. Enables live Seedance video generation; without it the app falls back to the transcript plus the demo video in `examples/video/`. |
| `MILLY_VIDEO_MODEL` | Video model id, default `bytedance-seedance-v2.5`. |

## Pipeline

`POST /api/classify` (image upload) → `POST /api/price` → `POST /api/write` →
`POST /api/studio`. See DESIGN.md.
