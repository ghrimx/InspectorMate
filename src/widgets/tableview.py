from qtpy import QtWidgets
from delegates.delegate import ReadOnlyDelegate

class TableView(QtWidgets.QTableView):
    def __init__(self):
        super().__init__()
        self.setSortingEnabled(True)

    def hide_columns(self, columns:list[int]):
        """Hide columns provided in List[int]"""

        for column in columns:
            self.setColumnHidden(column,True)

    def resize_column_toContents(self, col: int):
        self.resizeColumnToContents(col)

    def set_model(self, model):
        self.setModel(model)
        self.resizeColumnsToContents() 
        self.hide_rows_index(False)

    def hide_rows_index(self, b:bool = True):
        self.verticalHeader().setVisible(b)

    def read_only(self):
        """Set full tableview read-only"""
        delegate = ReadOnlyDelegate()
        self.setItemDelegate(delegate)

    def column_read_only(self, col):
        """Set specified column read-only"""
        delegate = ReadOnlyDelegate()
        self.setItemDelegateForColumn(col, delegate)

    def set_delegate(self, col, delegate):
        self.setItemDelegateForColumn(col, delegate)

        
