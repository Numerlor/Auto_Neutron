"""Constants and filter helper functions to be used in spec files."""
from pathlib import Path

DATAS = [
    ("../resources/*", "./resources"),
    ("../locale", "./locale"),
    ("../LICENSE.md", "."),
]
EXCLUDES = []
HIDDEN_IMPORTS = ["babel.numbers"]

DLL_EXCLUDE = {
    "opengl32sw.dll",
    "qt6opengl.dll",
    "qt6quick.dll",
    "qt6qmlmodels.dll",
    "qt6virtualkeyboard.dll",
    "svgicon.dll",
    "qgif.dll",
    "qicns.dll",
    "qjpeg.dll",
    "qtga.dll",
    "qtiff.dll",
    "qwbmp.dll",
    "qwebp.dll",
    "qtvirtualkeyboardplugin.dll",
    "qdirect2d.dll",
    "qminimal.dll",
    "qoffscreen.dll",
    "qwindowsvistastyle.dll",
    "qcertonlybackend.dll",
    "qopensslbackend.dll",
    "libssl-1_1.dll",
    "libcrypto-1_1.dll",
    "ucrtbase.dll",
}

BABEL_INCLUDE = {"root.dat", "en.dat", "en_001.dat", "en_150.dat"}


def filter_binaries(
    to_filter: list[tuple[str, str, str]]
) -> list[tuple[str, str, str]]:
    """Filter out any binaries that are in DLL_EXCLUDE."""
    filtered = []
    for dest, source, kind in to_filter:
        source_path = Path(source)
        if (
            source_path.name.lower() not in DLL_EXCLUDE
            and not source_path.name.startswith("api-ms")
        ):
            filtered.append((dest, source, kind))

    return filtered


def filter_datas(to_filter: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """
    Filter out pyinstaller data files.

    All PySide6 translation files and pytz files are excluded.
    Babel locale datas not present in BABEL_INCLUDE are excluded.
    """
    filtered = []
    for dest, source, kind in to_filter:
        source_path = Path(source)
        if source_path.is_absolute() and (
            "PySide6" in source_path.parts
            and source_path.parent.name.lower() == "translations"
            or (
                "babel" in source_path.parts
                and source_path.parent.name == "locale-data"
                and source_path.name.lower() not in BABEL_INCLUDE
            )
            or "pytz" in source_path.parts
        ):
            continue

        filtered.append((dest, source, kind))

    return filtered
