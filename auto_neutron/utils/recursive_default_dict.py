# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

import typing as t

_KT = t.TypeVar("_KT")
_VT = t.TypeVar("_VT")
_S = t.TypeVar("_S", bound="RecursiveDefaultDict")


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
