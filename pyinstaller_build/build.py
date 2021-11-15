import os
import subprocess  # noqa S404
import sys

import dotenv

dotenv.load_dotenv()
if len(sys.argv) < 2 or sys.argv[1] not in {"--debug", "-d"}:
    spec_file = "Auto_Neutron.spec"
else:
    spec_file = "Auto_Neutron_debug.spec"
subprocess.run(  # noqa S603
    [
        sys.executable,
        "-OO",
        "-m",
        "PyInstaller",
        spec_file,
        f"--upx-dir={os.environ['UPX_DIR']}",
    ]
)
