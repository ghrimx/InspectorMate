# Standard library imports.
import logging
from datetime import datetime

# Related third party imports.
from qtpy import (QtCore, QtWidgets, QtGui, Qt, Slot, Signal)

# Local application/library specific imports.
from signage.signage_model import SignageTreeModel, SignageProxyModel
from signage.signage_treeview import (SignageTreeView, TitleDelegate, TypeDelegate,
                                      StatusDelegate, EvidenceDelegate, PublicNoteDelegate,
                                      PrivateNoteDelegate, ProgressBarDelegate)
from signage.signage_rightpane_widgets import SignageInfoWidget
from signage.signage_dialogs import CreateDialog, FilterDialog, ExportDialog, ImportDialog

from widgets.basetab import BaseTab
from pyqtspinner import WaitingSpinner

from utilities.config import settings
from utilities.decorators import status_signal

from qt_theme_manager import theme_icon_manager



logger = logging.getLogger(__name__)


class LoadWorkerSignals(QtCore.QObject):
    finished = Signal(bool,str)
    error = Signal()
    result = Signal()
    progress = Signal(int)


class OneNoteWorker(QtCore.QRunnable):
    def __init__(self, model: SignageTreeModel):
        super().__init__()
        self.model = model
        self.signals = LoadWorkerSignals()
    
    @Slot()
    def run(self):
        try:
            ok, msg = self.model.loadFromOnenote()
        except Exception as e:
            self.signals.error.emit()
        finally:
            self.signals.finished.emit(ok, msg)

class DocxWorker(QtCore.QRunnable):
    def __init__(self, model: SignageTreeModel):
        super().__init__()
        self.model = model
        self.signals = LoadWorkerSignals()
    
    @Slot()
    def run(self):
        try:
            ok, msg = self.model.loadFromDocx()
        except Exception as e:
            self.signals.error.emit()
        finally:
            self.signals.finished.emit(ok, msg)


