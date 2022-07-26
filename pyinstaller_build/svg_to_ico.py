# This file uses the MIT license,
# Copyright (C) 2022  Numerlor

"""Utility script to convert a svg file into an icon library."""
import argparse
import shutil
import subprocess  # noqa: S404
from pathlib import Path

IMAGE_SIZES = (256, 128, 96, 64, 48, 40, 32, 24, 20, 16)


def main() -> None:
    """Accept the input and output paths from the user and run the conversion."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", action="store", required=True)
    parser.add_argument("-o", "--output", action="store", required=True)

    args = parser.parse_args()
    svg_path = args.input
    icon_path = args.output

    for size in IMAGE_SIZES:
        subprocess.run(  # noqa: S603
            [
                shutil.which("inkscape"),
                "-z",
                "-w",
                str(size),
                "-h",
                str(size),
                svg_path,
                "-e",
                f"icon{size}.png",
            ]
        )

    subprocess.run(  # noqa: S603
        [
            shutil.which("convert"),
            *[f"icon{size}.png" for size in IMAGE_SIZES],
            icon_path,
        ]
    )
    for path in Path().glob("icon*.png"):
        path.unlink()


if __name__ == "__main__":
    main()
