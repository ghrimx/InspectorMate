import logging

from qtpy import (Qt, QtCore, QtWidgets, QtGui, Slot)

from signage.signagemodel import SignageTablelModel
from signage.signagedelegate import (ProgressBarDelegate, TitleDelegate, EvidenceColumnDelegate)
from models.model import ProxyModel
from delegates.delegate import (NoteColumnDelegate, ReadOnlyDelegate)

from widgets.treeview import TreeView

from db.database import AppDatabase
from db.dbstructure import Signage

from utilities import config as mconf

logger = logging.getLogger(__name__)


class SignageTable(TreeView):
    def __init__(self, model: SignageTablelModel, proxy_model: ProxyModel):
        super().__init__()

        self._model: SignageTablelModel = model
        self._proxy_model = proxy_model

        self.setModel(self._proxy_model)

        # Selection mode
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.createAction()
        self.setDelegate()
        self.setAutoScroll(False)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

    def createAction(self):
        self.action_delete_rows = QtGui.QAction(QtGui.QIcon(":delete-bin2"),
                                                "Delete",
                                                self,
                                                triggered=self.deleteRows)

        self.action_openLink = QtGui.QAction(QtGui.QIcon(":link-m"),
                                             "Open Link",
                                             self,
                                             triggered=self.openLink)

        self.status_menu = QtWidgets.QMenu("Status", self)
        for status in AppDatabase.cache_signage_status:
            self.status_menu.addAction(status)

        self.owner_menu = QtWidgets.QMenu("Owner", self)
        owners: list = mconf.settings.value("owners", [], "QStringList")
        for owner in owners:
            self.owner_menu.addAction(owner)

        self.status_menu.triggered.connect(self.setStatus)
        self.owner_menu.triggered.connect(self.setOwner)

        self.action_resetfilter = QtGui.QAction(QtGui.QIcon(":filter-off-line"),
                                                "Reset filters",
                                                self,
                                                triggered=self.resetFilters)

        self.selectionModel().selectionChanged.connect(self.updateAction)

        self.updateAction()

    def contextMenuEvent(self, event: QtGui.QMouseEvent):
        # Creating a menu object with the central widget as parent
        menu = QtWidgets.QMenu(self)
        menu.addMenu(self.status_menu)
        menu.addMenu(self.owner_menu)
        menu.addAction(self.action_delete_rows)
        menu.addAction(self.action_openLink)
        menu.addAction(self.action_resetfilter)
        menu.exec(QtGui.QCursor().pos())

    @Slot()
    def resetFilters(self):
        self.selectionModel().clearSelection()
        self._model.refresh()
        self._proxy_model.setUserFilter("", [self._model.Fields.RefKey.index])
        self._proxy_model.invalidateFilter()
        self.sortByColumn(self._model.Fields.RefKey.index, Qt.SortOrder.AscendingOrder)

    @Slot(QtGui.QAction)
    def setStatus(self, action: QtGui.QAction):
        status_int = AppDatabase.cache_signage_status.get(action.text())

        if status_int is not None:
            rows = self.selectedRows()
            self._model.updateStatus(rows, status_int)

    @Slot(QtGui.QAction)
    def setOwner(self, action: QtGui.QAction):
        owner = action.text()

        if owner != "":
            rows = self.selectedRows()
            self._model.updateOwner(rows, owner)

    def setDelegate(self):
        self.evidence_delegate = EvidenceColumnDelegate(self)
        self.setItemDelegateForColumn(self._model.Fields.Evidence.index, self.evidence_delegate)

        self.note_delegate = NoteColumnDelegate(self)
        self.setItemDelegateForColumn(self._model.Fields.Note.index, self.note_delegate)

        self.title_delegate = TitleDelegate(self._proxy_model, self)
        self.setItemDelegateForColumn(self._model.Fields.Title.index, self.title_delegate)

        self.delegate = ReadOnlyDelegate(self)
        self.setItemDelegate(self.delegate)

        self.progress_delegate = ProgressBarDelegate(self._proxy_model, self)
        self.setItemDelegateForColumn(self._model.Fields.EvidenceEOL.index, self.progress_delegate)

    def updateAction(self):
        if len(self.selectedRows()) == 1:
            self.action_delete_rows.setEnabled(True)
            self.owner_menu.setEnabled(True)
            self.status_menu.setEnabled(True)

            selected_row = self._proxy_model.mapToSource(self.selectionModel().currentIndex()).row()
            link = self._model.getLink(selected_row)
            if link != "":
                self.action_openLink.setEnabled(True)
            else:
                self.action_openLink.setEnabled(False)

        if len(self.selectedRows()) == 0:
            self.action_delete_rows.setEnabled(False)
            self.action_openLink.setEnabled(False)
            self.owner_menu.setEnabled(False)
            self.status_menu.setEnabled(False)

        if len(self.selectedRows()) > 1:
            self.action_delete_rows.setEnabled(True)
            self.action_openLink.setEnabled(False)
            self.owner_menu.setEnabled(True)
            self.status_menu.setEnabled(True)

    def proxy_model(self):
        return self._proxy_model

    def selectedSignage(self) -> Signage:
        selected_model_index: QtCore.QModelIndex = self._proxy_model.mapToSource(self.selectionModel().currentIndex())
        return self._model.querySignage(selected_model_index.row())

    def selectedProxyIndexes(self) -> list[QtCore.QModelIndex]:
        indexes = self.selectedIndexes()
        selected_indexes = []
        for index in indexes:
            selected_indexes.append(self._proxy_model.mapToSource(index))

        return selected_indexes

    def selectedRows(self):
        indexes = self.selectedProxyIndexes()
        rows = []
        row = -1
        for index in indexes:
            if row != index.row():
                row = index.row()
                rows.append(row)
        return rows

    @Slot()
    def deleteRows(self):
        indexes = self.selectedIndexes()
        selected_indexes = []
        for index in indexes:
            selected_indexes.append(self._proxy_model.mapToSource(index))
        self._model.deleteRows(selected_indexes)

    @Slot()
    def openLink(self):
        selected_row = self._proxy_model.mapToSource(self.selectionModel().currentIndex()).row()
        link = self._model.getLink(selected_row)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(link, QtCore.QUrl.ParsingMode.TolerantMode))
