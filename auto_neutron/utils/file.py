# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import ctypes
import msvcrt
import os
import sys
import typing as t
from ctypes import wintypes
from pathlib import Path

GENERIC_WRITE = 0x40000000
FILE_SHARE_DELETE = 0x00000004
FILE_SHARE_READ = 0x00000001
CREATE_ALWAYS = 2
FILE_ATTRIBUTE_NORMAL = 128
INVALID_HANDLE_VALUE = -1

CreateFileW = ctypes.windll.Kernel32.CreateFileW
CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]

GetFinalPathNameByHandle = ctypes.windll.Kernel32.GetFinalPathNameByHandleW
GetFinalPathNameByHandle.argtypes = [
    wintypes.HANDLE,
    ctypes.c_wchar_p,
    wintypes.DWORD,
    wintypes.DWORD,
]


def create_delete_share_file(
    file: Path, encoding: t.Optional[str] = None, errors: t.Optional[str] = None
) -> t.TextIO:
    """
    Open the file at path with the `FILE_SHARE_DELETE` flag enabled.

    This allows us to move the file while it is being written to.
    """
    handle = CreateFileW(
        str(file),
        GENERIC_WRITE,
        FILE_SHARE_DELETE | FILE_SHARE_READ,
        None,
        CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == -1:
        raise ctypes.WinError()

    return open(
        msvcrt.open_osfhandle(handle, os.O_BINARY),
        "w",
        encoding=encoding,
        errors=errors,
    )


def get_file_name(file: t.IO) -> str:
    """Get the path of `file`."""
    handle = msvcrt.get_osfhandle(file.fileno())
    buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH)

    ret_val = GetFinalPathNameByHandle(handle, buffer, wintypes.MAX_PATH, 0)
    if ret_val > wintypes.MAX_PATH:
        buffer = ctypes.create_unicode_buffer(ret_val)
        ret_val = GetFinalPathNameByHandle(handle, buffer, ret_val, 0)

    if ret_val == 0:
        raise ctypes.WinError()

    return buffer.value.removeprefix("\\\\?\\")


def base_path() -> Path:
    """Get the script's base path, using pyinstaller's temp directory when built, the project root otherwise."""
    return Path(getattr(sys, "_MEIPASS", Path(sys.argv[0]).parent))
