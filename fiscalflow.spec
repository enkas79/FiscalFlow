# -*- mode: python ; coding: utf-8 -*-
"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Spec file di PyInstaller per generare l'eseguibile/bundle di FiscalFlow su
             Windows, Ubuntu e macOS. Il numero di versione applicativo è letto da
             VERSION.txt (fonte unica di verità) e incorporato nei metadati del pacchetto:
             risorsa versione dell'.exe su Windows, Info.plist su macOS.
"""

import sys
from pathlib import Path

percorso_progetto = Path(SPECPATH)
versione_applicazione = (percorso_progetto / "VERSION.txt").read_text(encoding="utf-8").strip()
percorso_version_info_windows = percorso_progetto / "build_resources" / "version_info_windows.txt"

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[str(percorso_progetto)],
    binaries=[],
    datas=[(str(percorso_progetto / "VERSION.txt"), ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

usa_version_file_windows = sys.platform.startswith("win") and percorso_version_info_windows.exists()

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FiscalFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    version=str(percorso_version_info_windows) if usa_version_file_windows else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FiscalFlow",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="FiscalFlow.app",
        icon=None,
        bundle_identifier="it.enricomartini.fiscalflow",
        info_plist={
            "CFBundleShortVersionString": versione_applicazione,
            "CFBundleVersion": versione_applicazione,
            "NSHighResolutionCapable": True,
        },
    )
