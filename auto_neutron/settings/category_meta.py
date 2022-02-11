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

_MISSING = object()


class SettingsParams(t.NamedTuple):
    """
    Metadata for a setting in `SettingsCategory`.

    `default` is the default value of the setting
    `on_save` is a callable that's applied before an user given value is saved
    `on_load` is a callable that's applied before a value from settings is returned to the user
    `fallback_paths` is a container of full paths to settings to be checked in case the initial look-up fails.
    """

    default: t.Any
    on_save: t.Optional[collections.abc.Callable[[t.Any], t.Any]] = None
    on_load: t.Optional[collections.abc.Callable[[t.Any], t.Any]] = None
    fallback_paths: tuple[str] = ()


class SettingsCategory(type):
    """
    Create a class representing a category from a settings object.

    An example class would look like this:

    >>> class Category(metaclass=SettingsCategory):
    ...     setting1: typing.Annotated[type, SettingsParams(..., ...)]
    ...     setting2: typing.Annotated[type, SettingsParams(..., ..., ..., ...)]
    ...

    Which would be represented like so in the settings:
        Category
        ├── setting1 ( = some value)
        └── setting2 ( = some other value)

    All class attributes annotated with typing.Annotated containing a `SettingsParam`s object in the annotation
    are proxies to a setting in the settings object.

    If `on_save` or `on_load` are given in the `SettingsParam` object, the functions are respectively used to
    serialize and deserialize the data coming from the setting object.

    A `settings_getter` kwarg can be specified when creating a new class to a function which returns the settings
    object to be used by the class, otherwise `settings.get_settings` is used by default.

    When `auto_sync_` is True, the settings are synced with the settings object on every value change.
    The initial value for `auto_sync_` can be set through the class' `auto_sync` kwargs.

    The auto sync can be delayed with the `delay_sync` context manager if multiple values are set at once.

    If prefix or suffix categories are specified, the settings category is prefixed/suffixed with them
    when looking up a value (e.g. category B with ('A',) prefix_categories becomes the A.B category).
    """

    auto_sync_: bool
    settings_getter_: collections.abc.Callable[[], TOMLSettings]
    __prefix_categories: collections.abc.Iterable[str]
    __suffix_categories: collections.abc.Iterable[str]

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
        prefix_categories: collections.abc.Iterable[str] = (),
        suffix_categories: collections.abc.Iterable[str] = (),
        **kwargs,
    ):
        """Create the category object and set its attributes."""
        obj = super().__new__(metacls, name, bases, namespace, **kwargs)
        obj.settings_getter_ = settings_getter
        obj.__prefix_categories = prefix_categories
        obj.__suffix_categories = suffix_categories
        obj.auto_sync_ = auto_sync
        _created_categories.add(obj)
        return obj

    def __getattr__(cls, key: str):
        """
        If the attribute is an annotated setting, fetch its value from the class' settings instead of the class itself.

        If the `SettingsParams` object of the setting defines an `on_load` callable, the callable is applied to `value`
        before it's returned to the caller.
        """
        annotation = cls.__annotations__.get(key)
        if annotation is not None:
            params = cls._get_params_from_annotation(annotation)

        if annotation is None or params is None:
            raise AttributeError

        settings_val = cls.settings_getter_().value(
            (*cls.__prefix_categories, cls.__name__, *cls.__suffix_categories),
            key,
            default=_MISSING,
        )
        if settings_val is _MISSING:
            # Couldn't find the value with the settings defined by its class, try fallbacks if any.
            for setting_path in params.fallback_paths:
                settings_val = cls.settings_getter_().value(
                    setting_path,
                    default=_MISSING,
                )
                if settings_val is not _MISSING:
                    break
            else:
                settings_val = params.default

        if params.on_load is not None:
            return params.on_load(settings_val)

        return settings_val

    def __setattr__(cls, key: str, value: t.Any):
        """
        Set the attribute of the object, if the attribute is an annotated setting set it on `_settings`.

        When setting an attribute of an annotated setting, the actual value of the attribute is left unchanged,
        if `cls.auto_sync_` is true, the settings are synced to the file after they're set.

        If the SettingsParams object of the setting defines an `on_save` callable, the callable is applied to `value`
        before it's saved to the class' settings.
        """
        annotation = cls.__annotations__.get(key)
        if annotation is not None:
            params = cls._get_params_from_annotation(annotation)

        if annotation is None or params is None:
            super().__setattr__(key, value)
            return

        if params.on_save is not None:
            value = params.on_save(value)

        cls.settings_getter_().set_value(
            (*cls.__prefix_categories, cls.__name__, *cls.__suffix_categories),
            key,
            value,
        )
        if cls.auto_sync_:
            cls.settings_getter_().sync()

    @staticmethod
    def _get_params_from_annotation(annotation: t.Any) -> t.Optional[SettingsParams]:
        """Try to find a `SettingsParams` object in a `typing.Annotated` `annotation`."""
        annotation_args = t.get_args(annotation)
        return next(
            (ann for ann in annotation_args if isinstance(ann, SettingsParams)), None
        )


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
        settings_objs.add(category.settings_getter_())

    for settings_obj in settings_objs:
        settings_obj.sync()
