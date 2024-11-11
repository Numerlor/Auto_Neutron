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
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Auto_Neutron_debug",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="file_version_info.txt",
)
coll = COLLECT(
    exe,
    filter_binaries(a.binaries),
    a.zipfiles,
    filter_datas(a.datas),
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Auto_Neutron_debug",
)
