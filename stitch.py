#!/usr/bin/env python3
"""Stitch videos into one longer video, in the order given."""

import argparse
import sys
from pathlib import Path

from moviepy import VideoFileClip, concatenate_videoclips


def stitch(videos, output):
    """Write the videos end to end. Return an exit code."""
    paths = [Path(video) for video in videos]
    if len(paths) < 2:
        print("Pass at least two videos.", file=sys.stderr)
        return 1

    for path in paths:
        if not path.is_file():
            print(f"Video not found: {path}", file=sys.stderr)
            return 1

    output = Path(output)
    clips = []
    final = None
    try:
        for path in paths:
            try:
                clip = VideoFileClip(str(path))
            except (OSError, ValueError) as exc:
                print(f"Could not read video: {path}: {exc}", file=sys.stderr)
                return 1
            if not clip.duration or clip.w < 2 or clip.h < 2:
                clip.close()
                print(f"Could not read video: {path}", file=sys.stderr)
                return 1
            clips.append(clip)

        same_size = len({tuple(clip.size) for clip in clips}) == 1
        method = "chain" if same_size else "compose"
        final = concatenate_videoclips(
            clips,
            method=method,
            bg_color=(0, 0, 0) if method == "compose" else None,
        )
        fps = final.fps or max(clip.fps or 0 for clip in clips) or 24
        write_kwargs = {
            "codec": "libx264",
            "fps": fps,
            "preset": "veryfast",
            "logger": None,
            "pixel_format": "yuv420p",
        }
        if any(clip.audio is not None for clip in clips):
            write_kwargs["audio_codec"] = "aac"
        else:
            write_kwargs["audio"] = False

        print(f"Writing {len(clips)} clips ({method}) to {output}")
        try:
            final.write_videofile(str(output), **write_kwargs)
        except (OSError, ValueError) as exc:
            print(f"Could not write video: {output}: {exc}", file=sys.stderr)
            return 1
    finally:
        if final is not None:
            final.close()
        for clip in clips:
            clip.close()

    print(output)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Stitch videos into one longer video, in the order given."
    )
    parser.add_argument("videos", nargs="+", help="Input videos, played in this order")
    parser.add_argument("--output", required=True, help="Path of the combined video")
    args = parser.parse_args(argv)
    return stitch(args.videos, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
