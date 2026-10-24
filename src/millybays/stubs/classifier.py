"""Filename stand-in for a vision classifier."""

import re
from pathlib import Path

from millybays.models import Item, RunContext

_SEPARATORS = re.compile(r"[-_]+")
_SPACES = re.compile(r"\s+")


def name_from_filename(path: Path) -> str:
    cleaned = _SPACES.sub(" ", _SEPARATORS.sub(" ", path.stem)).strip()
    return cleaned or "Untitled item"


class StubClassifier:
    """Return a name taken from the filename and a description that marks itself as a stub.

    A real classifier reads the image bytes and returns the primary object's name,
    description, and a confidence score.
    """

    def classify(self, ctx: RunContext) -> Item:
        byte_length = len(ctx.image.data)
        return Item(
            name=name_from_filename(ctx.image.path),
            description=(
                "Classification is stubbed for this "
                f"{ctx.image.media_type} file of {byte_length} bytes."
            ),
            confidence=None,
        )
