from datetime import datetime, timezone

import pytest

from millybays.image_io import load_image
from millybays.models import RunContext

PNG_BYTES = b"\x89PNG\r\nstub-image"


@pytest.fixture
def image_path(tmp_path):
    path = tmp_path / "widget.png"
    path.write_bytes(PNG_BYTES)
    return path


@pytest.fixture
def context(image_path):
    return RunContext(
        image=load_image(image_path),
        captured_at=datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc),
        location=None,
        currency="USD",
    )
