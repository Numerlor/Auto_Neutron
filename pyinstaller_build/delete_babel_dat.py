# This file uses the MIT license.
# Copyright (C) 2021  Numerlor

"""Delete .dat locale data files from the babel install that aren't needed for this app."""

import sys
from pathlib import Path

EXCLUDE_FILES = {"root.dat", "en.dat", "en_001.dat", "en_150.dat"}


def get_locale_data_dir() -> Path:
    """Get the babel locale-data dir site-packages path of the current interpreter."""
    parent_dir = Path(sys.executable).parent
    if parent_dir.name == "Scripts":
        root_dir = parent_dir.parent
    else:
        root_dir = parent_dir
    return root_dir / "Lib" / "site-packages" / "babel" / "locale-data"


def main() -> None:
    """Delete all the data files except the ones in EXCLUDE_FILES."""
    locale_dir = get_locale_data_dir()
    for file in locale_dir.glob("*"):
        if file.name not in EXCLUDE_FILES:
            file.unlink()


if __name__ == "__main__":
    main()
