import functools
import gettext

import babel

from auto_neutron.utils.file import base_path

_active_locale = None

LOCALE_DIR = base_path() / "locale"


def get_active_locale() -> babel.Locale:
    """Get the current active locale."""
    assert _active_locale is not None, "Locale uninitialized."
    return _active_locale


def set_active_locale(locale: babel.Locale) -> None:
    """Set the current active locale."""
    global _active_locale
    _active_locale = locale


def install_translation(language: str) -> None:
    """Install the translations for `language`."""
    gettext.translation(
        "auto_neutron", localedir=LOCALE_DIR, languages=[language]
    ).install()


@functools.cache
def get_available_languages() -> list[str]:
    """Get the languages translations are available for."""
    return [
        path.name
        for path in LOCALE_DIR.glob("*")
        if path.is_dir() and (path / "LC_MESSAGES" / "auto_neutron.mo").exists()
    ]
