# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import collections.abc
import typing as t
from contextlib import contextmanager

_KT = t.TypeVar("_KT")
_VT = t.TypeVar("_VT")
_S = t.TypeVar("_S", bound="RecursiveDefaultDict")
_DEFAULT_SENTINEL = object()


class RecursiveDefaultDict(dict[_KT, _VT], t.Generic[_KT, _VT]):
    """
    A recursive default dict.

    The creation of missing keys can be disabled by setting the `create_missing` attribute to False.
    This will propagate to all the `RecursiveDefaultDict`'s created by this class as defaults,
    if they didn't have the attribute set explicitly by the user, or if it is None.
    """

    def __init__(
        self,
        *,
        create_missing: t.Optional[bool] = True,
        parent: t.Optional[RecursiveDefaultDict] = None,
    ):
        super().__init__()
        self.parent = parent
        self._create_missing = create_missing

    def update_from_dict_recursive(
        self: _S, dict_: dict[_KT, _VT], *, ignore_conflicts: bool = True
    ) -> None:
        """Add the contents from `dict_` and replaces all dictionaries with this type."""
        with self.disable_defaults_for_missing():
            for key, value in dict_.items():
                if isinstance(value, dict):
                    check_conflict = not ignore_conflicts and key in self
                    if check_conflict and not isinstance(self[key], dict):
                        self._check_conflict(self, key, value)

                    new_dict = self.__class__(create_missing=None, parent=self)
                    if key in self:
                        new_dict.update_from_dict_recursive(self[key])
                    new_dict.update_from_dict_recursive(value)
                    value = new_dict

                    if check_conflict:
                        for sub_key in new_dict.keys() & self[key].keys():
                            self._check_conflict(self[key], sub_key, new_dict[sub_key])
                else:
                    if not ignore_conflicts:
                        self._check_conflict(self, key, value)
                self[key] = value

    @property
    def create_missing(self) -> bool:
        """
        Return whether this dict should create new defaults on missing keys.

        If this is unset, try to grab the value from the parent.
        """
        if self._create_missing is not None:
            return self._create_missing
        if self.parent is None:
            raise ValueError("Top dict has unset 'create_missing' attribute.")
        return self.parent.create_missing

    @create_missing.setter
    def create_missing(self, create_missing: bool) -> None:
        """Return whether this dict should create new defaults on missing keys."""
        self._create_missing = create_missing

    def __missing__(self: _S, key: _KT) -> _S:
        if self.create_missing:
            created_dict = self.__class__(create_missing=None, parent=self)
            self[key] = created_dict
            return created_dict
        raise KeyError(key)

    @contextmanager
    def disable_defaults_for_missing(self) -> collections.abc.Iterator[None]:
        """Disable creating defaults for missing keys for the duration of the context manager."""
        old_create_missing = self._create_missing
        self._create_missing = False
        try:
            yield
        finally:
            self._create_missing = old_create_missing

    @staticmethod
    def _check_conflict(
        dict_: dict, key: collections.abc.Hashable, new_value: object
    ) -> None:
        """Check if `key`'s value in `dict_` differs from `new_value`, if it does raise a ValueError."""
        if (
            current_value := dict_.get(key, _DEFAULT_SENTINEL)
        ) is not _DEFAULT_SENTINEL:
            if current_value != new_value:
                raise ValueError(
                    f"Value conflict with {key=!r} {current_value=!r} {new_value=!r}."
                )
