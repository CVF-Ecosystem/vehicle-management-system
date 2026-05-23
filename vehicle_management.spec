# -*- mode: python ; coding: utf-8 -*-
# vehicle_management.spec — PyInstaller spec cho Phần mềm Quản lý Xe V1.0
# Chạy: pyinstaller vehicle_management.spec --clean --noconfirm

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets',          'assets'),
        ('icons',           'icons'),
        ('config',          'config'),
        ('translations.py', '.'),
        ('config.py',       '.'),
        ('utils.py',        '.'),
        ('data_normalizer.py', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
        'cryptography',
        'rapidfuzz',
        'unidecode',
        'openpyxl',
        'babel',
        'dateutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['streamlit', 'flask', 'pandas', 'numpy'],
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
    name='VehicleManagement',
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
    icon=os.path.join('assets', 'Logo.jpg') if os.path.exists(os.path.join('assets', 'Logo.jpg')) else None,
)
