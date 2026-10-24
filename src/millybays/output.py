"""Write one run directory. An existing directory at that path is replaced."""

import json
import shutil
from pathlib import Path

from millybays.errors import InputError
from millybays.models import (
    PipelineResult,
    RunContext,
    ad_payload,
    format_timestamp,
    item_payload,
    price_payload,
    transcript_payload,
)

ARTIFACTS = {
    "item": "item.json",
    "price": "price.json",
    "transcript": "transcript.json",
    "transcript_text": "transcript.txt",
    "ad": "ad.json",
}


def write_run(
    directory: Path,
    ctx: RunContext,
    result: PipelineResult,
    *,
    backend: str,
) -> Path:
    directory = directory.resolve()
    _assert_replaceable(directory, ctx.image.path)
    if directory.exists() and not directory.is_dir():
        raise InputError(f"Output path is a file: {directory}")
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    _write_artifacts(directory, ctx, result, backend=backend)
    return directory


def _assert_replaceable(directory: Path, image_path: Path) -> None:
    # Replacing the run directory deletes it. These paths are never run folders.
    forbidden = {
        Path.cwd().resolve(),
        Path.home().resolve(),
        Path(directory.anchor).resolve(),
    }
    image_path = image_path.resolve()
    if directory in forbidden or image_path == directory or image_path.is_relative_to(directory):
        raise InputError(f"Refusing to replace output directory: {directory}")


def _write_artifacts(
    directory: Path,
    ctx: RunContext,
    result: PipelineResult,
    *,
    backend: str,
) -> None:
    _dump(directory / ARTIFACTS["item"], item_payload(result.item))
    _dump(directory / ARTIFACTS["price"], price_payload(result.quote))
    _dump(directory / ARTIFACTS["transcript"], transcript_payload(result.transcript))
    transcript_path = directory / ARTIFACTS["transcript_text"]
    transcript_path.write_text(result.transcript.text + "\n", encoding="utf-8")
    _dump(directory / ARTIFACTS["ad"], ad_payload(result.ad))
    _dump(
        directory / "run.json",
        {
            "backend": backend,
            "source_path": str(ctx.image.path),
            "image_sha256": ctx.image.sha256,
            "captured_at": format_timestamp(ctx.captured_at),
            "location": ctx.location,
            "currency": ctx.currency,
            "artifacts": ARTIFACTS,
        },
    )


def _dump(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
