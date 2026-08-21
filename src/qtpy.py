"""
Central Qt import shim. Every other module imports Qt through here, never
directly from PyQt6 — keeps a PySide6 migration (if it ever happens) to a
single-file change, and normalizes Signal/Slot naming to the PySide style.
"""
import PyQt6Ads as QtAds
from PyQt6 import QtCore, QtGui, QtSql, QtWidgets
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtCore import pyqtSlot as Slot
from PyQt6.QtSql import QSqlRelationalTableModel

__all__ = [
    "QSettings",
    "QSqlRelationalTableModel",
    "Qt",
    "QtAds",
    "QtCore",
    "QtGui",
    "QtSql",
    "QtWidgets",
    "Signal",
    "Slot",
]