#!/usr/bin/env python3
"""Print EXIF tags from an image."""

import argparse

from classifier import print_exif


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print EXIF data from an image.")
    parser.add_argument("--image", required=True, help="Path to an image file")
    args = parser.parse_args(argv)
    return print_exif(args.image)


if __name__ == "__main__":
    raise SystemExit(main())
