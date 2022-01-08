# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from typing_extensions import Self


class UninitializedAccessError(Exception):
    """Raised on access of uninitialized values from the ForbidUninitialized descriptor."""


class ForbidUninitialized:
    """
    Descriptor that raises on access of initialized attributes.

    The uninitialized value to raise on is taken as an argument, and None by default.
    """

    def __init__(self, uninitialized_value: object = None):
        self.uninitialized_value = uninitialized_value

    def __set_name__(self, owner: type, name: str) -> None:
        """Save the attribute's name and create a private name for use by the descriptor on the instance."""
        self._name = name
        self._private_name = f"_{self.__class__.__name__}_" + name

    @t.overload
    def __get__(self, instance: None, owner: None) -> Self:
        ...

    @t.overload
    def __get__(self, instance: object, owner: t.Optional[type] = ...) -> object:
        ...

    def __get__(
        self, instance: t.Optional[object], owner: t.Optional[type] = None
    ) -> t.Union[Self, object]:
        """If called from a class, return the descriptor, otherwise return the attribute or raise a RuntimeError."""
        if instance is None:
            return self

        value = getattr(instance, self._private_name, self.uninitialized_value)
        if value is self.uninitialized_value:
            raise UninitializedAccessError(
                f"Access of uninitialized attribute {self._name!r} from {owner.__qualname__!r} object at {hex(id(instance))}."
            )
        return value

    def __set__(self, instance: object, value: object) -> None:
        """Set the attribute's value."""
        if value is self:
            return
        setattr(instance, self._private_name, value)
