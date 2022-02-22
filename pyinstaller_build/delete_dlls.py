# This file uses the MIT license.
# Copyright (C) 2020  Numerlor

"""
Deletes dlls from the PySide6 install that aren't needed for this app.

Deletes specified DLLs and directories from the current python
without which the app runs fine, reducing its packaged size.
"""

import shutil
import sys
from pathlib import Path

ROOT_DELETE = (
    "opengl32sw.dll",
    "Qt6OpenGL.dll",
    "Qt6Quick.dll",
    "Qt6QmlModels.dll",
    "Qt6Svg.dll",
    "Qt6VirtualKeyboard.dll",
)
PLUGINS_DELETE = (
    "iconengines/qsvgicon.dll",
    "imageformats/qgif.dll",
    "imageformats/qicns.dll",
    "imageformats/qjpeg.dll",
    "imageformats/qtga.dll",
    "imageformats/qtiff.dll",
    "imageformats/qwbmp.dll",
    "imageformats/qwebp.dll",
    "platforminputcontexts/qtvirtualkeyboardplugin.dll",
    "platforms/qdirect2d.dll",
    "platforms/qminimal.dll",
    "platforms/qoffscreen.dll",
    "styles/qwindowsvistastyle.dll",
)


def get_pyside_dir() -> Path:
    """Get the pyside site-packages path of the current interpreter."""
    parent_dir = Path(sys.executable).parent
    if parent_dir.name == "Scripts":
        root_dir = parent_dir.parent
    else:
        root_dir = parent_dir
    return root_dir / "Lib" / "site-packages" / "PySide6"


def main() -> None:
    """Delete all the files listed in ROOT_DELETE and PLUGINS_DELETE and the translations directory."""
    pyside_dir = get_pyside_dir()
    for file in ROOT_DELETE:
        (pyside_dir / file).unlink(missing_ok=True)
    for file in PLUGINS_DELETE:
        (pyside_dir / "plugins" / file).unlink(missing_ok=True)
    shutil.rmtree(pyside_dir / "translations", ignore_errors=True)


if __name__ == "__main__":
    main()
