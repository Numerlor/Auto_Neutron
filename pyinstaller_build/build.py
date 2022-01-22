# This file uses the MIT license.
# Copyright (C) 2021  Numerlor

import hashlib
import os
import shutil
import subprocess  # noqa S404
import sys
from pathlib import Path

import delete_babel_dat
import dotenv
import PyInstaller.__main__

import delete_dlls

dotenv.load_dotenv()


BASE_PATH = Path("pyinstaller_build")


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


def sign_file(file: Path) -> subprocess.CompletedProcess:
    """
    Sign the file at `file`.

    The SIGN_TOOL_PATH, TIMESTAMPING_URL, and CERT_SUBJECT env vars must be set.
    """
    return subprocess.run(  # noqa S603
        [
            os.environ["SIGN_TOOL_PATH"],
            "sign",
            "/tr",
            os.environ["TIMESTAMPING_URL"],
            "/td",
            "sha256",
            "/fd",
            "sha256",
            "/a",
            "/n",
            os.environ["CERT_SUBJECT"],
            str(file),
        ]
    )


if sys.flags.optimize:
    spec_files = [
        BASE_PATH / "Auto_Neutron.spec",
        BASE_PATH / "Auto_Neutron_dir.spec",
    ]
    debug = False
else:
    spec_files = [
        BASE_PATH / "Auto_Neutron_debug.spec",
    ]
    debug = True
delete_dlls.main()
delete_babel_dat.main()
compiled_process = subprocess.run(  # noqa: S603, S607
    ["poetry", "run", "task", "i18n-compile"]
)
if compiled_process.returncode != 0:
    raise Exception("Failed to compile translation files.")

for spec_file in spec_files:
    PyInstaller.__main__.run(
        [
            str(spec_file),
            f"--upx-dir={os.environ['UPX_DIR']}",
            "-y",
            f"--workpath={BASE_PATH}/build",
            f"--distpath={BASE_PATH}/dist",
        ]
    )

directory_path = Path(f"{BASE_PATH}/dist/Auto_Neutron")
exe_path = directory_path.with_name("Auto_Neutron.exe")

if not debug:
    if os.environ.get("SIGN"):
        if sign_file(directory_path / "Auto_neutron.exe").returncode != 0:
            print("Failed to sign", directory_path / "Auto_neutron.exe")  # noqa T001

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

if os.environ.get("SIGN"):
    if sign_file(exe_path).returncode != 0:
        print("Failed to sign", exe_path)  # noqa T001

Path(exe_path.with_name(exe_path.name + ".signature.txt")).write_text(
    sha256sum(exe_path) + "\n"
)
