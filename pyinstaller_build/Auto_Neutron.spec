# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["..\\main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("../resources/icons_library.ico", "./resources"),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Auto_Neutron",
    debug=False,
    bootloader_ignore_signals=False,
    icon="../resources/icons_library.ico",
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
)
