This folder contains resources for building the app using PyInstaller.

The `build.py` module launches PyInstaller with `PYTHONOPTIMIZE=2` with UPX dir set to the value in the `UPX_DIR` env var; if not specified UPX will not be used.

`delete_dlls.py` deletes unused dlls which PyInstaller packs from the PySide6 install to reduce the size,
this module is automatically ran at the start of `build.py`

Specified files in this directory use the MIT license included in this directory's LICENSE.md
