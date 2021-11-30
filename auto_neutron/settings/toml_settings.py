# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

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


class TOMLSettings:
    """Provide an interface to a TOML settings file."""

    def __init__(self, file_path: Path):
        self.path = file_path

        self._settings_dict: t.Optional[
            RecursiveDefaultDict[str, t.Any]
        ] = RecursiveDefaultDict()
        with suppress(FileNotFoundError):
            with self.path.open("rb") as settings_file:
                self._settings_dict.update_from_dict_recursive(
                    tomli.load(settings_file)
                )

    # region value
    @t.overload
    def value(  # noqa D102
        self,
        categories: collections.abc.Iterable[str],
        key: str,
        *,
        default: t.Any = _DEFAULT_SENTINEL,
        sync_on_missing: bool = False,
    ) -> TOMLType:
        """Get the value of `key` in the category specified by `categories`."""

    @t.overload
    def value(  # noqa D102
        self,
        key: str,
        *,
        default: t.Any = _DEFAULT_SENTINEL,
        sync_on_missing: bool = False,
    ) -> TOMLType:
        ...

    def value(  # type: ignore
        self,
        categories_or_key: t.Union[
            collections.abc.Iterable[str], str
        ] = _MISSING_SENTINEL,
        /,
        key: str = _MISSING_SENTINEL,
        *,
        default: t.Any = _MISSING_SENTINEL,
        sync_on_missing: bool = False,
        categories: collections.abc.Iterable[str] = _MISSING_SENTINEL,
    ) -> TOMLType:
        """
        Get the value of `key`.

        If categories are specified as the first argument, the key will be fetched directly
        after getting to the category specified by the first argument.

        If only the key is specified, it may contain a dotted path containing categories.

        When `sync_on_missing` is True, the settings will be synced on the first lookup fail and an another attempt
        will be done.
        """
        categories, key = self._get_value_arguments(categories_or_key, categories, key)

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

    @staticmethod
    def _get_value_arguments(
        categories_or_key: t.Union[collections.abc.Iterable[str], str],
        categories: collections.abc.Iterable[str],
        key: str,
    ) -> tuple[collections.abc.Iterable[str], str]:
        """
        Construct `categories` and `key` from arguments passed to the `value` method.

        If the passed arguments are missing or have conflicts, raise an error.
        """
        if key is _MISSING_SENTINEL and categories_or_key is _MISSING_SENTINEL:
            raise TypeError("value() missing 1 required positional argument: 'key'")
        if (
            categories is not _MISSING_SENTINEL
            and categories_or_key is not _MISSING_SENTINEL
        ):
            raise TypeError("value() got multiple values for argument 'categories'")

        if key is not _MISSING_SENTINEL and (
            categories_or_key is not _MISSING_SENTINEL
            or categories is not _MISSING_SENTINEL
        ):
            if categories is _MISSING_SENTINEL:
                categories = categories_or_key

        else:
            if categories_or_key is not _MISSING_SENTINEL:
                split_categories_and_key = t.cast(str, categories_or_key).split(".")
            else:
                split_categories_and_key = key.split(".")
            categories = split_categories_and_key[:-1]
            key = split_categories_and_key[-1]

        return categories, key

    __getitem__ = value

    # endregion

    # region set_value
    @t.overload
    def set_value(  # noqa D102
        self, categories: collections.abc.Iterable[str], key: str, value: TOMLType
    ) -> None:
        ...

    @t.overload
    def set_value(self, key: str, value: TOMLType) -> None:  # noqa D102
        ...

    def set_value(  # type: ignore
        self,
        categories_or_key: t.Union[
            collections.abc.Iterable[str], str
        ] = _MISSING_SENTINEL,
        key_or_value: t.Union[str, TOMLType] = _MISSING_SENTINEL,
        value: TOMLType = _MISSING_SENTINEL,
        *,
        key: str = _MISSING_SENTINEL,
        categories: collections.abc.Iterable[str] = _MISSING_SENTINEL,
    ) -> None:
        """
        Set the value of `key` to `value`.

        If categories are specified as the first argument, the key to set the value to will be used directly
        after getting to the category specified by the first argument.

        If only the key and value is specified, the key may contain a dotted path containing categories.
        """
        categories, key, value = self._set_value_arguments(
            categories_or_key, key_or_value, value, key, categories
        )
        category_dict = self._get_category_dict(self._settings_dict, categories)
        category_dict[key] = value

    @staticmethod
    def _set_value_arguments(
        categories_or_key: t.Union[
            collections.abc.Iterable[str], str
        ] = _MISSING_SENTINEL,
        key_or_value: t.Union[str, TOMLType] = _MISSING_SENTINEL,
        value: TOMLType = _MISSING_SENTINEL,
        key: str = _MISSING_SENTINEL,
        categories: collections.abc.Iterable[str] = _MISSING_SENTINEL,
    ) -> tuple[collections.abc.Iterable[str], str, TOMLType]:
        """
        Construct `categories`, `key`, and `value` from arguments passed to the `set_value` method.

        If the passed arguments are missing or have conflicts, raise an error.
        """
        if key is _MISSING_SENTINEL and categories_or_key is _MISSING_SENTINEL:
            raise TypeError("set_value() missing 1 required positional argument: 'key'")
        if value is _MISSING_SENTINEL and key_or_value is _MISSING_SENTINEL:
            raise TypeError(
                "set_value() missing 1 required positional argument: 'value'"
            )
        if (
            categories is not _MISSING_SENTINEL
            and categories_or_key is not _MISSING_SENTINEL
        ):
            raise TypeError("set_value() got multiple values for argument 'categories'")
        if key is not _MISSING_SENTINEL and key_or_value is not _MISSING_SENTINEL:
            raise TypeError("set_value() got multiple values for argument 'key'")

        if key is _MISSING_SENTINEL:
            if value is _MISSING_SENTINEL:
                key = t.cast(str, categories_or_key)
            else:
                key = t.cast(str, key_or_value)

        if (
            value is not _MISSING_SENTINEL
            and (
                categories_or_key is not _MISSING_SENTINEL
                or categories is not _MISSING_SENTINEL
            )
            and (key_or_value is not _MISSING_SENTINEL or key is not _MISSING_SENTINEL)
        ):
            if categories_or_key is not _MISSING_SENTINEL:
                categories = categories_or_key
        else:
            if categories_or_key is not _MISSING_SENTINEL:
                split_categories_and_key = t.cast(str, categories_or_key).split(".")
            else:
                split_categories_and_key = key.split(".")
            categories = split_categories_and_key[:-1]
            key = split_categories_and_key[-1]
            if value is _MISSING_SENTINEL:
                value = key_or_value
        return categories, key, value

    __setitem__ = set_value

    # endregion

    @staticmethod
    def _get_category_dict(
        dict_: dict, categories: collections.Iterable[str]
    ) -> RecursiveDefaultDict:
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
        file_settings = RecursiveDefaultDict()
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
