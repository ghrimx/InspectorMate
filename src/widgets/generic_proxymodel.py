"""
Generic, schema-agnostic filter proxy model.

Instead of hard-coding one attribute per filter kind, filters are
registered by name against a column + a filter kind. Any table schema
can reuse this by registering the filters it needs.
"""
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from qtpy import Qt, QtCore


class FilterKind(Enum):
    EXACT_LIST = auto()     # combobox multi-select: row passes if cell value is in an allowed set
    REGEX = auto()          # permanent regex filter, must match (AND'd with everything else)
    TRISTATE_BOOL = auto()  # Qt.CheckState: Checked -> truthy only, Unchecked -> falsy only, else no-op


@dataclass
class ColumnFilter:
    column: int
    kind: FilterKind
    value: Any = None
    role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole
    transform: Callable[[Any], Any] | None = None


class GenericFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Configure independent, named column filters; they combine with AND.
    A separate text-search filter (QLineEdit style) can span several
    columns at once and is OR'd across those columns.
    """

    def __init__(self, model=None, parent=None):
        super().__init__(parent)
        if model is not None:
            self.setSourceModel(model)
        self.setRecursiveFilteringEnabled(True)

        self._filters: dict[str, ColumnFilter] = {}
        self._search_columns: list[int] = []
        self._search_text: str = ""

    # Setup

    def set_filter(self, key: str, column: int, kind: FilterKind, value: Any,
                    role=Qt.ItemDataRole.DisplayRole,
                    transform: Callable[[Any], Any] | None = None) -> None:
        """
        Register or replace a named filter, e.g.:
            proxy.set_filter("owner", column=2, kind=FilterKind.EXACT_LIST, value=["Alice", "Bob"])
            proxy.set_filter("evidence", column=5, kind=FilterKind.TRISTATE_BOOL,
                              value=Qt.CheckState.Checked)
            proxy.set_filter("id_format", column=0, kind=FilterKind.REGEX, value=r"^SIG-\\d+$")
        An empty/None value for EXACT_LIST or a CheckState other than
        Checked/Unchecked means "no filtering" for that key.
        """
        self._filters[key] = ColumnFilter(column, kind, value, role, transform)
        self.invalidateFilter()

    def clear_filter(self, key: str) -> None:
        self._filters.pop(key, None)
        self.invalidateFilter()

    def clear_filters(self) -> None:
        """Remove every registered filter, including the search text/columns."""
        self._filters.clear()
        self._search_columns = []
        self._search_text = ""
        self.invalidateFilter()

    def set_search_text(self, text: str, columns: list[int],
                         role=Qt.ItemDataRole.DisplayRole) -> None:
        """Convenience for the QLineEdit case: OR-match 'text' across 'columns'."""
        self._search_columns = columns
        self._search_role = role
        self._search_text = text.lower()
        self.invalidateFilter()

    # Filtering

    def _cell(self, row: int, column: int, role, transform, parent) -> Any:
        index = self.sourceModel().index(row, column, parent)
        data = self.sourceModel().data(index, role)
        return transform(data) if transform else data

    def _matches(self, row: int, cf: ColumnFilter, parent) -> bool:
        data = self._cell(row, cf.column, cf.role, cf.transform, parent)

        if cf.kind == FilterKind.EXACT_LIST:
            if not cf.value:
                return True
            return data in cf.value

        if cf.kind == FilterKind.REGEX:
            pattern = QtCore.QRegularExpression(
                cf.value, QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption)
            return pattern.match(str(data)).hasMatch()

        if cf.kind == FilterKind.TRISTATE_BOOL:
            if cf.value == Qt.CheckState.Checked:
                return bool(data)
            if cf.value == Qt.CheckState.Unchecked:
                return not bool(data)
            return True  # PartiallyChecked / unset -> no filtering

        return True

    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
        for cf in self._filters.values():
            if not self._matches(source_row, cf, source_parent):
                return False

        return not (
            self._search_text
            and self._search_columns
            and not any(
                self._search_text
                in str(
                    self._cell(source_row, col, self._search_role, None, source_parent)
                ).lower()
                for col in self._search_columns
            )
        )

    # Sorting

    def sort_tree(self, column: int = 0,
                  order: Qt.SortOrder = Qt.SortOrder.AscendingOrder,
                  parent: QtCore.QModelIndex | None = None) -> None:
        if parent is None:
            parent = QtCore.QModelIndex()
        self.sort(column, order)
        for row in range(self.rowCount(parent)):
            child = self.index(row, 0, parent)
            self.sort_tree(column, order, child)


# --------------------------------------------------------------------
# Equivalent to the old two classes, expressed with the new one:
#
#   proxy = GenericFilterProxyModel(source_model)
#
#   # was: setPermanentFilter(pattern, columns) applied per-column with AND
#   for i, col in enumerate(permanent_columns):
#       proxy.set_filter(f"perm_{i}", col, FilterKind.REGEX, pattern)
#
#   # was: setUserFilter(pattern, columns) -> QLineEdit search, OR across columns
#   proxy.set_search_text(text, columns=user_columns)
#
#   # was: setSatusFilter(statuses, column)
#   proxy.set_filter("status", status_column, FilterKind.EXACT_LIST, statuses)
#
#   # was: setTypeFilter(signage_types, column)
#   proxy.set_filter("type", types_column, FilterKind.EXACT_LIST, signage_types)
#
#   # was: setOwnerFilter(owners, column)  (SignageProxyModel)
#   proxy.set_filter("owner", owner_column, FilterKind.EXACT_LIST, owners)
#
#   # was: setEvidenceFilter(evidence_only, column)  (SignageProxyModel)
#   proxy.set_filter("evidence", evidence_column, FilterKind.TRISTATE_BOOL, evidence_only)
# --------------------------------------------------------------------


