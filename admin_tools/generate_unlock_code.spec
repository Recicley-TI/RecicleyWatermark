# -*- mode: python ; coding: utf-8 -*-
# Empaqueta admin_tools/generate_unlock_code.py como un .exe de un solo
# archivo (onefile), para que Recicley-TI pueda generar códigos de
# activación sin tener Python instalado en la máquina de soporte.
#
# OJO: este .exe NO lleva la clave privada adentro. private_key.pem se
# sigue leyendo desde el disco, al lado del .exe (ver _here() en
# generate_unlock_code.py) — así que hay que copiar ambos archivos juntos
# a la máquina de soporte, y nunca subir ninguno de los dos al repo.
#
# Build:
#   python -m PyInstaller admin_tools/generate_unlock_code.spec --noconfirm
import os

here = SPECPATH

a = Analysis(
    [os.path.join(here, 'generate_unlock_code.py')],
    pathex=[],
    binaries=[],
    datas=[],
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
    a.binaries,
    a.datas,
    [],
    name='Recicley_GenerarCodigoActivacion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
