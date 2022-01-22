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

if not debug:
    archive_path = shutil.make_archive(
        f"{BASE_PATH}/dist/Auto_Neutron",
        "zip",
        f"{BASE_PATH}/dist/Auto_Neutron",
    )
    Path(archive_path + ".signature.txt").write_text(
        sha256sum(Path(archive_path)) + "\n"
    )

Path(f"{BASE_PATH}/dist/Auto_Neutron.exe.signature.txt").write_text(
    sha256sum(Path(f"{BASE_PATH}/dist/Auto_Neutron.exe")) + "\n"
)
