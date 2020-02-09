"""
Deletes dlls from PyQt5 install that aren't needed for this app.

Deletes specified DLLs and directories from the VENV_DIR or .venv if unspecified
without which the app runs fine, reducing its packaged size.
"""

import os

IMAGE_FORMATS = (
    "qgif.dll",
    "qicns.dll",
    "qjpeg.dll",
    "qsvg.dll",
    "qtga.dll",
    "qtiff.dll",
    "qwbmp.dll",
    "qwebp.dll",
)

PLATFORMS = (
    "qminimal.dll",
    "qoffscreen.dll",
    "qwebgl.dll",
)

BIN = (
    "d3dcompiler_47.dll",
    "libcrypto-1_1-x64.dll",
    "libeay32.dll",
    "libEGL.dll",
    "libGLESv2.dll",
    "libss2-1_1-x64.dll",
    "opengl32sw.dll",
    "Qt5DBus.dll",
    "Qt5Svg.dll",
)

os.chdir(f"..\\{os.environ.get('VENV_DIR', '.venv')}\\Lib\\site-packages\\PyQt5\\Qt")
try:
    for file in os.listdir("translations"):
        try:
            os.remove("translations\\" + file)
        except FileNotFoundError:
            pass
    os.rmdir("translations")
except FileNotFoundError:
    pass

for file in IMAGE_FORMATS:
    try:
        os.remove("plugins\\imageformats\\" + file)
    except FileNotFoundError:
        pass

for file in PLATFORMS:
    try:
        os.remove("plugins\\platforms\\" + file)
    except FileNotFoundError:
        pass

try:
    for file in os.listdir("plugins\\styles"):
        try:
            os.remove("plugins\\styles\\" + file)
        except FileNotFoundError:
            pass
    os.rmdir("plugins\\styles")
except FileNotFoundError:
    pass

for file in BIN:
    try:
        os.remove("bin\\" + file)
    except FileNotFoundError:
        pass
