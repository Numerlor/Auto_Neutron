This folder contains resources for building the app using PyInstaller.

Two environmental variables can be set in a .env file:
    
- VENV_DIR which defaults to `.venv`
- UPX_DIR which defaults to ` `

The `build.bat` file launches PyInstaller with `PYTHONOPTIMIZE=2` under the venv from `VENV_DIR`,
with UPX dir set to `UPX_DIR`, if not specified UPX will not be used.

`delete_dlls.py` deletes unused dlls which PyInstaller packs from the PyQt5 install to reduce the size

Specified files in this directory use the MIT license included in LICENSE.md