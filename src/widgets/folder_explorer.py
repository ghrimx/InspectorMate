from qtpy import QtWidgets, QtGui, QtCore, Signal

class FolderExplorerModel(QtGui.QFileSystemModel):
    def __init__(self) -> None:
        super().__init__()
        self.setFilter(QtCore.QDir.Filter.AllDirs |
                             QtCore.QDir.Filter.NoDotAndDotDot)

    def hasChildren(self, index):
        file_info = self.fileInfo(index)
        _dir = QtCore.QDir(file_info.absoluteFilePath())
        return bool(_dir.entryList(self.filter()))

class FolderExplorer(QtWidgets.QWidget):
    rowClicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.model = FolderExplorerModel()

        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vbox)

        self.view = QtWidgets.QTreeView()
        self.view.setHeaderHidden(True)
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.view.setStyleSheet("""QTreeView { border: none; }""")
        vbox.addWidget(self.view)

        self.view.setModel(self.model)
        self.view.clicked.connect(self.onRowClicked)

    def setRootPath(self, path: str):
        idx = self.model.setRootPath(path)
        self.view.setRootIndex(idx)
        for i in range(1, self.model.columnCount()):
            self.view.hideColumn(i)

    def onRowClicked(self, index):
        if not index.isValid():
            return
        
        path = self.model.filePath(index)

        if not path:
            return

        self.rowClicked.emit(path) 
