# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('app', 'app')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off', 'psutil', 'platformdirs', 'httpx'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# Filter out models from the build in case any linger in the development directory
# We ensure the distribution bundle remains lightweight.
def exclude_models(datas):
    filtered_datas = []
    for data in datas:
        # data is a tuple (dest, source, type)
        dest = data[0].replace(os.sep, '/')
        if 'app/models/' in dest and dest.endswith('.onnx'):
            continue
        filtered_datas.append(data)
    return filtered_datas

a.datas = exclude_models(a.datas)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PictoPy_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # disabled until DLL compatibility is validated
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    upx=False,          # disabled until DLL compatibility is validated
    upx_exclude=[],
    name='PictoPy_Server',
)
