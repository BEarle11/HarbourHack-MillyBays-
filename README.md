# HarbourHack-MillyBays-

Print the EXIF data from an image.

## Setup

Create a virtual environment, activate it, and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The `.venv` directory already exists in this checkout. Skip the first command and activate it.

## Run

From the repository root, with the virtual environment active:

```bash
python milly_bays.py --image examples/images/chair.jpeg
```

To run the script without activating the environment, call the interpreter inside `.venv` directly:

```bash
.venv/bin/python milly_bays.py --image examples/images/chair.jpeg
```

The script prints one EXIF tag per line. A missing file exits with status 1. A readable image with no EXIF prints a short message and exits with status 0.
