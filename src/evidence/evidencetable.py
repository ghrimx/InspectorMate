import logging
import base64
from pathlib import Path

from qtpy import (QtWidgets, Qt, QtCore, QtGui, Slot, Signal)

from evidence.evidencemodel import DocTableModel
from models.model import ProxyModel
from db.dbstructure import Document

from widgets.treeview import TreeView
from delegates.delegate import (NoteColumnDelegate, ReadOnlyDelegate)

from utilities.utils import (open_file, queryFileNameByID)

from db.database import AppDatabase

logger = logging.getLogger(__name__)


class DocTable(TreeView):
    sig_open_document = Signal()

    def __init__(self, model: DocTableModel, proxy_model: ProxyModel):
        super().__init__()

        self._model = model
        self._proxy_model = proxy_model

        self.setModel(self._proxy_model)
        self.setDelegate(self._proxy_model)

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.createAction()

    def createAction(self):
        self.action_delete_rows = QtGui.QAction(QtGui.QIcon(":delete-bin2"),
                                                "Delete",
                                                self,
                                                triggered=self.deleteRows)
        self.action_open_externally = QtGui.QAction(QtGui.QIcon(":share-forward-2-line"),
                                                    "Open externally",
                                                    self,
                                                    triggered=self.openExternally)
        self.action_open_folder = QtGui.QAction(QtGui.QIcon(":folder-open-line"),
                                                "Open folder",
                                                self,
                                                triggered=self.openFolder)
        self.action_cite = QtGui.QAction(QtGui.QIcon(":double-quotes"),
                                         "Cite",
                                         self,
                                         triggered=self.cite)
        self.shortcut_action_cite = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+C"), self, self.cite, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.action_cite.setShortcut(QtGui.QKeySequence("Ctrl+Alt+C"))

        self.action_auto_refkey = QtGui.QAction(QtGui.QIcon(":refkey"),
                                                "auto RefKey",
                                                self,
                                                triggered=self.autoRefKey)
        self.action_locate = QtGui.QAction(QtGui.QIcon(":search-line"),
                                           "Locate",
                                           self,
                                           triggered=self.locate)
        self.status_menu = QtWidgets.QMenu("Status", self)
        for status in AppDatabase.cache_doc_status:
            self.status_menu.addAction(status)

        self.status_menu.triggered.connect(self.setStatus)

        self.action_resetfilter = QtGui.QAction(QtGui.QIcon(":filter-off-line"),
                                                "Reset filters",
                                                self,
                                                triggered=self.resetFilters)

        self.action_setRefKey = QtGui.QAction(QtGui.QIcon(":key-2-line"),
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
        menu.addAction(self.action_delete_rows)
        menu.addAction(self.action_open_externally)
        menu.addAction(self.action_open_folder)
        menu.addAction(self.action_cite)
        menu.addAction(self.action_auto_refkey)
        menu.addAction(self.action_setRefKey)
        menu.addAction(self.action_locate)
        menu.addAction(self.action_resetfilter)

        menu.exec(QtGui.QCursor().pos())

    def proxy_model(self):
        return self._proxy_model

    def model(self):
        return self._model

    def document(self) -> Document:
        selected_model_index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        return self._model.document(selected_model_index)

    def setDelegate(self, model: DocTableModel):
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
            self.action_open_externally.setEnabled(True)
            self.action_open_folder.setEnabled(True)
            self.action_cite.setEnabled(True)
            self.action_delete_rows.setEnabled(True)
            self.action_auto_refkey.setEnabled(True)
            self.action_setRefKey.setEnabled(True)
            self.action_locate.setEnabled(True)
            self.status_menu.setEnabled(True)

        if len(self.selectedRows()) == 0:
            self.action_open_externally.setEnabled(False)
            self.action_open_folder.setEnabled(False)
            self.action_cite.setEnabled(False)
            self.action_delete_rows.setEnabled(False)
            self.action_auto_refkey.setEnabled(False)
            self.action_setRefKey.setEnabled(False)
            self.action_locate.setEnabled(False)
            self.status_menu.setEnabled(False)

        if len(self.selectedRows()) > 1:
            self.action_open_externally.setEnabled(False)
            self.action_open_folder.setEnabled(False)
            self.action_cite.setEnabled(False)
            self.action_delete_rows.setEnabled(True)
            self.action_auto_refkey.setEnabled(True)
            self.action_setRefKey.setEnabled(True)
            self.action_locate.setEnabled(False)
            self.status_menu.setEnabled(True)

    # Slots
    @Slot()
    def resetFilters(self):
        self.selectionModel().clearSelection()
        self._model.refresh()
        self._proxy_model.setUserFilter("", [self._model.Fields.RefKey.index])
        self._proxy_model.invalidateFilter()
        self.sortByColumn(self._model.Fields.RefKey.index, Qt.SortOrder.AscendingOrder)

    @Slot(QtGui.QAction)
    def setStatus(self, action: QtGui.QAction):
        status_int = AppDatabase.cache_doc_status.get(action.text())

        if status_int is not None:
            rows = self.selectedRows()
            self._model.updateStatus(rows, status_int)

    @Slot()
    def setRefKey(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Update refKey", "New refKey:")
        if ok and text != "":
            self._model.updateRefKey(self.selectedRows(), text)

    @Slot()
    def cite(self):
        doc = self.document()
        refkey = "refkey: " + doc.refKey if doc.refKey != "" else None
        title = f'"{doc.title}"'
        citation = "; ".join(x for x in [refkey, title, doc.subtitle, doc.reference] if x)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(f"[{citation}]")

    @Slot()
    def deleteRows(self):
        indexes = self.selectedIndexes()
        selected_indexes = []
        for index in indexes:
            selected_indexes.append(self._proxy_model.mapToSource(index))
        self._model.deleteRows(selected_indexes)

    @Slot()
    def openExternally(self):
        selected_index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())

        doc = self._model.document(selected_index)
        open_file(doc.filepath)

    @Slot()
    def openFolder(self):
        selected_index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        doc = self._model.document(selected_index)
        open_file(doc.folderpath())

    @Slot()
    def autoRefKey(self):
        self._model.autoRefKey(self.selectedRows())

    @Slot()
    def locate(self):
        row_idx: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        fileid = self._model.data(self._model.index(row_idx.row(), self._model.Fields.FileID.index), Qt.ItemDataRole.DisplayRole)
        filepath = queryFileNameByID(fileid)

        if Path(filepath).exists():
            folder = Path(filepath).parent.as_posix()
        else:
            folder = AppDatabase.active_workspace.rootpath

        filepath = QtWidgets.QFileDialog.getOpenFileName(caption='Locate the file...', directory=folder)

        if filepath[0] != "":
            self._model.updateFilePath(row_idx.row(), filepath[0])


class TitleColumnDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, model: ProxyModel, parent=None):
        super().__init__(parent=parent)
        self._model = model

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)

        title = index.data(Qt.ItemDataRole.DisplayRole)
        doc_type_idx = self._model.index(index.row(), self._model.sourceModel().Fields.Type.index)
        icon_binary: str = doc_type_idx.data()
        pix = QtGui.QPixmap()

        if icon_binary is not None:
            try:
                icon_bytearray = base64.b64decode(icon_binary)
            except UnicodeError:
                logger.error('Cannot decode string to bytes')
            else:
                pix.loadFromData(icon_bytearray)

        doc_type_icon = QtGui.QIcon(pix)

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = doc_type_icon
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
            option.icon = QtGui.QIcon(ico)
            option.text = ""

    def createEditor(self, *args):
        """ Make editor read-only """
        return
