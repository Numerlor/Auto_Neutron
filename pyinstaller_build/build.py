import os
import shutil
import subprocess  # noqa S404
import sys
from pathlib import Path

import dotenv
import PyInstaller.__main__

import delete_dlls

dotenv.load_dotenv()

if sys.flags.optimize:
    spec_files = ["Auto_Neutron.spec", "Auto_Neutron_dir.spec"]
    debug = False
else:
    spec_files = ["Auto_Neutron_debug.spec"]
    debug = True
delete_dlls.main()

for spec_file in spec_files:
    PyInstaller.__main__.run(
        [
            spec_file,
            f"--upx-dir={os.environ['UPX_DIR']}",
            "-y",
        ]
    )

if not debug:
    if Path("dist/Auto_Neutron").exists():
        shutil.make_archive("dist/Auto_Neutron", "zip", "dist/Auto_Neutron")
