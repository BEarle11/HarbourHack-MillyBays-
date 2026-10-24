"""Load a product photo as bytes. Pixel decoding belongs to a future classifier."""

import hashlib
from pathlib import Path

from millybays.errors import InputError
from millybays.models import ImageAsset

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

ACCEPTED_TYPES = ", ".join(MEDIA_TYPES)


def load_image(path: Path) -> ImageAsset:
    if not path.exists():
        raise InputError(f"Image not found: {path}")
    if not path.is_file():
        raise InputError(f"Image path is not a file: {path}")

    suffix = path.suffix.lower()
    media_type = MEDIA_TYPES.get(suffix)
    if media_type is None:
        shown = suffix or "(none)"
        raise InputError(f"Unsupported image type {shown}. Accepted types: {ACCEPTED_TYPES}.")

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise InputError(f"Cannot read image: {path}") from exc
    if not data:
        raise InputError(f"Image file is empty: {path}")

    return ImageAsset(
        path=path.resolve(),
        media_type=media_type,
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
    )
