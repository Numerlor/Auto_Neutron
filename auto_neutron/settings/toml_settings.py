# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import inspect
import logging
import shutil
import typing as t
from contextlib import suppress

import tomli
import tomli_w

from auto_neutron.utils.recursive_default_dict import RecursiveDefaultDict

if t.TYPE_CHECKING:
    import collections.abc
    import datetime
    import decimal
    from pathlib import Path

    TOMLType = t.Union[
        bool,
        int,
        float,
        datetime.date,
        datetime.time,
        datetime.datetime,
        decimal.Decimal,
        str,
        list,
        tuple,
        dict,
    ]

_DEFAULT_SENTINEL = t.cast(t.Any, object())
_MISSING_SENTINEL = t.cast(t.Any, object())
_overload_dummy = t.overload
if not t.TYPE_CHECKING:
    t.overload = lambda x: x

log = logging.getLogger(__name__)


class TOMLSettings:
    """Provide an interface to a TOML settings file."""

    _settings_dict: RecursiveDefaultDict[str, t.Any]

    def __init__(self, file_path: Path):
        self.path = file_path
        self._settings_dict = RecursiveDefaultDict()
        with suppress(FileNotFoundError):
            self.load_from_file()

    # region value
    @t.overload
    def value(  # noqa D102
        self,
        categories: collections.abc.Iterable[str],
        key: str,
        *,
        default: t.Any = _MISSING_SENTINEL,
        sync_on_missing: bool = False,
    ) -> TOMLType:
        ...

    _value_sig_key_and_categories = inspect.Signature.from_callable(value)

    @t.overload
    def value(  # noqa D102
        self,
        key: str,
        *,
        default: t.Any = _MISSING_SENTINEL,
        sync_on_missing: bool = False,
    ) -> TOMLType:
        ...

    _value_sig_key_only = inspect.Signature.from_callable(value)

    def value(self, *args, **kwargs) -> TOMLType:
        """
        Get the value of `key`.

        If categories are specified as the first argument, the key will be fetched directly
        after getting to the category specified by the first argument.

        If only the key is specified, it may contain a dotted path containing categories.

        When `sync_on_missing` is True, the settings will be synced on the first lookup fail and an another attempt
        will be done.
        """
        categories, key, default, sync_on_missing = self._get_value_arguments(
            self, *args, **kwargs
        )

        with self._settings_dict.disable_defaults_for_missing():
            try:
                category_dict = self._get_category_dict(self._settings_dict, categories)
            except KeyError:
                value = _DEFAULT_SENTINEL
            else:
                value = category_dict.get(key, _DEFAULT_SENTINEL)

            if value is _DEFAULT_SENTINEL and sync_on_missing:
                self.sync()
                try:
                    category_dict = self._get_category_dict(
                        self._settings_dict, categories
                    )
                except KeyError:
                    value = _DEFAULT_SENTINEL
                else:
                    value = category_dict.get(key, _DEFAULT_SENTINEL)

            if value is _DEFAULT_SENTINEL:
                if default is _MISSING_SENTINEL:
                    raise KeyError(key)
                else:
                    value = default

        return value

    @classmethod
    def _get_value_arguments(
        cls,
        *args,
        **kwargs,
    ) -> tuple[collections.abc.Iterable[str], str, t.Any, bool]:
        """
        Construct `categories` and `key` from arguments passed to the `value` method.

        If the passed arguments are missing or have conflicts, raise an error.
        """
        try:
            bound_arguments = cls._value_sig_key_only.bind(*args, **kwargs)
            bound_arguments.apply_defaults()
            split_key = bound_arguments.arguments["key"].split(".")
            categories = split_key[:-1]
            key = split_key[-1]
        except TypeError:
            bound_arguments = cls._value_sig_key_and_categories.bind(*args, **kwargs)
            bound_arguments.apply_defaults()
            key = bound_arguments.arguments["key"]
            categories = bound_arguments.arguments["categories"]

        default = bound_arguments.arguments["default"]
        sync_on_missing = bound_arguments.arguments["sync_on_missing"]

        return categories, key, default, sync_on_missing

    __getitem__ = value

    # endregion

    # region set_value
    @t.overload
    def set_value(  # noqa D102
        self, categories: collections.abc.Iterable[str], key: str, value: TOMLType
    ) -> None:
        ...

    _set_value_sig_key_and_categories = inspect.Signature.from_callable(set_value)

    @t.overload
    def set_value(self, key: str, value: TOMLType) -> None:  # noqa D102
        ...

    _set_value_sig_key_only = inspect.Signature.from_callable(set_value)

    def set_value(self, *args, **kwargs) -> None:
        """
        Set the value of `key` to `value`.

        If categories are specified as the first argument, the key to set the value to will be used directly
        after getting to the category specified by the first argument.

        If only the key and value is specified, the key may contain a dotted path containing categories.
        """
        categories, key, value = self._set_value_arguments(self, *args, **kwargs)
        category_dict = self._get_category_dict(self._settings_dict, categories)
        category_dict[key] = value

    @classmethod
    def _set_value_arguments(
        cls,
        *args,
        **kwargs,
    ) -> tuple[collections.abc.Iterable[str], str, TOMLType]:
        """
        Construct `categories`, `key`, and `value` from arguments passed to the `set_value` method.

        If the passed arguments are missing or have conflicts, raise an error.
        """
        try:
            bound_arguments = cls._set_value_sig_key_only.bind(*args, **kwargs)
            bound_arguments.apply_defaults()
            split_key = bound_arguments.arguments["key"].split(".")
            categories = split_key[:-1]
            key = split_key[-1]
        except TypeError:
            bound_arguments = cls._set_value_sig_key_and_categories.bind(
                *args, **kwargs
            )
            bound_arguments.apply_defaults()
            key = bound_arguments.arguments["key"]
            categories = bound_arguments.arguments["categories"]
        value = bound_arguments.arguments["value"]
        return categories, key, value

    __setitem__ = set_value

    # endregion

    @staticmethod
    def _get_category_dict(
        dict_: dict, categories: collections.abc.Iterable[str]
    ) -> dict:
        """Get the category specified by `categories`."""
        for category in categories:
            dict_ = dict_[category]
        return dict_

    def sync(self, *, overwrite_external: bool = True, atomic: bool = True) -> None:
        """
        Sync the object with the settings file.

        If `overwrite_external` is True and the same key has different values in the file and in the settings object,
        the values from the settings object will overwrite the values from the file.
        Otherwise the argument is set to False, a ValueError is raised in case of a conflict.

        If `atomic` is True, the contents are written to a temporary file and then moved to the target path;
        otherwise if it is set to False, the contents are written directly to the file.
        """
        log.info(f"Syncing settings to {self.path}.")
        file_settings: RecursiveDefaultDict[str, t.Any] = RecursiveDefaultDict()
        with suppress(FileNotFoundError):
            with self.path.open("rb") as settings_file:
                file_settings.update_from_dict_recursive(tomli.load(settings_file))
        file_settings.update_from_dict_recursive(
            self._settings_dict, ignore_conflicts=overwrite_external
        )
        self._settings_dict = file_settings

        if atomic:
            temp_path = self.path.with_stem("_TEMP" + self.path.stem)
            with temp_path.open("wb") as settings_file:
                tomli_w.dump(self._settings_dict, settings_file, multiline_strings=True)

            shutil.move(temp_path, self.path)
        else:
            with self.path.open("wb") as settings_file:
                tomli_w.dump(self._settings_dict, settings_file, multiline_strings=True)

    def load_from_file(self) -> None:
        """Load new settings from the file path of the settings object."""
        log.info(f"Loading new settings from {self.path}.")
        file_settings: RecursiveDefaultDict[str, t.Any] = RecursiveDefaultDict()
        with self.path.open("rb") as settings_file:
            file_settings.update_from_dict_recursive(tomli.load(settings_file))
        self._settings_dict = file_settings


t.overload = _overload_dummy
