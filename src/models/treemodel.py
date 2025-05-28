from qtpy import QtCore


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
            self.dataChanged.emit(index, index,
                                  [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole])

        return result

    def setHeaderData(self, section: int, orientation: QtCore.Qt.Orientation, value,
                      role: int = None) -> bool:
        if role != QtCore.Qt.ItemDataRole.EditRole or orientation != QtCore.Qt.Orientation.Horizontal:
            return False

        result: bool = self.root_item.setData(section, value)

        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result