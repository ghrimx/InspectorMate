"""
Generic filter dialog, paired with 'generic_proxy_model.py'.

Instead of one hard-coded row per attribute, the dialog is built from a list of
FilterField specs. Each spec says which widget to show, which combo items to
load, and which column/FilterKind it maps to on the proxy. get_filters()
returns exactly what GenericFilterProxyModel.set_filter(**kwargs) expects.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from my_pyqt_widgets import ClearableComboBox, MultiCheckableComboBox

from qtpy import Qt, QtCore, QtGui, QtWidgets
from widgets.generic_proxymodel import FilterKind

# Default options for a TRISTATE_BOOL field, when no custom 'items' is given.
DEFAULT_TRISTATE_ITEMS = [
    ("All", Qt.CheckState.PartiallyChecked),
    ("Checked", Qt.CheckState.Checked),
    ("Unckecked", Qt.CheckState.Unchecked),
]


@dataclass
class FilterField:
    key: str                       # matches the key passed to proxy.set_filter()
    label: str                     # row label in the form
    column: int                    # target column in the source model
    kind: FilterKind               # EXACT_LIST or TRISTATE_BOOL

    # items: (display_text, data_value) pairs.
    # EXACT_LIST: required, populates a checkable multi-select combo.
    # TRISTATE_BOOL: optional, defaults to DEFAULT_TRISTATE_ITEMS; data_value should be a Qt.CheckState.
    items: list[tuple[str, Any]] | None = None
    items_provider: Callable[[], list[tuple[str, Any]]] | None = None  # lazy alternative to 'items'
    widget_class: type = MultiCheckableComboBox           # EXACT_LIST only: or MultiCheckableComboBox, or your own

    role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole


class GenericFilterDialog(QtWidgets.QDialog):
    def __init__(self, fields: list[FilterField], parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Popup)
        self.fields = fields
        self._widgets: dict[str, QtWidgets.QWidget] = {}

        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        for f in fields:
            if f.kind == FilterKind.EXACT_LIST:
                combo: MultiCheckableComboBox | ClearableComboBox = f.widget_class()
                items = f.items_provider() if f.items_provider else (f.items or [])
                for text, data in items:
                    combo.addItem(text, data)
                form.addRow(f"{f.label}:", combo)
                self._widgets[f.key] = combo

            elif f.kind == FilterKind.TRISTATE_BOOL:
                combo = QtWidgets.QComboBox()
                items = f.items_provider() if f.items_provider else (f.items or DEFAULT_TRISTATE_ITEMS)
                for text, data in items:
                    combo.addItem(text, data)
                form.addRow(f"{f.label}:", combo)
                self._widgets[f.key] = combo

            else:
                raise ValueError(f"Unsupported FilterKind for a dialog field: {f.kind}")

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok
                   | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        form.addWidget(self.buttonBox)

    # ---------------------------------------------------------------

    def resetFields(self):
        for f in self.fields:
            widget: MultiCheckableComboBox | ClearableComboBox = self._widgets[f.key]
            if f.kind == FilterKind.EXACT_LIST:
                if hasattr(widget, "clearSelection"):
                    widget.clearSelection()
            elif f.kind == FilterKind.TRISTATE_BOOL:
                widget.setCurrentIndex(0)

    def get_filters(self) -> dict[str, dict]:
        """
        Returns {key: kwargs} ready to apply, e.g.:
            for key, kwargs in dialog.get_filters().items():
                proxy.set_filter(key, **kwargs)
        Empty EXACT_LIST selections and the default TRISTATE_BOOL option
        (index 0, "All"/PartiallyChecked) are included with a "no-op" value
        rather than omitted, so calling this after resetFields() clears any
        previously-applied filter too.
        """
        result = {}
        for f in self.fields:
            widget: MultiCheckableComboBox | ClearableComboBox = self._widgets[f.key]
            value = widget.currentData()
            result[f.key] = {"column": f.column, "kind": f.kind, "value": value, "role": f.role}
        return result

    def popupNear(self, anchor: QtWidgets.QWidget) -> None:
        """
        Position the dialog just below 'anchor', clamped to the screen's
        available geometry - mirrors QMenu's default popup placement.
        """
        self.adjustSize()
        pos = anchor.mapToGlobal(QtCore.QPoint(0, anchor.height()))
        screen = anchor.screen() or QtGui.QGuiApplication.primaryScreen()
        available = screen.availableGeometry()

        pos.setX(min(max(pos.x(), available.left()), available.right() - self.width()))
        pos.setY(min(max(pos.y(), available.top()), available.bottom() - self.height()))

        self.move(pos)


# --------------------------------------------------------------------
# Example:
#
#   fields = [
#       FilterField(
#           key="status", label="Status", column=STATUS_COL, kind=FilterKind.EXACT_LIST,
#           items=[(item.name, item.name) for item in AppDatabase.cache_signage_status.values()],
#           widget_class=MultiCheckableComboBox,
#       ),
#       FilterField(
#           key="type", label="Type", column=TYPE_COL, kind=FilterKind.EXACT_LIST,
#           items=[(item.name, item.name) for item in AppDatabase.cache_signage_type.values()],
#       ),
#       FilterField(
#           key="owner", label="Owner", column=OWNER_COL, kind=FilterKind.EXACT_LIST,
#           items_provider=lambda: [(o, o) for o in settings.value("owners", [], "QStringList")],
#       ),
#       FilterField(
#           key="evidence", label="Evidence", column=EVIDENCE_COL, kind=FilterKind.TRISTATE_BOOL,
#       ),
#   ]
#
#   dialog = GenericFilterDialog(fields, parent=self)
#   if dialog.exec():
#       for key, kwargs in dialog.get_filters().items():
#           proxy.set_filter(key, **kwargs)
# --------------------------------------------------------------------