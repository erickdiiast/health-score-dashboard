# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Caminho base
base_path = os.path.dirname(os.path.abspath('__file__'))

block_cipher = None

# Configurar dados extras - usar formato tupla (origem, destino)
datas = [
    (os.path.join(base_path, 'templates'), 'templates'),
    (os.path.join(base_path, 'static'), 'static'),
]

a = Analysis(
    ['app.py'],
    pathex=[base_path],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging', 
        'uvicorn.lifespan', 
        'uvicorn.protocols.http', 
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'pandas', 
        'openpyxl',
        'openpyxl.cell._writer',
        'numpy',
        'starlette',
        'fastapi',
        'jinja2',
        'jinja2.ext',
        'python-multipart',
        'pkg_resources',
        'pkg_resources._vendor',
    ],
    hookspath=[],
    hooksconfig={},
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
    [],
    exclude_binaries=True,
    name='HealthScoreDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HealthScoreDashboard',
)
