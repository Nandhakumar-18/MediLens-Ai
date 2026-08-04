# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('modules', 'modules'),
    ('database', 'database'),
    ('medilensai.db', '.'),
]

# Include Tesseract OCR binaries if present on build machine
tesseract_dir = r'C:\Program Files\Tesseract-OCR'
if os.path.exists(tesseract_dir):
    added_files.append((tesseract_dir, 'Tesseract-OCR'))

a = Analysis(
    ['run_desktop.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'waitress',
        'fitz',
        'pytesseract',
        'PIL',
        'cv2',
        'qrcode',
        'fpdf2',
        'matplotlib',
        'sqlite3',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MediLensAI_Setup',
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
    icon=None,
)
