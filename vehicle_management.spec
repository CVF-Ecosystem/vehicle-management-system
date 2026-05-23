# -*- mode: python ; coding: utf-8 -*-
# vehicle_management.spec — PyInstaller spec cho Phần mềm Quản lý Xe V1.0
# Chạy: pyinstaller vehicle_management.spec --clean --noconfirm

import os

block_cipher = None

# Chỉ bundle file tĩnh (ảnh, font) vào _MEIPASS — KHÔNG đưa .py vào datas
_datas = [
    ('assets', 'assets'),   # Logo.jpg, Arial fonts
]
if os.path.isdir('icons') and os.listdir('icons'):
    _datas.append(('icons', 'icons'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        # CustomTkinter + PIL
        'customtkinter',
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageTk',
        # Tkinter internals
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.simpledialog',
        'tkcalendar',
        # Auth / crypto
        'cryptography',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.backends.openssl',
        # Text / locale
        'babel',
        'babel.numbers',
        'babel.dates',
        'dateutil',
        'dateutil.parser',
        # Fuzzy / normalizer
        'rapidfuzz',
        'rapidfuzz.fuzz',
        'unidecode',
        # Data / Excel / Word / PDF
        'pandas',
        'numpy',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'docx',
        'docxtpl',
        'reportlab',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.pdfbase.ttfonts',
        # Charts (pdf_generator dùng matplotlib + seaborn)
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_agg',
        'seaborn',
        # QR code
        'qrcode',
        'qrcode.image.pil',
        # Misc
        'requests',
        'packaging',
        'packaging.version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['streamlit'],
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
