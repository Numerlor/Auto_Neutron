from contextlib import suppress
from pathlib import Path

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog

from auto_neutron.appinfo import settings


class Category:
    def __init__(self, settings_obj: QSettings, name: str):
        self.settings = settings_obj
        self.name = name
        self.auto_sync = True

    def __setattr__(self, key, value):
        if not hasattr(self, key):
            self.__dict__[key] = value
            return
        if key in settings:
            if not isinstance(value, settings[key].type):
                raise TypeError(f"Invalid type '{type(value)}' for setting {key}.")
            self.settings.setValue(f"{self.name}/{key}", value)
            if self.auto_sync:
                self.settings.sync()

        self.__dict__[key] = value

    def __repr__(self):
        base_str = f"<Category {repr(self.name)}; "
        for setting in settings:
            with suppress(AttributeError):
                base_str += f"{setting}: {repr(getattr(self, setting))}, "
        return f"{base_str[:-2]}>"


class Settings(Category):
    def __init__(self, settings_folder: Path):
        self.subcategories = []
        super().__init__(QSettings(str(settings_folder / "config.ini"), QSettings.IniFormat), "")

        for setting, (sett_type, category, _) in settings.items():
            if not category:
                # Add setting to self when there's no category
                setattr(self, setting, self.settings.value(setting, type=sett_type))
            else:
                if not hasattr(self, category):
                    # Create category if it doesn't exist
                    cat = Category(self.settings, category)
                    setattr(self, category, cat)
                    self.subcategories.append(cat)
                setattr(getattr(self, category), setting, self.settings.value(f"{category}/{setting}", type=sett_type))

        if not len(self.settings.allKeys()):
            self.write_default_settings()

    def switch_auto_sync(self):
        """Flip auto_sync for self and all subcategories."""
        self.auto_sync = not self.auto_sync
        for cat in self.subcategories:
            cat.auto_sync = self.auto_sync

    def __repr__(self):
        return '\n'.join([repr(cat) for cat in self.subcategories] + [super().__repr__()])

    def write_default_settings(self):
        self.switch_auto_sync()
        for setting, (_, category, value) in settings.items():
            if not category:
                setattr(self, setting, value)
            else:
                setattr(getattr(self, category), setting, value)
        self.write_ahk_path()
        self.settings.sync()
        self.switch_auto_sync()

    def write_ahk_path(self):
        if not Path(self.paths.ahk).exists():
            ahk_path, _ = QFileDialog.getOpenFileName(
                filter="AutoHotKey (AutoHotKey*.exe)",
                caption="Select AutoHotkey's executable "
                        "if you wish to use it; cancel for copy mode",
                directory="C:/")

            if not ahk_path:
                self.copy_mode = True
                self.paths.ahk = ""
            else:
                self.copy_mode = False
                self.paths.ahk = ahk_path