class SignageTab(BaseTab):
    sigSignageTreemodelChanged = Signal()
    sigSignageDoubleClicked = Signal(str)

    def __init__(self, model: SignageTreeModel, parent=None):
        super(SignageTab, self).__init__(parent)
        self._model = model
        self.initUI()
        self.connectSignals()

        self.threadpool = QtCore.QThreadPool()

    def moduleName(self) -> str:
        """Return the name of the module"""
        return "Signage"
    
    def signageSource(self) -> str:
        return '{"application":"InspectorMate", "module":"Signage"}'

    def initUI(self):
        """Init the GUI"""
        self.setupCentralWidget()
        self.setupToolbar()
        self.setupLeftPane()
        self.setupRightPane()
        self.setupDialogs()
        self.createShortcuts()

        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.right_pane)
        self.splitter.setSizes([0, 800, 100])

    def setupCentralWidget(self):
        """Init Central Widget"""
        self.table = SignageTreeView(self._model.cacheSignageStatus(), self)
        self.proxy_model = SignageProxyModel(self._model)
        self.proxy_model.setDynamicSortFilter(False)
        self.table.setModel(self.proxy_model)
        self.table.setUniformRowHeights(True)
        self.table.sortByColumn(self._model.Fields.ID.index, QtCore.Qt.SortOrder.AscendingOrder)
        self.table.setAutoScroll(False)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)

        # Hide columns
        for field in self._model.Fields.fields():
            if not field.visible:
                self.table.hideColumn(field.index)

        # Delegate
        type_delegate = TypeDelegate(self._model.cacheSignageType(), self)
        self.table.setItemDelegateForColumn(self._model.Fields.Type.index, type_delegate)

        title_delegate = TitleDelegate(self._model.cacheSignageType(), self._model.Fields.Type.index, self.table)
        self.table.setItemDelegateForColumn(self._model.Fields.Title.index, title_delegate)

        status_delegate = StatusDelegate(self._model.cacheSignageStatus(), self._model.Fields.Status.index, self)
        self.table.setItemDelegate(status_delegate)

        privatenote_delegate = PrivateNoteDelegate(self.table)
        self.table.setItemDelegateForColumn(self._model.Fields.Note.index, privatenote_delegate)

        publicnote_delegate = PublicNoteDelegate(self.table)
        self.table.setItemDelegateForColumn(self._model.Fields.PublicNote.index, publicnote_delegate)

        evidence_delegate = EvidenceDelegate(self.table)
        self.table.setItemDelegateForColumn(self._model.Fields.Evidence.index, evidence_delegate)

        progressbar_delegate = ProgressBarDelegate(self._model.Fields.Evidence.index)
        self.table.setItemDelegateForColumn(self._model.Fields.EvidenceEOL.index, progressbar_delegate)

        # Restore columns size
        self.restoreTableColumnWidth()

    def setupToolbar(self):
        """Add custom button to the Toolbar"""
        self.action_create_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line"),
                                                   "Create Signage (Ctrl + R)",
                                                   self,
                                                   triggered = lambda: self.createSignage(source=self.signageSource()))
        self.toolbar.insertAction(self.action_separator, self.action_create_signage)

        self.action_create_child_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line-child"),
                                                         "Create Child Signage (Ctrl + H)",
                                                         self,
                                                         triggered = lambda: self.createChildSignage(source=self.signageSource()))
        self.toolbar.insertAction(self.action_separator, self.action_create_child_signage)

        self.action_delete_signage = QtGui.QAction(theme_icon_manager.get_icon(":delete-bin2"),
                                                   "Delete Signage",
                                                   self,
                                                   triggered = self.deleteRow)
        self.toolbar.insertAction(self.action_separator, self.action_delete_signage)

        separator = self.toolbar.addSeparator()
        self.toolbar.insertAction(self.action_separator, separator)

        self.filtering = QtGui.QAction(theme_icon_manager.get_icon(":filter-line"),
                                       "Filters",
                                       self,
                                       triggered=self.setFilters)
        self.toolbar.insertAction(self.action_separator, self.filtering)

        self.reset_filtering = QtGui.QAction(theme_icon_manager.get_icon(":filter-off-line"),
                                             "Reset Filters",
                                             self,
                                             triggered=self.onResetFilters)
        self.toolbar.insertAction(self.action_separator, self.reset_filtering)

        self.sort_by_creation_order = QtGui.QAction(theme_icon_manager.get_icon(":sort-number-asc"),
                                                    "Sort by Creation Order",
                                                    self,
                                                    triggered=self.onSortByCreationOrder)
        self.toolbar.insertAction(self.action_separator, self.sort_by_creation_order)

        self.action_expandAll = QtGui.QAction(theme_icon_manager.get_icon(":expand-vertical-line"),
                                                "Expand All",
                                                self,
                                                triggered=self.table.expandAll)
        self.toolbar.insertAction(self.action_separator, self.action_expandAll)
        
        self.action_collapseAll = QtGui.QAction(theme_icon_manager.get_icon(":collapse-vertical-line"),
                                                "Collapse All",
                                                self,
                                                triggered=self.table.collapseAll)
        self.toolbar.insertAction(self.action_separator, self.action_collapseAll)

        action_load_onenote = QtGui.QAction(theme_icon_manager.get_icon(":onenote"), "OneNote connector", self, triggered=self.loadFromOnenote)
        action_import_connector = QtGui.QAction(theme_icon_manager.get_icon(":file-text-line"), "Docx connector", self, triggered=self.importFromConnector)

        connector_menu_btn = QtWidgets.QToolButton(self)
        connector_menu_btn.setIcon(theme_icon_manager.get_icon(':links-line'))
        connector_menu_btn.setText("Import from Connector")
        connector_menu_btn.setToolTip("Import from Connector")
        connector_menu_btn.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        connector_menu_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        connector_menu = QtWidgets.QMenu()
        connector_menu.addAction(action_load_onenote)
        connector_menu.addAction(action_import_connector)
        connector_menu_btn.setMenu(connector_menu)
        self.toolbar.insertWidget(self.action_separator, connector_menu_btn)
    
    def createShortcuts(self):
        self.shortcut_create_childsignage = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+H"),
                                                            self,
                                                            lambda: self.createChildSignage(source=self.signageSource()),
                                                            context=QtCore.Qt.ShortcutContext.WindowShortcut)

    def setupLeftPane(self):
        """Remove the Left Pane and the collapse button from the Toolbar"""
        self.left_pane.hide()
        self.toolbar.removeAction(self.fold_left_pane) # Not needed in signage tab

    def setupRightPane(self):
        """Setup the Right Pane"""
        self.info_tab = SignageInfoWidget(self._model.cacheSignageStatus(), self._model.cacheSignageType())
        self.info_tab.setupMapper(self._model)
        self.right_pane.addTab(self.info_tab, "Info")
        self.right_pane.addTab(self.info_tab.note, theme_icon_manager.get_icon(':lock-2'), "Private Note")
        self.right_pane.addTab(self.info_tab.public_note, theme_icon_manager.get_icon(':glasses-2'), "Public Note")

    def setupDialogs(self):
        """Setup dialogs"""
        self.signage_dialog: CreateDialog = None
        self.filter_dialog: FilterDialog = None
        self.export_dialog: ExportDialog = None
        self.import_dialog: ImportDialog = None

    def connectSignals(self):
        """Connect signals"""

        # Table signals
        self.table.selectionModel().currentRowChanged.connect(self.onTableRowChanged)
        self.table.signals.resetFilters.connect(self.onResetFilters)
        self.table.signals.delete.connect(self.deleteRow)
        self.table.signals.updateStatus.connect(self.onUpdateStatusTriggered)
        self.table.signals.updateOwner.connect(self.onUpdateOwnerTriggered)
        self.table.doubleClicked.connect(self.onTableDoubleClicked)

        # Search tool signals
        self.search_tool.textChanged.connect(self.searchfor)

        # Info Tab signals
        self.info_tab.signals.updateTitle.connect(self.onUpdateTitleTriggered)
        self.info_tab.signals.updateStatus.connect(self.onUpdateStatusTriggered)
        self.info_tab.signals.updateOwner.connect(self.onUpdateOwnerTriggered)
        self.info_tab.signals.updateRefkey.connect(self.onUpdateRefkeyTriggered)
        self.info_tab.signals.updateType.connect(self.onUpdateTypeTriggered)
        self.info_tab.signals.updatePrivateNote.connect(self.onUpdatePrivateNoteTriggered)
        self.info_tab.signals.updatePublicNote.connect(self.onUpdatePublicNoteTriggered)

    @Slot(QtCore.QModelIndex, QtCore.QModelIndex)
    def onTableRowChanged(self, currentIndex: QtCore.QModelIndex, previousIndex: QtCore.QModelIndex):
        """Map proxy model indexes to source model indexes"""
        _currentIndex = self.proxy_model.mapToSource(currentIndex) 
        _previousIndex = self.proxy_model.mapToSource(previousIndex)
        self.info_tab.updatePanelFields(_currentIndex, _previousIndex)

    @Slot(QtCore.QModelIndex)
    def onTableDoubleClicked(self, index: QtCore.QModelIndex):
        refkey = index.sibling(index.row(), self._model.Fields.Refkey.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        self.sigSignageDoubleClicked.emit(refkey)
    
    def restoreTableColumnWidth(self):
        """Restore table column width upon GUI initialization"""
        settings.beginGroup("signage")
        for column in range(self._model.columnCount()):
            # if settings.contains(f"column-{column}"):
            self.table.setColumnWidth(column, settings.value(f"column-{column}", 100, int))
        settings.endGroup()

    def saveTableColumnWidth(self):
        """Save table column width upon closing"""
        settings.beginGroup("signage")
        for column in range(self._model.columnCount()):
            settings.setValue(f"column-{column}", self.table.columnWidth(column))
        settings.endGroup()

    @Slot(str, str)
    def createSignage(self, title: str = "", source: str = ""):
        """Create Parent Signage"""
        if not self.openSignageDialog(title):
            return
        
        # Get signage from the dialog
        signage = self.signage_dialog.getNewSignage()
        signage.source = source
        signage.creation_datetime = datetime.now().strftime("%Y-%m-%d")

        # source:
        # '{"application":"InspectorMate", "module":"Notebook", "item":"note", "item_title":"1.3 Line Listing session", "item_id":"1.3 Line Listing session.html", "position":"hanchor123"}'
        # '{"application":"InspectorMate", "module":"Evidence", "item":"doc", "item_title":"document[:25]", "item_id":"6", "position":"page2"}'
        # '{"application":"InspectorMate", "module":"Signage", "item":"Request", "item_title":"signage[:25]", "item_id":"2", "position":"child2"}'
        # '{"application":"InspectorMate", "module":"ImportFromOneNote", "item":"Page", "item_title":"title[:25]", "item_id":"id", "position":"link"}'
        # '{"application":"InspectorMate", "module":"ImportFromExcel", "item":"xlsx", "item_title":"filename", "item_id":"fileid", "position":"link to file"}'

        # Insert signage into the database and into the model
        ok, err = self._model.insertSignage(signage=signage, parent=self.table.rootIndex())

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error saving signage",
                                        f"Signage: {signage} - Error:{err}",
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return

        if signage.type == 0:
            self.sigSignageTreemodelChanged.emit()
        
        status_signal.status_message.emit("Signage created!", 10000)
        return True

    @Slot(int, str, str)
    def createChildSignage(self, parent_id: int = None, title: str = "", source: str = ""):
        """Create Child Signage"""
        if not self.openSignageDialog(title):
            return
        
        logger.debug(f"parent_id={parent_id}, source={source}")

        treemodel_index = None

        if parent_id is None: # Triggered from signage treeview
            index = self.table.selectionModel().currentIndex()
            treemodel_index = self.proxy_model.mapToSource(index)
            parent_id = index.sibling(index.row(), self._model.Fields.ID.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        elif parent_id > 0:
            treemodel_index = self._model.getTreeModelIndexById(parent_id)

        if treemodel_index is None:
            logger.debug("treemodel_index is None")
            treemodel_index = self._model.parent()
            parent_id = None
 
        signage = self.signage_dialog.getNewSignage()
        signage.parentID = parent_id
        signage.source = source
        
        ok, err = self._model.insertSignage(signage=signage, parent=treemodel_index.sibling(treemodel_index.row(), 0))

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error saving child signage",
                                        f"Signage: {signage}\nError: {err}",
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return
        
        if signage.type == 0:
            self.sigSignageTreemodelChanged.emit()
        
        # Re-apply filters to refresh filtered view
        self.applyFilters()

        return True

    @Slot()
    def openSignageDialog(self, title):
        """
            Open the signage dialog
            data: [title, source]
        """
        if self.signage_dialog is None:
            self.signage_dialog = CreateDialog(self._model.cacheSignageType(),
                                               self._model.getSignageLastRefkey,
                                               parent=None)

        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.updateRefkeyField()
        self.signage_dialog.signage_title_lineedit.setText(title)
        self.signage_dialog.signage_title_lineedit.setFocus()
        
        result = self.signage_dialog.exec()
        return result

    @Slot()
    def onEvidenceModelUpdate(self):
        """Refresh part of the treemodel upon evidence model update"""
        ok, err = self._model.updateReviewProgess()

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error refreshing model",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()

    @Slot()
    def deleteRow(self) -> None:
        """Trigger Delete row from the QSqlTableModel and TreeModel"""
        index: QtCore.QModelIndex = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        ok, msg = self._model.deleteRow(treemodel_index)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error deleting signage",
                                        msg,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return

        self.sigSignageTreemodelChanged.emit()
            
    @Slot(str)
    def onUpdatePrivateNoteTriggered(self, value: str):
        """Trigger signage's Private Note update from the info tab disabling update of the TreeModel"""
        index = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        
        ok, err = self._model.updateField(treemodel_index, self._model.Fields.Note.index, value, False)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error updating private note data",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
            
    @Slot(str)
    def onUpdatePublicNoteTriggered(self, value: str):
        """Trigger signage's Public Note update from the info tab disabling update of the TreeModel"""
        index = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        
        ok, err = self._model.updateField(treemodel_index, self._model.Fields.PublicNote.index, value, False)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error updating public note data",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
    
    @Slot(str)
    def onUpdateRefkeyTriggered(self, value: str):
        """Trigger signage's Refkey update from the info tab disabling update of the TreeModel"""
        index = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        
        ok, err = self._model.updateField(treemodel_index, self._model.Fields.Refkey.index, value, False)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error updating refkey data",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()

    @Slot(str)
    def onUpdateTitleTriggered(self, value: str):
        """Trigger signage's Title from the info tab disabling update of the TreeModel"""
        index = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        
        ok, err = self._model.updateField(treemodel_index, self._model.Fields.Title.index, value, False)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error updating title data",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
    
    @Slot(int)
    def onUpdateStatusTriggered(self, value: int, update_treemodel: bool = True):
        """Trigger signage's Status update on the QSqlTableModel and TreeModel"""
        parent = self.sender().parent()
        if isinstance(parent, SignageInfoWidget):
            update_treemodel = False

        index = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        
        ok, err = self._model.updateField(treemodel_index, self._model.Fields.Status.index, value, update_treemodel)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error updating status data",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
            
            
    @Slot(str)
    def onUpdateOwnerTriggered(self, value: str, update_treemodel: bool = True):
        """Trigger signage's Owner update on the QSqlTableModel and TreeModel"""

        parent = self.sender().parent()
        if isinstance(parent, SignageInfoWidget):
            update_treemodel = False

        index = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        
        ok, err = self._model.updateField(treemodel_index, self._model.Fields.Owner.index, value, update_treemodel)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error updating owner data ",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
            
    @Slot(int)
    def onUpdateTypeTriggered(self, value: int, update_treemodel: bool = True):
        """Trigger signage's Type update on the QSqlTableModel and TreeModel"""

        parent = self.sender().parent()
        if isinstance(parent, SignageInfoWidget):
            update_treemodel = False

        index = self.table.selectionModel().currentIndex()
        treemodel_index = self.proxy_model.mapToSource(index)
        
        ok, err = self._model.updateField(treemodel_index, self._model.Fields.Type.index, value, update_treemodel)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error updating type data ",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()

    @Slot()
    def setFilters(self):
        """Open Signage Filter Dialog"""
        if self.filter_dialog is None:
            self.filter_dialog = FilterDialog(statuses=self._model.cacheSignageStatus(),
                                              signage_types=self._model.cacheSignageType(),
                                              parent=self)    
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
        """Apply Filter on the Signage Table"""
        if self.filter_dialog is None:
            return

        self.proxy_model.setSatusFilter(self.filter_dialog.statusFilter(), self._model.Fields.Status.index)
        self.proxy_model.setTypeFilter(self.filter_dialog.typeFilter(), self._model.Fields.Type.index)
        self.proxy_model.setOwnerFilter(self.filter_dialog.ownerFilter(), self._model.Fields.Owner.index)
        self.proxy_model.setEvidenceFilter(self.filter_dialog.evidenceFilter(), self._model.Fields.Evidence.index)
        self.proxy_model.invalidateFilter()

    @Slot()
    def onResetFilters(self):
        """Reset Signage Table Filters"""
        self.proxy_model.setSatusFilter([], self._model.Fields.Status.index)
        self.proxy_model.setTypeFilter([], self._model.Fields.Type.index)
        self.proxy_model.setOwnerFilter([], self._model.Fields.Owner.index)
        self.proxy_model.setEvidenceFilter([], self._model.Fields.Evidence.index)
        self.proxy_model.setUserFilter("", [])
        self.search_tool.setText("")
        self.proxy_model.invalidateFilter()

        if self.filter_dialog is not None:
            self.filter_dialog.resetFields()
    
    @Slot()
    def onSortByCreationOrder(self):
        """Sort the Signage Table by order of creation"""
        self.table.sortByColumn(self._model.Fields.ID.index, QtCore.Qt.SortOrder.AscendingOrder)

    @Slot()
    def onExportTriggered(self):
        if self.export_dialog is None:
            self.export_dialog = ExportDialog(signage_types=self._model.cacheSignageType(),
                                              signage_statuses=self._model.cacheSignageStatus(),
                                              workspace_root=self._model.activeWorkspace().rootpath)

        if not self.export_dialog.exec():
            return
        
        selected_types = self.export_dialog.selected_types
        selected_statuses = self.export_dialog.selected_statuses
        outfile_destination = self.export_dialog.outfile_destination 
        include_public_note = self.export_dialog.include_public_note 

        ok, err = self._model.export2Excel(selected_types,
                                           selected_statuses,
                                           outfile_destination,
                                           include_public_note)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Export Signage to Excel",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
        else:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Information,
                                        "Export Signage to Excel",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
    
    @Slot()
    def onImportTriggered(self):
        if self.import_dialog is None:
            self.import_dialog = ImportDialog(workspace_root=self._model.activeWorkspace().rootpath)

        if not self.import_dialog.exec():
            return
        
        selected_files = self.import_dialog.selectedFiles()
        update_title = self.import_dialog.update_title

        ok, err = self._model.importFromExcel(selected_files, update_title)

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Importing Signage from Excel",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()

    @Slot(str)
    def searchfor(self, text: str):
        self.proxy_model.setUserFilter(text,
                                       [self._model.Fields.Refkey.index,
                                        self._model.Fields.Status.index,
                                        self._model.Fields.Title.index,
                                        self._model.Fields.Note.index,
                                        self._model.Fields.PublicNote.index,
                                        self._model.Fields.Owner.index])

        self.proxy_model.invalidateFilter()
    
    @Slot()
    def loadFromOnenote(self):
        self.oeloadspinner = WaitingSpinner(self, True, True, QtCore.Qt.WindowModality.WindowModal)
        self.oeloadspinner.start()
        worker = OneNoteWorker(self._model)
        worker.signals.finished.connect(self.handleWorkerEnded)
        self.threadpool.tryStart(worker)
    
    def importFromConnector(self):
        self.oeloadspinner = WaitingSpinner(self, True, True, QtCore.Qt.WindowModality.WindowModal)
        self.oeloadspinner.start()
        worker = DocxWorker(self._model)
        worker.signals.finished.connect(self.handleWorkerEnded)
        self.threadpool.tryStart(worker)

    @Slot(bool,str)
    def handleWorkerEnded(self, ok, msg):
        self.oeloadspinner.stop()

        if not ok:
            message_type = QtWidgets.QMessageBox.Icon.Critical
        else:
            message_type = QtWidgets.QMessageBox.Icon.Information

        msg = QtWidgets.QMessageBox(message_type,
                                    "Importing Signage Ended",
                                    msg,
                                    QtWidgets.QMessageBox.StandardButton.Ok, self)
        msg.exec()

    @Slot()
    def refresh(self):
        ok, err = self._model.refreshSourceModel()

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error refreshing source model",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
        
        ok, err = self._model.refreshTreeModel()

        if not ok:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical,
                                        "Error refreshing TreeModel",
                                        err,
                                        QtWidgets.QMessageBox.StandardButton.Ok, self)
            msg.exec()
        
        self._model.cacheOESignage()

    def closeEvent(self, a0):
        self.saveTableColumnWidth()
        self.info_tab.mapper.submit()
        
        if self.info_tab.mapper.model().sourceModel().lastError().isValid():
            err = self.info_tab.mapper.model().sourceModel().lastError().text()
            logger.error(f'Signage Model Error - {err}')

        return super().closeEvent(a0)
    
