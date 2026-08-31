# -*- mode: python ; coding: utf-8 -*-
import os

# SPECPATH lo define PyInstaller en tiempo de ejecucion del .spec: es la carpeta
# donde vive este archivo. Usarlo (en vez de rutas relativas "pelonas") hace que
# el build funcione sin importar desde donde se invoque pyinstaller
# (p. ej. `pyinstaller app/GUI_Watermark.spec` desde la raiz del proyecto).
here = SPECPATH

a = Analysis(
    [os.path.join(here, 'GUI_Watermark.py')],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(here, 'rec.jpg'), '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GUI_Watermark',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GUI_Watermark',
)
