"""Read an image and print its EXIF tags."""

import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import GPSTAGS, IFD, TAGS

# These tags are pointers to nested IFDs. The nested tags are printed separately.
IFD_POINTERS = {IFD.Exif, IFD.GPSInfo, IFD.Interop}


def render(value):
    if isinstance(value, bytes):
        if len(value) == 1:
            return str(value[0])
        text = value.split(b"\x00", 1)[0]
        try:
            decoded = text.decode("ascii")
        except UnicodeDecodeError:
            decoded = ""
        if decoded and decoded.isprintable():
            return decoded
        return f"<{len(value)} bytes>"
    if isinstance(value, tuple):
        return " ".join(render(item) for item in value)
    return str(value).strip()


def tag_lines(exif, names):
    lines = []
    for tag_id, value in exif.items():
        if tag_id in IFD_POINTERS:
            continue
        name = names.get(tag_id, str(tag_id))
        lines.append(f"{name}: {render(value)}")
    return lines


def exif_lines(image):
    exif = image.getexif()
    lines = tag_lines(exif, TAGS)
    lines.extend(tag_lines(exif.get_ifd(IFD.Exif), TAGS))
    lines.extend(tag_lines(exif.get_ifd(IFD.GPSInfo), GPSTAGS))
    return lines


def print_exif(path):
    """Print EXIF tags for an image. Return a process exit code."""
    path = Path(path)
    if not path.is_file():
        print(f"Image not found: {path}", file=sys.stderr)
        return 1

    try:
        with Image.open(path) as image:
            lines = exif_lines(image)
    except (UnidentifiedImageError, OSError) as exc:
        print(f"Could not read image: {path}: {exc}", file=sys.stderr)
        return 1

    if not lines:
        print(f"No EXIF data in {path}", file=sys.stderr)
        return 0

    print("\n".join(lines))
    return 0
