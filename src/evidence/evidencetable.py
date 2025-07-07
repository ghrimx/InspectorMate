import logging
import base64
from pathlib import Path

from qtpy import (QtWidgets, Qt, QtCore, QtGui, Slot, Signal)

from evidence.evidencemodel import EvidenceModel
from models.model import ProxyModel
from database.dbstructure import Document

from widgets.treeview import TreeView
from delegates.delegate import (NoteColumnDelegate, ReadOnlyDelegate)

from utilities.utils import (open_file, queryFileNameByID)

from theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


class DocTable(TreeView):
    sigOpenDocument = Signal(QtCore.QModelIndex)
    sigStatusUpdated = Signal()
    sigResetFilters = Signal()
    sigDeleteRows = Signal()

    def __init__(self, model: EvidenceModel, proxy_model: ProxyModel):
        super().__init__()

        self._model = model
        self._proxy_model = proxy_model

        self.setModel(self._proxy_model)
        self.setDelegate(self._proxy_model)

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setAutoScroll(False)

        self.createAction()

    def createAction(self):
        self.action_delete_rows = QtGui.QAction(theme_icon_manager.get_icon(":delete-bin2"),
                                                "Delete",
                                                self,
                                                triggered=self.deleteRows)
        self.action_open = QtGui.QAction(theme_icon_manager.get_icon(":file-4-line"),
                                         "Open",
                                         self,
                                         triggered=self.openFile)
        self.action_open_externally = QtGui.QAction(theme_icon_manager.get_icon(":share-forward-2-line"),
                                                    "Open with...",
                                                    self,
                                                    triggered=self.openWith)
        self.action_open_folder = QtGui.QAction(theme_icon_manager.get_icon(":folder-open-line"),
                                                "Open folder",
                                                self,
                                                triggered=self.openFolder)
        self.action_cite = QtGui.QAction(theme_icon_manager.get_icon(":double-quotes"),
                                         "Cite",
                                         self,
                                         triggered=self.cite)
        self.shortcut_action_cite = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+C"), self, self.cite, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.action_cite.setShortcut(QtGui.QKeySequence("Ctrl+Alt+C"))

        self.action_auto_refkey = QtGui.QAction(theme_icon_manager.get_icon(":refkey"),
                                                "auto RefKey",
                                                self,
                                                triggered=self.autoRefKey)
        self.action_locate = QtGui.QAction(theme_icon_manager.get_icon(":search-line"),
                                           "Locate",
                                           self,
                                           triggered=self.locate)
        self.status_menu = QtWidgets.QMenu("Status", self)

        for status in self._model.cacheEvidenceStatus().values():
            self.status_menu.addAction(status.name)

        self.status_menu.triggered.connect(self.setStatus)

        self.action_resetfilter = QtGui.QAction(theme_icon_manager.get_icon(":filter-off-line"),
                                                "Reset filters",
                                                self,
                                                triggered=self.sigResetFilters)

        self.action_setRefKey = QtGui.QAction(theme_icon_manager.get_icon(":key-2-line"),
                                              "Set RefKey",
                                              self,
                                              triggered=self.setRefKey)

        self.selectionModel().selectionChanged.connect(self.updateAction)
        self.updateAction()
        self.customContextMenuRequested.connect(self.contextMenuEvent)

    def contextMenuEvent(self, event: QtGui.QMouseEvent):
        # Creating a menu object with the central widget as parent
        menu = QtWidgets.QMenu(self)

        menu.addMenu(self.status_menu)
        menu.addAction(self.action_delete_rows)
        menu.addAction(self.action_open)
        menu.addAction(self.action_open_externally)
        menu.addAction(self.action_open_folder)
        menu.addAction(self.action_cite)
        menu.addAction(self.action_auto_refkey)
        menu.addAction(self.action_setRefKey)
        menu.addAction(self.action_locate)
        menu.addAction(self.action_resetfilter)

        menu.exec(QtGui.QCursor().pos())

    def proxy_model(self) -> ProxyModel:
        return self._proxy_model

    def model(self) -> EvidenceModel:
        return self._model

    def document(self) -> Document:
        """Return the dataclass of the document currently selected"""
        selected_model_index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        return self._model.document(selected_model_index)

    def setDelegate(self, model: EvidenceModel):
        self.delegate = ReadOnlyDelegate(self)
        self.setItemDelegate(self.delegate)

        self.note_delegate = NoteColumnDelegate(self)
        self.setItemDelegateForColumn(self._model.Fields.Note.index, self.note_delegate)

        self.title_delegate = TitleColumnDelegate(self._proxy_model, self)
        self.setItemDelegateForColumn(self._model.Fields.Title.index, self.title_delegate)

    def selectedProxyIndexes(self) -> list[QtCore.QModelIndex]:
        indexes = self.selectedIndexes()
        selected_indexes = []
        for index in indexes:
            selected_indexes.append(self._proxy_model.mapToSource(index))

        return selected_indexes

    def selectedRows(self) -> list:
        indexes = self.selectedProxyIndexes()
        rows = []
        row = -1
        for index in indexes:
            if row != index.row():
                row = index.row()
                rows.append(row)
        return rows

    def updateAction(self):
        if len(self.selectedRows()) == 1:
            self.action_open.setEnabled(True)
            self.action_open_externally.setEnabled(True)
            self.action_open_folder.setEnabled(True)
            self.action_cite.setEnabled(True)
            self.action_delete_rows.setEnabled(True)
            self.action_auto_refkey.setEnabled(True)
            self.action_setRefKey.setEnabled(True)
            self.action_locate.setEnabled(True)
            self.status_menu.setEnabled(True)

        if len(self.selectedRows()) == 0:
            self.action_open.setEnabled(False)
            self.action_open_externally.setEnabled(False)
            self.action_open_folder.setEnabled(False)
            self.action_cite.setEnabled(False)
            self.action_delete_rows.setEnabled(False)
            self.action_auto_refkey.setEnabled(False)
            self.action_setRefKey.setEnabled(False)
            self.action_locate.setEnabled(False)
            self.status_menu.setEnabled(False)

        if len(self.selectedRows()) > 1:
            self.action_open.setEnabled(False)
            self.action_open_externally.setEnabled(False)
            self.action_open_folder.setEnabled(False)
            self.action_cite.setEnabled(False)
            self.action_delete_rows.setEnabled(True)
            self.action_auto_refkey.setEnabled(True)
            self.action_setRefKey.setEnabled(True)
            self.action_locate.setEnabled(False)
            self.status_menu.setEnabled(True)

    @Slot(QtGui.QAction)
    def setStatus(self, action: QtGui.QAction):
        status = self._model.cacheEvidenceStatus().get(action.text())

        if status is not None:
            rows = self.selectedRows()
            r = self._model.updateStatus(rows, status.uid)

            if r:
                self.sigStatusUpdated.emit()

    @Slot()
    def setRefKey(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Update refKey", "New refKey:")
        if ok and text != "":
            self._model.updateRefKey(self.selectedRows(), text)

    @Slot()
    def cite(self):
        index = self.selectionModel().currentIndex()
        refkey = index.sibling(index.row(), self._model.Fields.Refkey.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        title = index.sibling(index.row(), self._model.Fields.Title.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        subtitle = index.sibling(index.row(), self._model.Fields.Subtitle.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        reference = index.sibling(index.row(), self._model.Fields.Reference.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        
        refkey = "refkey: " + refkey if refkey != "" else None
        title = f'"{title}"'
        citation = "; ".join(x for x in [refkey, title, subtitle, reference] if x)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(f"[{citation}]")

    @Slot()
    def deleteRows(self):
        msgbox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Question,
                              "Delete document",
                              "Are you sure you want to delete this document",
                              QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No,
                              self)
        confirm = msgbox.exec()
        
        if not confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            return

        indexes = self.selectedIndexes()
        selected_indexes = []
        for index in indexes:
            selected_indexes.append(self._proxy_model.mapToSource(index))
        self._model.deleteRows(selected_indexes)

    @Slot()
    def openFile(self):
        idx = self.selectionModel().currentIndex()
        self.sigOpenDocument.emit(idx)

    @Slot()
    def openWith(self):
        index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        filepath = index.sibling(index.row(), self._model.Fields.Filepath.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        open_file(filepath)

    @Slot()
    def openFolder(self):
        index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        filepath = index.sibling(index.row(), self._model.Fields.Filepath.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        fpath = Path(filepath)

        if fpath.exists():
            open_file(fpath.parent)

    @Slot()
    def autoRefKey(self):
        self._model.autoRefKey(self.selectedRows())

    @Slot()
    def locate(self):
        index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        fileid = index.sibling(index.row(), self._model.Fields.FileID.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        filepath = queryFileNameByID(fileid)

        if Path(filepath).exists():
            folder = Path(filepath).parent.as_posix()
        else:
            folder = self._model.activeWorkspace().rootpath

        filepath = QtWidgets.QFileDialog.getOpenFileName(caption='Locate the file...', directory=folder)

        if filepath[0] != "":
            self._model.updateFilePath(index, filepath[0])


class TitleColumnDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, model: ProxyModel, parent=None):
        super().__init__(parent=parent)
        self._model = model
        self.cache_icon = {}
        self.icon_provider = QtWidgets.QFileIconProvider()

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)

        title = index.data(Qt.ItemDataRole.DisplayRole)
        file_path = index.sibling(index.row(), self._model.sourceModel().Fields.Filepath.index).data(Qt.ItemDataRole.DisplayRole)

        if file_path not in self.cache_icon:
            icon = self.icon_provider.icon(QtCore.QFileInfo(file_path)) 
            self.cache_icon[file_path] = icon
        else:
            icon = self.cache_icon[file_path]

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = icon
        option.text = title

    def createEditor(self, *args):
        """ Make editor read-only """
        return


class ExistColumnDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        value = index.data(Qt.ItemDataRole.DisplayRole)
        if value == 1:
            ico = ':active-icon'
        else:
            ico = ':inactive-icon'

        if (not value == ""):
            option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
            option.icon = theme_icon_manager.get_icon(ico)
            option.text = ""

    def createEditor(self, *args):
        """ Make editor read-only """
        return
