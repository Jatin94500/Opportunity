# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\ACER\\Music\\NuroChain\\dig_os\\ui_shell\\main.py'],
    pathex=['C:\\Users\\ACER\\Music\\NuroChain\\dig_os\\ui_shell'],
    binaries=[],
    datas=[],
    hiddenimports=['PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6'],
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
    name='OpportunityOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
