from pathlib import Path
from dataclasses import dataclass

from qtpy import QtCore
from PyQt6.QtCore import (QObject, Qt, 
                          QModelIndex,
                          QSortFilterProxyModel,
                          QRegularExpression)
from PyQt6.QtSql import QSqlRelationalTableModel

from db.database import AppDatabase

@dataclass
class DatabaseField:
    name: str
    index: int
    visible: bool

class BaseRelationalTableModel(QSqlRelationalTableModel):

    class Fields: DatabaseField

    def __init__(self):
        super().__init__()

    def visible_fields(self) -> list[int]:
        """Return a list[int] of visible fields"""
        visible_fields = []
        for name, field in vars(self.Fields).items():
            if not name.startswith('_'):
                if field.visible:
                    visible_fields.append(field.index)
        return visible_fields
    
    def hidden_fields(self) -> set[int]:
        """Return a list[int] of hidden fields"""
        return set(range(self.columnCount()))-set(self.visible_fields())
    
    def refresh(self):
        """Refresh the table view"""
        r = self.select()
        self.setFilter(f"workspace_id={AppDatabase.active_workspace.id}")
        return r

    def apply_filter(self, field, value):
        """
        Apply filter to the QSqlRelationalTableModel

            args:
                field: database field
                value: value of the WHERE clause
        """
        self.setFilter(f"{field} LIKE '{value}%' AND workspace_id='{AppDatabase.active_workspace.id}'")

    def deleteRow(self, row: int) -> bool:
        res = self.removeRow(row)
        if res:
            self.submitAll()

        return res

class ProxyModel(QSortFilterProxyModel):

    def __init__(self, model):
        super().__init__()

        self.setSourceModel(model)

        self.permanent_filter = QRegularExpression()
        self.user_filter = QRegularExpression()
        self.permanent_columns = []
        self.user_columns = []
        self.status_filter = []
        self.status_columns = []

    def setPermanentFilter(self, pattern: str, columns: list):
        self.permanent_filter = QRegularExpression(pattern, QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.permanent_columns = columns

    def setUserFilter(self, pattern: str, columns: list):
        self.user_filter = pattern.lower()
        self.user_columns = columns

    def setSatusFilter(self, statuses: list, column: int):
        self.status_filter = statuses
        self.status_column = column
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        user_filter = True
        status_filter = True

        # Apply the permanent filter on the specified column
        for col in self.permanent_columns:
            index_perm = self.sourceModel().index(source_row, col, source_parent)
            data_perm = str(self.sourceModel().data(index_perm))
            if not self.permanent_filter.match(data_perm).hasMatch():
                return False
            
        if len(self.status_filter) > 0:
            index_status = self.sourceModel().index(source_row, self.status_column, source_parent)
            data_status = self.sourceModel().data(index_status)
            if data_status in self.status_filter:
                status_filter = True
            else:
                status_filter = False

        # Apply the user filter on the specified columns
        for column in self.user_columns:
            index_user = self.sourceModel().index(source_row, column, source_parent)
            data_user = str(self.sourceModel().data(index_user)).lower()

            if self.user_filter not in data_user:
                user_filter = False
            else: 
                user_filter = True
                break
            
        return user_filter and status_filter

    
