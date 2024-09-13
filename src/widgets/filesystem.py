from qtpy import (Qt, QtWidgets, QtGui, Slot)

from db.database import AppDatabase
from utilities.utils import createFolder

class FileSystem(QtWidgets.QTreeView):
    def __init__(self, rootpath: str, parent=None):
        super(FileSystem, self).__init__()
        self._model: QtGui.QFileSystemModel = QtGui.QFileSystemModel()
        self.setModel(self._model)
        self.set_root_path(rootpath)
        self.setColumnWidth(0,150)
        self.setMinimumWidth(150)
        self.setSortingEnabled(True)
        self.hide_columns(range(1, self._model.columnCount()))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.action_addfile = QtGui.QAction(QtGui.QIcon(":file_add"),
                                            "Add file",
                                            self,
                                            triggered=self.addFile)

        self.action_delete = QtGui.QAction(QtGui.QIcon(":delete-bin2"),
                                           "Delete",
                                           self,
                                           triggered=self.deleteItem)
        
        self.addAction(self.action_addfile)
        self.addAction(self.action_delete)

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
        current_index = self.selectionModel().currentIndex()
        self._model.remove(current_index)

    @Slot()
    def addFile(self, parent=None):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(parent,
                                                            caption="Create a note",
                                                            directory=AppDatabase.active_workspace.notebook_path,
                                                            filter="Text files (*.phv)")
        if filename:
            with open(filename, "w") as f:
                text = ""
                f.write(text)
                f.close()
