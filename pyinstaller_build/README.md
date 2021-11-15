This folder contains resources for building the app using PyInstaller.

Two environmental variables can be set in a .env file:

- UPX_DIR which defaults to ` `

The `build.py` module launches PyInstaller with `PYTHONOPTIMIZE=2` under the venv from `VENV_DIR`,
with UPX dir set to `UPX_DIR`, if not specified UPX will not be used.

`delete_dlls.py` deletes unused dlls which PyInstaller packs from the PySide6 install to reduce the size,
this module is run at the start of in `build.py`

Specified files in this directory use the MIT license included in LICENSE.md
