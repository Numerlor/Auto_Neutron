# This file uses the MIT license.
# Copyright (C) 2021  Numerlor
import argparse
import hashlib
import os
import re
import shutil
import string
import subprocess
import sys
import tomllib
from pathlib import Path

import dotenv
import PyInstaller.__main__

dotenv.load_dotenv()


BASE_PATH = Path(__file__).parent
FILE_INFO_FLAG_RELEASE = 0x0
FILE_INFO_FLAG_PRERELEASE = 0x3  # VS_FF_PRERELEASE & VS_FF_DEBUG
VERSION_REGEX = re.compile(r"^v\d.\d.\d$")


def sha256sum(file: Path) -> str:
    """Get the SHA256 checksum of `file`."""
    hash_ = hashlib.sha256()
    buffer = memoryview(bytearray(128 * 1024))
    with file.open("rb", buffering=0) as f:
        while True:
            num_read = f.readinto(buffer)
            if num_read == 0:
                break
            hash_.update(buffer[:num_read])
    return hash_.hexdigest()


def create_version_info_file(flags: int) -> None:
    """Substitute flags and version into file_version_info_template.txt and create file_version_info.txt."""
    with (BASE_PATH.parent / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    version_string = pyproject["tool"]["poetry"]["version"]

    if VERSION_REGEX.match(version_string) is None:
        raise RuntimeError("Invalid version string format")

    comma_version_string = version_string[1:].replace(".", ",")

    template = string.Template(
        (BASE_PATH / "file_version_info_template.txt").read_text()
    )
    (BASE_PATH / "file_version_info.txt").write_text(
        template.substitute(
            flags=f"0x{flags:X}",
            version_tuple=f"({comma_version_string},0)",
            version=version_string,
        )
    )


parser = argparse.ArgumentParser(
    description="Run the pyinstaller build process. If running with the optimize mode build for release."
)
parser.add_argument(
    "--clean", action="store_true", help="run pyinstaller with the --clean argument."
)
clean = parser.parse_args().clean

if sys.flags.optimize:
    spec_files = [
        BASE_PATH / "Auto_Neutron.spec",
        BASE_PATH / "Auto_Neutron_dir.spec",
    ]
    debug = False
    create_version_info_file(FILE_INFO_FLAG_RELEASE)
else:
    spec_files = [
        BASE_PATH / "Auto_Neutron_debug.spec",
    ]
    debug = True
    create_version_info_file(FILE_INFO_FLAG_PRERELEASE)

if not os.getenv("GITHUB_ACTIONS"):
    compiled_process = subprocess.run(["poetry", "run", "task", "i18n-compile"])
    if compiled_process.returncode != 0:
        raise Exception("Failed to compile translation files.")

for spec_file in spec_files:
    PyInstaller.__main__.run(
        [
            str(spec_file),
            "-y",
            f"--workpath={BASE_PATH}/build",
            f"--distpath={BASE_PATH}/dist",
        ]
        + (["--clean"] if clean else [])
    )

directory_path = Path(f"{BASE_PATH}/dist/Auto_Neutron")
exe_path = directory_path.with_name("Auto_Neutron.exe")

if not debug:
    archive_path = Path(
        shutil.make_archive(
            str(directory_path),
            "zip",
            directory_path,
        )
    )

    Path(archive_path.with_name(archive_path.name + ".signature.txt")).write_text(
        sha256sum(archive_path) + "\n"
    )

    Path(exe_path.with_name(exe_path.name + ".signature.txt")).write_text(
        sha256sum(exe_path) + "\n"
    )
