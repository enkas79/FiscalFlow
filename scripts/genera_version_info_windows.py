"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Genera build_resources/version_info_windows.txt a partire da VERSION.txt,
             così l'eseguibile .exe prodotto da PyInstaller espone sempre lo stesso
             numero di versione dichiarato nel file di versione del progetto.
"""

from __future__ import annotations

import sys
from pathlib import Path

_MODELLO_VERSION_INFO = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tupla_versione}),
    prodvers=({tupla_versione}),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Enrico Martini'),
        StringStruct(u'FileDescription', u'FiscalFlow - Proiezione Fiscale Buste Paga'),
        StringStruct(u'FileVersion', u'{versione}'),
        StringStruct(u'InternalName', u'FiscalFlow'),
        StringStruct(u'LegalCopyright', u'Enrico Martini'),
        StringStruct(u'OriginalFilename', u'FiscalFlow.exe'),
        StringStruct(u'ProductName', u'FiscalFlow'),
        StringStruct(u'ProductVersion', u'{versione}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def leggi_versione(percorso_version_txt: Path) -> str:
    return percorso_version_txt.read_text(encoding="utf-8").strip()


def versione_a_tupla_a_quattro_componenti(versione: str) -> str:
    """Converte '0.0.1' in '0, 0, 1, 0', formato richiesto dalla risorsa versione di Windows."""
    componenti = [int(parte) for parte in versione.split(".")]
    while len(componenti) < 4:
        componenti.append(0)
    return ", ".join(str(c) for c in componenti[:4])


def genera_version_info(versione: str, percorso_output: Path) -> None:
    contenuto = _MODELLO_VERSION_INFO.format(
        tupla_versione=versione_a_tupla_a_quattro_componenti(versione),
        versione=versione,
    )
    percorso_output.parent.mkdir(parents=True, exist_ok=True)
    percorso_output.write_text(contenuto, encoding="utf-8")


if __name__ == "__main__":
    percorso_progetto = Path(__file__).resolve().parent.parent
    versione_richiesta = sys.argv[1] if len(sys.argv) > 1 else leggi_versione(percorso_progetto / "VERSION.txt")
    percorso_output = percorso_progetto / "build_resources" / "version_info_windows.txt"
    genera_version_info(versione_richiesta, percorso_output)
    print(f"Generato {percorso_output} per la versione {versione_richiesta}")
