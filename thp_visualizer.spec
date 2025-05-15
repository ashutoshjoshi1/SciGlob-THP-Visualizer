# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Check if icon file exists
icon_path = 'icon.ico'
if not os.path.exists(icon_path):
    print(f"Warning: Icon file '{icon_path}' not found. Using default icon.")
    icon_path = None

# Check if main_gui.py exists
if not os.path.exists('main_gui.py'):
    print("Error: main_gui.py not found!")
    exit(1)

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[('main_gui.py', '.'), ('controllers', 'controllers'), ('drivers', 'drivers'), ('logs', 'logs')],
    hiddenimports=['pkg_resources.py2_warn', 'numpy', 'pyqtgraph', 'serial', 'serial.tools.list_ports'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='THP_Visualizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep this as True to see error messages
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='THP_Visualizer',
)


