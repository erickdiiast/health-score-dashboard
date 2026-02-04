# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Caminho base - usa o diretório atual (onde o spec está)
base_path = os.getcwd()

block_cipher = None

# Verifica se as pastas existem
static_path = os.path.join(base_path, 'static')
templates_path = os.path.join(base_path, 'templates')

print(f"Base path: {base_path}")
print(f"Static path: {static_path} - Exists: {os.path.exists(static_path)}")
print(f"Templates path: {templates_path} - Exists: {os.path.exists(templates_path)}")

# Configurar dados extras - usar formato tupla (origem, destino)
datas = []

# Adiciona todos os arquivos da pasta static
if os.path.exists(static_path):
    for root, dirs, files in os.walk(static_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_path)
            datas.append((full_path, os.path.dirname(rel_path)))

# Adiciona todos os arquivos da pasta templates
if os.path.exists(templates_path):
    for root, dirs, files in os.walk(templates_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_path)
            datas.append((full_path, os.path.dirname(rel_path)))

print(f"Total de arquivos a incluir: {len(datas)}")

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
