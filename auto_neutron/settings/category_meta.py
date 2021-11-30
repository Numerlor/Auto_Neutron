# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t
import weakref
from contextlib import contextmanager

import auto_neutron.settings as settings

if t.TYPE_CHECKING:
    import collections.abc

    from .toml_settings import TOMLSettings

_created_categories: weakref.WeakSet[SettingsCategory] = weakref.WeakSet()


class SettingsParams(t.NamedTuple):
    """
    Metadata for a setting in `SettingsCategory`.

    `settings_type` contains the tpye under which QSetting saved the object
    `default` is the default value of the setting
    `on_save` is a callable that's applied before an user given value is saved
    `on_load` is a callable that's applied before a value from settings is returned to the user
    """

    setting_type: type
    default: t.Any
    on_save: t.Optional[collections.abc.Callable[[t.Any], t.Any]] = None
    on_load: t.Optional[collections.abc.Callable[[t.Any], t.Any]] = None


class SettingsCategory(type):
    """
    Create a class representing a category from a QSettings ini file.

    An example class would look like this:

    >>> class Category(metaclass=SettingsCategory):
    ...     setting1: type = SettingsParams(..., ...)
    ...     setting2: type = SettingsParams(..., ..., ..., ...)
    ...

    A QSettings object must be set through `set_settings` before any access is attempted.

    Each annotated name in the class represents a value in the underlying QSettings category,
    metadata in its `SettingsParams` value that's used when it's accessed or set on the class.

    On access, if the requested name is a setting, its value is fetched from the category given by the class name,
    using the `on_load` callable (if present) to modify the value before it's returned to the user.

    On attribtue setting the same behaviour applies but in reverse.
    The user given value is passed through `on_save` before being passed to the QSettings object.
    Attribute setting without using the `delay_sync` context manager automatically syncs the settings to the ini file.

    A `settings_getter` kwarg can be specified when creating a new class to a function which returns the settings
    object to be used by the class.

    When `auto_sync_` is True, the settings are synced with the settings object on every value change.
    The initial value for `auto_sync_` can be set through the class' `auto_sync` kwargs.
    """

    auto_sync: bool
    _settings_getter: collections.abc.Callable[[], TOMLSettings]

    def __new__(
        metacls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, t.Any],
        *,
        auto_sync: bool = True,
        settings_getter: collections.abc.Callable[
            [], TOMLSettings
        ] = settings.get_settings,
        **kwargs,
    ):
        """Create the category object and set its settings getter and auto sync from the kwargs."""
        obj = super().__new__(metacls, name, bases, namespace, **kwargs)
        obj._settings_getter = settings_getter
        obj.auto_sync_ = auto_sync
        _created_categories.add(obj)
        return obj

    def __getattribute__(cls, key: str):
        """
        If the attribute is an annotated setting, fetch its value from the class' settings instead of the class itself.

        If the SettingsParams object of the setting defines an `on_load` callable, the callable is applied to `value`
        before it's returned to the caller.
        """
        getattr_ = super().__getattribute__
        value: SettingsParams = getattr_(key)
        if key in getattr_("__annotations__"):
            settings_val = cls._settings_getter().value(
                (cls.__name__,), key, default=value.default
            )
            if value.on_load is not None:
                return value.on_load(settings_val)
            return settings_val
        return value

    def __setattr__(cls, key: str, value: t.Any):
        """
        Set the attribute of the object, if the attribute is an annotated setting set it on `_settings`.

        When setting an attribute of an annotated setting, the actual value of the attribute is left unchanged,
        if `cls.auto_sync_` is true, the settings are synced to the file after they're set.

        If the SettingsParams object of the setting defines an `on_save` callable, the callable is applied to `value`
        before it's saved to the class' settings.
        """
        if key in cls.__annotations__:
            if super().__getattribute__(key).on_save is not None:
                value = super().__getattribute__(key).on_save(value)
            cls._settings_getter().set_value((cls.__name__,), key, value)
            if cls.auto_sync_:
                cls._settings_getter().sync()
        else:
            super().__setattr__(key, value)


@contextmanager
def delay_sync(
    *,
    categories: t.Optional[collections.abc.Iterable[SettingsCategory]] = None,
    exclude_categories: collections.abc.Iterable[SettingsCategory] = (),
    module_filter_include: t.Optional[collections.abc.Container[str]] = None,
    module_filter_exclude: t.Optional[collections.abc.Container[str]] = None,
) -> collections.abc.Iterator[None]:
    """
    Delay sync of settings from specified categories until the end of the context manager.

    The `categories` and `module_filter_include` filters specify which categories to include, categories from the
    categories kwarg are used directly, and all categories from modules within the `module_filter_include`
    container are included to the delayed syncing.

    The categories specified by the above explained kwargs (or all the categories if the kwargs are unset) are then
    further filtered to remove categories from the `exclude_categories` iterable and categories from modules
    in the `module_filter_exclude` container.
    """
    if categories is None:
        if module_filter_include is None:
            categories = set(_created_categories)
        else:
            categories = set()
    else:
        categories = set(categories)

    if module_filter_include is not None:
        for category in _created_categories:
            if category.__module__ in module_filter_include:
                categories.add(category)

    if module_filter_exclude is not None:
        for category in categories.copy():
            if category.__module__ in module_filter_exclude:
                categories.remove(category)

    categories.difference_update(exclude_categories)
    categories.difference_update(
        category for category in categories if not category.auto_sync_
    )

    for category in categories:
        category.auto_sync_ = False

    yield

    settings_objs: set[TOMLSettings] = set()
    for category in categories:
        category.auto_sync_ = True
        settings_objs.add(category._settings_getter())

    for settings_obj in settings_objs:
        settings_obj.sync()
