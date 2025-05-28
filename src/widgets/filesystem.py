from qtpy import (Qt, QtCore, QtWidgets, QtGui, Slot, Signal)

class FileSystem(QtWidgets.QTreeView):
    sigOpenFile = Signal(str)
    sigOpenNote = Signal(str)

    def __init__(self, rootpath: str, parent=None):
        super(FileSystem, self).__init__(parent)
        self._model: QtGui.QFileSystemModel = QtGui.QFileSystemModel()
        self.setModel(self._model)
        self.set_root_path(rootpath)
        self.setColumnWidth(0,150)
        self.setMinimumWidth(150)
        self.setSortingEnabled(True)
        self.hide_columns(range(1, self._model.columnCount()))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.action_delete = QtGui.QAction(QtGui.QIcon(":delete-bin2"),
                                           "Delete",
                                           self,
                                           triggered=self.deleteItem)

        self.action_open_externally = QtGui.QAction(QtGui.QIcon(":share-forward-2-line"),
                                                    "Open",
                                                    self,
                                                    triggered=self.openPathEntry)

        self.addAction(self.action_delete)
        self.addAction(self.action_open_externally)
        self.doubleClicked.connect(self.openPathEntry)

    def set_root_path(self, rootpath: str):
        index = self._model.setRootPath(rootpath)
        self.setRootIndex(index)

    def hide_columns(self, columns:list[int]):
        """Hide columns.
            Args:
                List of int
        """
        for column in columns:
            self.setColumnHidden(column,True)

    @Slot()
    def deleteItem(self):
        index = self.selectionModel().currentIndex()
        fileinfo = QtCore.QFileInfo(self._model.filePath(index))

        if fileinfo.isFile():
            name = fileinfo.fileName()
        else:
            name = "the folder"

        dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Question,
                                    "Delete ...",
                                    f"Are you sure you want to permanently remove {name}")
        dlg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Cancel|QtWidgets.QMessageBox.StandardButton.Ok)

        ret = dlg.exec()

        if ret == QtWidgets.QMessageBox.StandardButton.Ok:
            self._model.remove(index)

    @Slot()
    def openPathEntry(self):
        index = self.selectionModel().currentIndex()
        filepath = self._model.filePath(index)

        fileinfo = QtCore.QFileInfo(filepath)

        if fileinfo.suffix() == "html":
            self.sigOpenNote.emit(filepath)
        else:
            self.sigOpenFile.emit(filepath)
        

