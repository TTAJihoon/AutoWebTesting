# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — AWT v1.0 Windows 단일 폴더 패키징."""

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # 프롬프트 파일
        (str(ROOT / "prompts"), "prompts"),
        # Playwright 브라우저 번들은 playwright install 후 자동 포함
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "anthropic",
        "psycopg2",
        "playwright.sync_api",
        "openpyxl",
        "fitz",          # PyMuPDF
        "docx",          # python-docx
        "cryptography.fernet",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "numpy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AWT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI 앱: 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "installer" / "awt.ico") if (ROOT / "installer" / "awt.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AWT",
)
