# Standard library imports.
import logging

# Related third party imports.
from qtpy import (Qt, QtGui, QtCore, Signal, Slot)

# Local application/library specific imports.
from evidence.evidencemodel import (EvidenceModel, DocExplorerModel)
from evidence.evidencetable import DocTable
from evidence.evidence_dialogs import FilterDialog
from evidence.evidencetab_rightpane import DocInfoWidget
from evidence.evidencetab_leftpane import SignageFilter

from signage.signage_model import SignageTreeModel

from models.model import ProxyModel
from database.dbstructure import Document

from widgets.basetab import BaseTab
from widgets.treeview import TreeView
from widgets.waitingspinner import WaitingSpinner

from utilities.config import settings

from theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


class LoadWorkerSignals(QtCore.QObject):
    finished = Signal()
    error = Signal(object)
    result = Signal(object)
    progress = Signal(int)


class LoadDocWorker(QtCore.QRunnable):
    def __init__(self, model: EvidenceModel):
        super().__init__()
        self.model = model
        self.signals = LoadWorkerSignals()
    
    @Slot()
    def run(self):
        try:
            self.model.insertDocument()
        except Exception as e:
            self.signals.error.emit(e)
        finally:
            self.signals.finished.emit()


class EvidenceTab(BaseTab):
    sigOpenDocument = Signal(object, QtCore.QModelIndex)
    sigStatusUpdated = Signal()
    sigRefkeyUpdated = Signal()
    sigDocUploaded = Signal()
    sigCreateSignage = Signal(str, str)
    sigCreateChildSignage = Signal(int, str, str)

    def __init__(self, model: EvidenceModel, parent=None):
        super(EvidenceTab, self).__init__(parent)
        self.create_models(model=model)
        self.initUI()
        self.connectSignals()

        self.threadpool = QtCore.QThreadPool()

    def initUI(self):
        """Init the GUI"""
        self.setupLeftPane()
        self.setupCentralWidget()
        self.setupRightPane()
        self.setupToolbar()
        self.setupDialogs()
        self.createShortcuts()

        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.right_pane)
        self.splitter.setSizes([150, 500, 100])

    def setupDialogs(self):
        """Setup dialogs"""
        self.filter_dialog: FilterDialog = None
    
    def setupLeftPane(self):
        """Remove the Left Pane and the collapse button from the Toolbar"""
        self.doc_filter = TreeView(parent=self, border=False)
        self.doc_filter.setModel(self.doc_explorer_model.proxy_model)
        self.doc_filter.setRootIndex(self.doc_explorer_model.proxy_index)
        self.doc_filter.hide_columns(range(1, self.doc_explorer_model.columnCount()))
        self.doc_filter.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.doc_filter.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        # Tag filter tab
        # self.tag_filter = QtWidgets.QListView(self)

        self.left_pane.addTab(self.doc_filter, theme_icon_manager.get_icon(":node-tree"), "")
        # self.left_pane.addTab(self.tag_filter, theme_icon_manager.get_icon(":tags"), "")
    
    def setupCentralWidget(self):
        """Init Central Widget"""
        self.table = DocTable(model=self._model, proxy_model=self.doctable_proxy_model)

        for field in self._model.Fields.fields():
            if not field.visible:
                self.table.hideColumn(field.index)

        self.table.sortByColumn(self._model.Fields.Refkey.index, Qt.SortOrder.AscendingOrder)

        # Restore columns size
        self.restoreTableColumnWidth()

    def setupRightPane(self):
        """Setup the Right Pane"""
        self.doc_info_tab = DocInfoWidget(self._model, self)
        self.right_pane.addTab(self.doc_info_tab, "Info")
        self.right_pane.addTab(self.doc_info_tab.note, "Note")

    def setupToolbar(self):
        """Add custom button to the Toolbar"""
        self.load_file = QtGui.QAction(theme_icon_manager.get_icon(":folder_upload"), "Load file", self, triggered=self.handle_load_file)
        self.toolbar.insertAction(self.action_separator, self.load_file)

        self.detect_refkey = QtGui.QAction(theme_icon_manager.get_icon(":refkey"), "Detect refkey", self, triggered=self.table.autoRefKey)
        self.toolbar.insertAction(self.action_separator, self.detect_refkey)

        self.filtering = QtGui.QAction(theme_icon_manager.get_icon(":filter-line"), "Filter", self, triggered=self.setFilters)
        self.toolbar.insertAction(self.action_separator, self.filtering)

        self.reset_filtering = QtGui.QAction(theme_icon_manager.get_icon(":filter-off-line"),
                                             "Reset Filters",
                                             self,
                                             triggered=self.onResetFilters)
        self.toolbar.insertAction(self.action_separator, self.reset_filtering)

        self.action_create_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line"),
                                                   "Create Signage (Ctrl + R)",
                                                   self,
                                                   triggered = self.createSignage)
        self.toolbar.insertAction(self.action_separator, self.action_create_signage)

        self.action_create_child_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line-child"),
                                                   "Create Child Signage (Ctrl + N)",
                                                   self,
                                                   triggered = self.createChildSignage)
        self.toolbar.insertAction(self.action_separator, self.action_create_child_signage)
    
    def createShortcuts(self):
        self.shortcut_create_childsignage = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+N"),
                                                            self,
                                                            self.createChildSignage,
                                                            context=QtCore.Qt.ShortcutContext.WindowShortcut)

    def createRefKeyFilterPane(self, model: SignageTreeModel):
        self.request_filter_tab = SignageFilter(model=model)
        self.request_filter_tab.table.clicked.connect(self.onRequestFilterClicked)
        self.request_filter_tab.table.sortByColumn(model.Fields.Refkey.index, Qt.SortOrder.AscendingOrder)
        self.left_pane.insertTab(1, self.request_filter_tab, theme_icon_manager.get_icon(":request"), "")

    @Slot()
    def setFilters(self):
        if self.filter_dialog is None:
            self.filter_dialog = FilterDialog(self._model.cacheEvidenceStatus(),
                                              self)
            self.filter_dialog.accepted.connect(self.applyFilters)

            # Move the dialog below the button
            ph = self.toolbar.widgetForAction(self.filtering).geometry().height()
            pw = self.toolbar.widgetForAction(self.filtering).geometry().width()
            px = self.toolbar.widgetForAction(self.filtering).geometry().x()
            py = self.toolbar.widgetForAction(self.filtering).geometry().y()
            dw = self.filter_dialog.width()
            dh = self.filter_dialog.height()   
            self.filter_dialog.setGeometry(px + int(dw / 2), py + (ph * 2) + (dh * 2), dw, dh )

        self.filter_dialog.exec()

    @Slot()
    def applyFilters(self):
        self.doctable_proxy_model.setSatusFilter(self.filter_dialog.statusFilter(), self._model.Fields.Status.index)
        self.doctable_proxy_model.invalidateFilter()

    def create_models(self, model: EvidenceModel):
        self._model = model
        self.doctable_proxy_model = ProxyModel(self._model)
        self.doctable_proxy_model.setUserFilter('', self._model.visibleFields())
        self.doctable_proxy_model.setDynamicSortFilter(False)
        self.doc_explorer_model = DocExplorerModel()

    def connectSignals(self):
        self.table.selectionModel().selectionChanged.connect(self.onRowSelected)
        self.table.doubleClicked.connect(self.onTableDoubleClicked)
        self.table.sigOpenDocument.connect(self.onTableDoubleClicked)
        self.table.sigStatusUpdated.connect(self.sigStatusUpdated)
        self.table.sigResetFilters.connect(self.onResetFilters)
        self.doc_filter.selectionModel().selectionChanged.connect(self.onFolderFilterClicked)
        self.search_tool.textChanged.connect(self.searchfor)
        self._model.layoutChanged.connect(self.doctable_proxy_model.layoutChanged)
        self._model.layoutChanged.connect(self.doctable_proxy_model.invalidateFilter)
        self._model.layoutChanged.connect(lambda: self.doctable_proxy_model.setDynamicSortFilter(True))
        self.doc_info_tab.sigStatusUpdated.connect(self.sigStatusUpdated)
        self.doc_info_tab.sigRefkeyUpdated.connect(self.sigRefkeyUpdated)
    
    @Slot(QtCore.QModelIndex)
    def onTableDoubleClicked(self, index: QtCore.QModelIndex):
        sidx = self.doctable_proxy_model.mapToSource(index) # Source index
        r = sidx.row() #row

        doc = Document(refkey=sidx.sibling(r, self._model.Fields.Refkey.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       title=sidx.sibling(r, self._model.Fields.Title.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       subtitle=sidx.sibling(r, self._model.Fields.Subtitle.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       reference=sidx.sibling(r, self._model.Fields.Reference.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       status=sidx.sibling(r, self._model.Fields.Status.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       type=sidx.sibling(r, self._model.Fields.Type.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       note=sidx.sibling(r, self._model.Fields.Note.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       id=sidx.sibling(r, self._model.Fields.ID.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       fileid=sidx.sibling(r, self._model.Fields.FileID.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       workspace_id=sidx.sibling(r, self._model.Fields.Workspace.index).data(QtCore.Qt.ItemDataRole.DisplayRole),
                       signage_id=sidx.sibling(r, self._model.Fields.SignageID.index).data(QtCore.Qt.ItemDataRole.DisplayRole))

        doc.filepath = sidx.sibling(r, self._model.Fields.Filepath.index).data(QtCore.Qt.ItemDataRole.DisplayRole)

        # emit signals
        self.sigOpenDocument.emit(doc, sidx)

    @Slot()
    def searchfor(self):
        pattern = self.search_tool.text()
        self.doctable_proxy_model.setUserFilter(pattern,
                                                [self._model.Fields.Refkey.index,
                                                 self._model.Fields.Status.index,
                                                 self._model.Fields.Title.index,
                                                 self._model.Fields.Note.index,
                                                 self._model.Fields.Reference.index,
                                                 self._model.Fields.Subtitle.index,
                                                 self._model.Fields.Filepath.index])
        self.doctable_proxy_model.invalidateFilter()

    @Slot()
    def refresh(self):
        self._model.refresh()
        self.doc_explorer_model.refresh()
        self.doc_filter.setModel(self.doc_explorer_model.proxy_model)
        self.doc_filter.setRootIndex(self.doc_explorer_model.proxy_index)

    @Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def onRowSelected(self, selected: QtCore.QItemSelection, deseleted: QtCore.QItemSelection):
        if len(self.table.selectedRows()) == 1:
            self.source_index = self.doctable_proxy_model.mapToSource(self.table.selectionModel().currentIndex())
            self.doc_info_tab.mapper.setCurrentModelIndex(self.source_index)

    @Slot()
    def onFolderFilterClicked(self):
        try:
            selected_index = self.doc_filter.selectionModel().currentIndex()
        except Exception as e:
            logger.error(e)
        else:
            folderpath = self.doc_explorer_model.get_path(selected_index)
            self.doctable_proxy_model.setUserFilter(folderpath.as_posix(), [self._model.Fields.Filepath.index])
            self.doctable_proxy_model.invalidateFilter()
            self.table.updateAction()

    @Slot(QtCore.QModelIndex)
    def onRequestFilterClicked(self, index: QtCore.QModelIndex):
        """Filter the Evidence table on Request Refkey clicked"""
        if index.isValid():
            signage_refkey = index.sibling(index.row(), SignageTreeModel.Fields.Refkey.index).data(Qt.ItemDataRole.DisplayRole)
            self.doctable_proxy_model.setUserFilter(f"{signage_refkey}", [self._model.Fields.Refkey.index])
            self.doctable_proxy_model.invalidateFilter()

    @Slot(str)
    def filterWithRefkey(self, refkey: str):
        self.doctable_proxy_model.setUserFilter(f"{refkey}", [self._model.Fields.Refkey.index])
        self.doctable_proxy_model.invalidateFilter()

    @Slot() #TODO
    def handle_tag_explorer_selection(self, selected, deselected):
        """Filter docview from tag explorer filter pane"""
        # select from model the list of document associated to the tag selected
        # get in the model tagname, tagid, doclist
        selected_indexes = ...
        for i in selected.indexes():
            print(f'selected : {i.row()} - {i.data()}')
        for j in deselected.indexes():
            print(f'deselected : {j.row()} - {j.data()}')
        taglist = ...
        doclist = ...
        self._model.apply_filter('doc_id', doclist)

    @Slot()
    def createSignage(self):
        source = f'{{"application":"InspectorMate", "module":"Evidence"}}'
        self.sigCreateSignage.emit("", source)

    @Slot()
    def createChildSignage(self):
        index = self.table.selectionModel().currentIndex()

        if not index.isValid():
            return

        sidx = self.doctable_proxy_model.mapToSource(index)

        signage_id = sidx.sibling(sidx.row(), self._model.Fields.SignageID.index).data(QtCore.Qt.ItemDataRole.DisplayRole)

        try:
            signage_id = int(signage_id)
        except Exception as e:
            signage_id = -1

        title = sidx.sibling(sidx.row(), self._model.Fields.Title.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        uid = sidx.sibling(sidx.row(), self._model.Fields.ID.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        source = f'{{"application":"InspectorMate", "module":"Evidence", "item":"document", "item_title":"{title}", "item_id":"{uid}"}}'
        self.sigCreateChildSignage.emit(signage_id, "", source)

    @Slot()
    def handle_load_file(self):
        self.docloadspinner = WaitingSpinner(self, True, True, QtCore.Qt.WindowModality.WindowModal)
        self.docloadspinner.start()

        worker = LoadDocWorker(self._model)

        worker.signals.finished.connect(self.handleLoadEnded)
        self.threadpool.tryStart(worker)

    @Slot()
    def onResetFilters(self):
        """Reset Evidence Table Filters"""
        self.doctable_proxy_model.setUserFilter("", [self._model.Fields.Refkey.index])
        self.doctable_proxy_model.setSatusFilter([], self._model.Fields.Status.index)
        self.doctable_proxy_model.setTypeFilter([], self._model.Fields.Type.index)
        self.doctable_proxy_model.invalidateFilter()
        self.table.sortByColumn(self._model.Fields.Refkey.index, QtCore.Qt.SortOrder.AscendingOrder)

        self.search_tool.clear()

        if self.filter_dialog is not None:
            self.filter_dialog.resetFields()

    def handleLoadEnded(self):
        self.docloadspinner.stop()
        self.sigDocUploaded.emit()

    @Slot()
    def submitMapper(self) -> bool:
        if self._model.lastError().isValid():
            err = True
            logger.info(f"Utility pane mapper submitted: {err}")
            logger.error(f'Mapper failed to submit - {self._model.lastError().text()}')
        else:
            self._model.submitAll()
            self._model.refresh()
            err = False
        return err
    
    def restoreTableColumnWidth(self):
        """Restore table column width upon GUI initialization"""
        settings.beginGroup("evidence")
        for column in range(self._model.columnCount()):
            # if settings.contains(f"column-{column}"):
            self.table.setColumnWidth(column, settings.value(f"column-{column}", 100, int))
        settings.endGroup()

    def saveTableColumnWidth(self):
        """Save table column width upon closing"""
        settings.beginGroup("evidence")
        for column in range(self._model.columnCount()):
            settings.setValue(f"column-{column}", self.table.columnWidth(column))
        settings.endGroup()

    def closeEvent(self, a0):
        self.saveTableColumnWidth()
        self.submitMapper()
        return super().closeEvent(a0)
