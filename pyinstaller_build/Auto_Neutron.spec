# -*- mode: python ; coding: utf-8 -*-

# Set CWD to project root dir.
os.chdir("..")

block_cipher = None

a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[("resources/icons_library.ico", "."),
                    ("resources/ahk_templates/*", "ahk_templates"),
                    ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Auto Neutron',
          debug=False,
          bootloader_ignore_signals=False,
          icon = "resources/icons_library.ico",
          strip=False,
          upx=True,
          upx_exclude=["qt5core.dll", "qt5widgets.dll", "qt5gui.dll",
               "qt5multimedia.dll", "wmfengine.dll", "qwindows.dll",
               "qtcore.pyd", "msvcp140.dll", "vcruntime140.dll", "qico.dll"],
          runtime_tmpdir=None,
          console=False )
