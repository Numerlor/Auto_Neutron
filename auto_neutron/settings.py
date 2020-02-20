# This file is part of Auto_Neutron.
# Copyright (C) 2019-2020  Numerlor

from contextlib import suppress
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog

from auto_neutron.constants import SETTINGS


class Category:
    """
    Contains one ini QSettings category.

    If `auto_sync` is `True` settings will be written on every set setting.
    Types are checked against settings in `appinfo`, TypeError is raised on a mismatch.
    """

    def __init__(self, settings_obj: QSettings, name: str):
        self.settings = settings_obj
        self.name = name
        self._auto_sync = True

    def __setattr__(self, key: str, value: Any) -> None:
        if not hasattr(self, key):
            self.__dict__[key] = value
            return
        if key in SETTINGS:
            if not isinstance(value, SETTINGS[key].type):
                raise TypeError(f"Invalid type '{type(value)}' for setting {key}.")
            self.settings.setValue(f"{self.name}/{key}", value)
            if self._auto_sync:
                self.settings.sync()

        self.__dict__[key] = value

    def __repr__(self) -> str:
        base_str = f"<Category {repr(self.name)}; "
        for setting in SETTINGS:
            with suppress(AttributeError):
                base_str += f"{setting}: {repr(getattr(self, setting))}, "
        return f"{base_str[:-2]}>"


class Settings(Category):
    """
    Holds top level settings and categories of QSettings ini file.

    config.ini file in `settings_folder` is read and attributes are created from its contents.
    """

    def __init__(self, settings_folder: Path):
        self.subcategories = []
        super().__init__(QSettings(str(settings_folder / "config.ini"), QSettings.IniFormat), "")

        for setting, (sett_type, category, _) in SETTINGS.items():
            if category is None:
                # Add setting to self when there's no category
                setattr(self, setting, self.settings.value(setting, type=sett_type))
            else:
                if not hasattr(self, category):
                    # Create category if it doesn't exist
                    cat = Category(self.settings, category)
                    setattr(self, category, cat)
                    self.subcategories.append(cat)
                # Set new setting on `category`
                setattr(
                    getattr(self, category),
                    setting,
                    self.settings.value(f"{category}/{setting}", type=sett_type)
                )

        if not len(self.settings.allKeys()):
            self.write_default_settings()

    @property
    def auto_sync(self) -> bool:
        """
        Get or set `self._auto_sync`.

        Setting switches all subcategories' `_auto_sync` to `value`.
        """
        return self._auto_sync

    @auto_sync.setter
    def auto_sync(self, value: Any) -> None:
        self._auto_sync = value
        for category in self.subcategories:
            category.auto_sync = value

    def __repr__(self) -> str:
        return '\n'.join([repr(cat) for cat in self.subcategories] + [super().__repr__()])

    def write_default_settings(self) -> None:
        """Write default settings from `app_info` to config.ini and prompt for `ahk_path`."""
        self.auto_sync = False
        for setting, (_, category, value) in SETTINGS.items():
            if not category:
                setattr(self, setting, value)
            else:
                setattr(getattr(self, category), setting, value)
        if not Path(self.paths.ahk).exists():
            path = self.set_ahk_path()
            if path:
                self.copy_mode = True
            else:
                self.copy_mode = False
        self.settings.sync()
        self.auto_sync = True

    def set_ahk_path(self) -> bool:
        """Prompt for ahk path and set it if valid. If dialog is closed, set to an empty string."""
        ahk_path, _ = QFileDialog.getOpenFileName(
            filter="AutoHotkey (AutoHotkey*.exe)",
            caption="Select AutoHotkey's executable.",
            directory="C:/")

        if ahk_path and Path(ahk_path).stem.lower().startswith("autohotkey"):
            self.paths.ahk = ahk_path
            return True
        else:
            self.paths.ahk = ""
            return False
