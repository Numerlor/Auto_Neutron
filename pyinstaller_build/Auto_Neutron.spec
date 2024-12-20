# -*- mode: python ; coding: utf-8 -*-

from spec_helper import *

block_cipher = None

a = Analysis(
    ["..\\main.py"],
    pathex=["."],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    filter_binaries(a.binaries),
    OPTIONS,
    a.zipfiles,
    filter_datas(a.datas),
    [],
    name="Auto_Neutron",
    debug=False,
    bootloader_ignore_signals=False,
    icon="../resources/icons_library.ico",
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    version="file_version_info.txt",
)
