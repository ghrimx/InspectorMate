import typing
from qtpy import (QtCore, QtWidgets)

class TreeView(QtWidgets.QTreeView):
    """Read-Only Custom QTreeView"""
    def __init__(self, parent=None, sorting_enabled: bool = True, hide_header: bool = False, border: bool = True) -> None:
        super().__init__(parent)
        self.setSortingEnabled(sorting_enabled)
        self.setHeaderHidden(hide_header)
        self.set_border(border)
        self.setMinimumWidth(150)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)  # Make ReadOnly

    def set_border(self, border):
        if not border: 
            self.setStyleSheet("""QTreeView { border: none; }""")

    def hide_columns(self, columns:typing.List[int]):
        """Hide columns.
        
            Args:
                List of int
        """
        for column in columns:
            self.setColumnHidden(column,True)

    def clear_view(self) -> None:
        """Clearing the TreeView."""
        self.destroy(destroySubWindows=True)

    def set_sorting_column(self, col: int):
        self.sortByColumn(col, QtCore.Qt.SortOrder.AscendingOrder)

    def selectedRows(self) -> list[int]:
        indexes = self.selectedIndexes()
        rows = []
        row = -1
        for index in indexes:
            if row != index.row():
                row = index.row()
                rows.append(row)
        return rows


