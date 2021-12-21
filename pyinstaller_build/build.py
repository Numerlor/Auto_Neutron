import os
import subprocess  # noqa S404
import sys

import dotenv

import delete_dlls

dotenv.load_dotenv()

if len(sys.argv) < 2 or sys.argv[1] not in {"--debug", "-d"}:
    spec_file = "Auto_Neutron.spec"
    debug = False
else:
    spec_file = "Auto_Neutron_debug.spec"
    debug = True
delete_dlls.main()

run_args = [
    sys.executable,
    "-m",
    "PyInstaller",
    spec_file,
    f"--upx-dir={os.environ['UPX_DIR']}",
]

if not debug:
    run_args.insert(1, "-OO")

subprocess.run(run_args)  # noqa S603
