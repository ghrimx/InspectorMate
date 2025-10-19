from qtpy import QtCore, QtGui



class ProxyModel(QtCore.QSortFilterProxyModel):

    def __init__(self, model):
        super().__init__()
        self.setSourceModel(model)

        self.permanent_filter = QtCore.QRegularExpression()
        self.user_filter = QtCore.QRegularExpression()
        self.permanent_columns = []
        self.user_columns = []
        self.status_filter = []
        self.types_filter = []

    def setPermanentFilter(self, pattern: str, columns: list):
        self.permanent_filter = QtCore.QRegularExpression(pattern,
                                                          QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.permanent_columns = columns

    def setUserFilter(self, pattern: str, columns: list):
        self.user_filter = pattern.lower()
        self.user_columns = columns

    def setSatusFilter(self, statuses: list, column: int):
        self.status_filter = statuses
        self.status_column = column

    def setTypeFilter(self, signage_types: list, column: int):
        self.types_filter = signage_types
        self.types_column = column
    
    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
        user_filter = True
        status_filter = True
        types_filter = True

        # Apply the permanent filter on the specified column
        for col in self.permanent_columns:
            index_perm = self.sourceModel().index(source_row, col, source_parent)
            data_perm = str(self.sourceModel().data(index_perm))
            if not self.permanent_filter.match(data_perm).hasMatch():
                return False
            
        if len(self.status_filter) > 0:
            index_status = self.sourceModel().index(source_row, self.status_column, source_parent)
            data_status = self.sourceModel().data(index_status, QtCore.Qt.ItemDataRole.DisplayRole)
            if data_status in self.status_filter:
                status_filter = True
            else:
                status_filter = False

        if len(self.types_filter) > 0:
            index_type = self.sourceModel().index(source_row, self.types_column, source_parent)
            data_type = self.sourceModel().data(index_type, QtCore.Qt.ItemDataRole.DisplayRole)
            if data_type in self.types_filter:
                types_filter = True
            else:
                types_filter = False

        # Apply the user filter on the specified columns
        for column in self.user_columns:
            index_user = self.sourceModel().index(source_row, column, source_parent)
            data_user = str(self.sourceModel().data(index_user, QtCore.Qt.ItemDataRole.DisplayRole)).lower()

            if self.user_filter not in data_user:
                user_filter = False
            else: 
                user_filter = True
                break
            
        return user_filter and status_filter and types_filter


class TreeItem:
    def __init__(self, data: list, parent: 'TreeItem' = None):
        self.item_data = data
        self.parent_item = parent
        self.child_items = []

    def child(self, number: int) -> 'TreeItem':
        if number < 0 or number >= len(self.child_items):
            return None
        return self.child_items[number]

    def lastChild(self):
        return self.child_items[-1] if self.child_items else None

    def childCount(self) -> int:
        return len(self.child_items)

    def childNumber(self) -> int:
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

    def columnCount(self) -> int:
        return len(self.item_data)

    def data(self, column: int):
        if column < 0 or column >= len(self.item_data):
            return None
        return self.item_data[column]

    def insertChildren(self, position: int, count: int, columns: int) -> bool:
        if position < 0 or position > len(self.child_items):
            return False

        for row in range(count):
            data = [None] * columns
            item = TreeItem(data.copy(), self)
            self.child_items.insert(position, item)

        return True

    def insertColumns(self, position: int, columns: int) -> bool:
        if position < 0 or position > len(self.item_data):
            return False

        for column in range(columns):
            self.item_data.insert(position, None)

        child: TreeItem
        for child in self.child_items:
            child.insertColumns(position, columns)

        return True

    def parent(self):
        return self.parent_item

    def removeChildren(self, position: int, count: int) -> bool:
        if position < 0 or position + count > len(self.child_items):
            return False

        for row in range(count):
            self.child_items.pop(position)

        return True

    def removeColumns(self, position: int, columns: int) -> bool:
        if position < 0 or position + columns > len(self.item_data):
            return False

        for column in range(columns):
            self.item_data.pop(position)

        child: TreeItem
        for child in self.child_items:
            child.removeColumns(position, columns)

        return True

    def setData(self, column: int, value):
        if column < 0 or column >= len(self.item_data):
            return False

        self.item_data[column] = value
        return True
    
    def findChildById(self, target_id, id_column=0) -> 'TreeItem | None':
        """Recursively search for a TreeItem whose data[id_column] == target_id."""
        if self.data(id_column) == target_id:
            return self

        child: TreeItem
        for child in self.child_items:
            result = child.findChildById(target_id, id_column)
            if result:
                return result

        return None

    def __repr__(self) -> str:
        result = f"<treeitem.TreeItem at 0x{id(self):x}"
        for d in self.item_data:
            result += f' "{d}"' if d else " <None>"
        result += f", {len(self.child_items)} children>"
        return result
    

class TreeModel(QtCore.QAbstractItemModel):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.headers = []
        self.root_item: TreeItem = None
        self._data = None

    def columnCount(self, parent: QtCore.QModelIndex = None) -> int:
        return self.root_item.columnCount()
    
    def data(self, index: QtCore.QModelIndex, role: int = None):
        if not index.isValid():
            return None

        if role != QtCore.Qt.ItemDataRole.DisplayRole and role != QtCore.Qt.ItemDataRole.EditRole:
            return None
        item: TreeItem = self.getItem(index)

        return item.data(index.column())
    
    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags

        return QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.QAbstractItemModel.flags(self, index)

    def getItem(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> TreeItem:
        if index.isValid():
            item: TreeItem = index.internalPointer()
            if item:
                return item

        return self.root_item
    
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation,
                   role: int = QtCore.Qt.ItemDataRole.DisplayRole):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.root_item.data(section)

        return None
    
    def index(self, row: int, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        parent_item: TreeItem = self.getItem(parent)
        if not parent_item:
            return QtCore.QModelIndex()

        child_item: TreeItem = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QtCore.QModelIndex()
    
    def insertColumns(self, position: int, columns: int,
                      parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        self.beginInsertColumns(parent, position, position + columns - 1)
        success: bool = self.root_item.insertColumns(position, columns)
        self.endInsertColumns()

        return success
    
    def insertRows(self, position: int, rows: int,
                   parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        parent_item: TreeItem = self.getItem(parent)
        if not parent_item:
            return False

        self.beginInsertRows(parent, position, position + rows - 1)
        column_count = self.root_item.columnCount()
        success: bool = parent_item.insertChildren(position, rows, column_count)
        self.endInsertRows()

        return success

    def parent(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item: TreeItem = self.getItem(index)
        if child_item:
            parent_item: TreeItem = child_item.parent()
        else:
            parent_item = None

        if parent_item == self.root_item or not parent_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.childNumber(), 0, parent_item)

    def removeColumns(self, position: int, columns: int,
                      parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success: bool = self.root_item.removeColumns(position, columns)
        self.endRemoveColumns()

        if self.root_item.columnCount() == 0:
            self.removeRows(0, self.rowCount())

        return success

    def removeRows(self, position: int, rows: int,
                   parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        parent_item: TreeItem = self.getItem(parent)
        if not parent_item:
            return False

        self.beginRemoveRows(parent, position, position + rows - 1)
        success: bool = parent_item.removeChildren(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent.isValid() and parent.column() > 0:
            return 0

        parent_item: TreeItem = self.getItem(parent)
        if not parent_item:
            return 0
        return parent_item.childCount()

    def setData(self, index: QtCore.QModelIndex, value, role: int) -> bool:
        if role != QtCore.Qt.ItemDataRole.EditRole:
            return False

        item: TreeItem = self.getItem(index)
        result: bool = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index,
                                  index,
                                  [QtCore.Qt.ItemDataRole.DisplayRole,
                                   QtCore.Qt.ItemDataRole.EditRole])

        return result

    def setHeaderData(self, section: int, orientation: QtCore.Qt.Orientation, value,
                      role: int = None) -> bool:
        if role != QtCore.Qt.ItemDataRole.EditRole or orientation != QtCore.Qt.Orientation.Horizontal:
            return False

        result: bool = self.root_item.setData(section, value)

        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result
    
    def findIndexById(self, target_id, id_column=0) -> QtCore.QModelIndex:
        """Return QModelIndex for TreeItem with given ID, or invalid index if not found."""
        if not target_id:
            return QtCore.QModelIndex()

        item = self.root_item.findChildById(target_id, id_column)
        if not item or item == self.root_item:
            return QtCore.QModelIndex()

        parent = item.parent_item
        row = parent.child_items.index(item)
        return self.createIndex(row, id_column, item)


class SummaryModel(QtCore.QAbstractTableModel):

    def __init__(self, data=[[]]):
        super().__init__()
        self._data = data
        self.header = []
        self.vheader = []

    def data(self, index, role):
        if len(self._data) > 0:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:

                if index.row() < len(self._data) - 1:
                    if self._data[-1][index.column()] > 0:
                        percentage = round(self._data[index.row()][index.column()]/self._data[-1][index.column()] * 100)
                    else:
                        percentage = "-"
                    return f"{self._data[index.row()][index.column()]} ({percentage}%)"
                return self._data[index.row()][index.column()]
            
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            return QtCore.Qt.AlignmentFlag.AlignVCenter + QtCore.Qt.AlignmentFlag.AlignHCenter
        
        if role ==  QtCore.Qt.ItemDataRole.ForegroundRole:
            value = self._data[index.row()][index.column()]

            if ((isinstance(value, int) or isinstance(value, float)) and value == 0):
                return QtGui.QColor('lightGray')
            
        if role == QtCore.Qt.ItemDataRole.FontRole:
            if index.row() == len(self._data) - 1:
                return QtGui.QFont.Weight.Bold

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])
    
    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if len(self._data) > 0:
            if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
                if len(self.hheader) > 0:
                    return self.hheader[section]
            if orientation == QtCore.Qt.Orientation.Vertical and role == QtCore.Qt.ItemDataRole.DisplayRole:
                if len(self.vheader) > 0:
                    return self.vheader[section]
        return super().headerData(section, orientation, role)
    
    def loadData(self, data, vheaders, hheaders):
        self.beginResetModel()
        self._data = data
        self.vheader = vheaders
        self.hheader = hheaders
        self.endResetModel()


