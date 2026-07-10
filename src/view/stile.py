"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Foglio di stile (QSS) applicato all'intera applicazione per un aspetto
             moderno e coerente: palette chiara, angoli arrotondati, spaziature e stati
             hover/pressed sui controlli interattivi.
"""

from __future__ import annotations

FOGLIO_STILE: str = """
QWidget {
    background-color: #f4f6f9;
    color: #1f2933;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 10.5pt;
}

QMainWindow {
    background-color: #f4f6f9;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 10px;
    margin-top: 16px;
    padding: 12px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #2f6fed;
}

QPushButton {
    background-color: #2f6fed;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #255bd1;
}
QPushButton:pressed {
    background-color: #1d49ab;
}
QPushButton:disabled {
    background-color: #b7c3e0;
    color: #eef1f8;
}

QLabel {
    background: transparent;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 8px;
    gridline-color: #eef1f4;
    selection-background-color: #dbe6fd;
    selection-color: #1f2933;
    alternate-background-color: #f8fafc;
}
QHeaderView::section {
    background-color: #eef1f6;
    color: #1f2933;
    padding: 6px 10px;
    border: none;
    border-bottom: 2px solid #dfe3e8;
    font-weight: 600;
}
QTableWidget::item {
    padding: 4px 8px;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #c3cbd6;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dfe3e8;
    padding: 2px;
}
QMenuBar::item {
    padding: 6px 12px;
    border-radius: 4px;
    background: transparent;
}
QMenuBar::item:selected {
    background-color: #eef1f6;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #dbe6fd;
}
QMenu::separator {
    height: 1px;
    background: #dfe3e8;
    margin: 4px 8px;
}

QDialog {
    background-color: #f4f6f9;
}

QTextBrowser {
    background-color: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 8px;
    padding: 8px;
}

QMessageBox {
    background-color: #ffffff;
}

QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #dfe3e8;
    color: #52606d;
}
"""
