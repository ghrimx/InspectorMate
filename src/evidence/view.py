# Standard library imports.
import logging
from pathlib import Path

# Related third party imports.
from qtpy import Qt, QtGui, QtCore, Signal, Slot, QtWidgets, QtSql


# Local application/library specific imports.
from database.database import AppDatabase

from evidence.model import EvidenceModel
from signage.model import SignageModel, SignageSqlModel

from base_models import ProxyModel
from base_delegates import NoteColumnDelegate, CompositeDelegate

from common import Document

from widgets.basetab import BaseTab
from widgets.richtexteditor import RichTextEditor
from widgets.fitcontenteditor import FitContentTextEdit
from widgets.combobox import CheckableComboBox
from widgets.tooltip_widget import QToolTipper
from widgets.folder_explorer import FolderExplorer
from widgets.readonly_linedit import ReadOnlyLineEdit

from utilities.config import settings
from utilities.utils import queryFileNameByID, open_file
from utilities.decorators import status_signal

from qt_theme_manager import theme_icon_manager, Theme

logger = logging.getLogger(__name__)


class FilterDialog(QtWidgets.QDialog):
    def __init__(self, statuses: list, parent=None):
        super().__init__(parent)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        self.status_combobox = CheckableComboBox()
        for item in statuses:
            self.status_combobox.addItem(item)

        form.addRow("Status:", self.status_combobox)
        form.addWidget(self.buttonBox)

    def accept(self):
        super().accept()

    def statusFilter(self):
        return [x for x in self.status_combobox.currentData()]
    
    def resetFields(self):
        self.status_combobox.clearSelection()


class SignageFilter(QtWidgets.QWidget):
    def __init__(self, model: SignageModel, parent=None):
        super(SignageFilter, self).__init__(parent)

        self._model = model.rootModel()
        self._proxy_model = ProxyModel(self._model)
        self._proxy_model.setPermanentFilter('Request', [SignageSqlModel.Fields.Type.index])
        self._proxy_model.setDynamicSortFilter(False)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        form = QtWidgets.QFormLayout()
        vbox.addLayout(form)

        self.search_field = QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Search...")
        vbox.addWidget(self.search_field)

        self.count_request = QtWidgets.QLabel()
        self.count_request.setText(str(self._proxy_model.rowCount()))
        form.addRow("Count:", self.count_request)

        self.table = QtWidgets.QTableView()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)  # Make ReadOnly
        self.table.setModel(self._proxy_model)
        tooltipper = QToolTipper(self.table)
        self.table.viewport().installEventFilter(tooltipper)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)

        for field in SignageSqlModel.Fields.fields():
            self.table.hideColumn(field.index)

        self.table.showColumn(SignageSqlModel.Fields.Refkey.index)
        self.table.showColumn(SignageSqlModel.Fields.Title.index)

        vbox.addWidget(self.table)

        # Connection
        self._model.dataChanged.connect(self.updateCounter)
        self._model.modelReset.connect(self.updateCounter)
        self.search_field.textChanged.connect(self.searchFor)

    @Slot()
    def updateCounter(self):
        self.count_request.setText(str(self._proxy_model.rowCount()))

    def searchFor(self):
        pattern = self.search_field.text()
        self._proxy_model.setUserFilter(pattern,
                                        [SignageSqlModel.Fields.Refkey.index,
                                         SignageSqlModel.Fields.Title.index])
        self._proxy_model.invalidateFilter()


class TitleColumnDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.cache_icon = {}
        self.icon_provider = QtWidgets.QFileIconProvider()

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)

        model: EvidenceModel = index.model().sourceModel()
        title = index.data(Qt.ItemDataRole.DisplayRole)
        file_path = index.sibling(index.row(), model.Fields.Filepath.index).data(Qt.ItemDataRole.DisplayRole)

        if file_path not in self.cache_icon:
            icon = self.icon_provider.icon(QtCore.QFileInfo(file_path)) 
            self.cache_icon[file_path] = icon
        else:
            icon = self.cache_icon[file_path]

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = icon
        option.text = title


class StatusColorDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        model = index.model()
        if hasattr(model, "mapToSource"):
            source_index = model.mapToSource(index)
            model: EvidenceModel = source_index.model()
        else:
            source_index = index

        if not hasattr(model, "Fields"):
            return

        fk_col = model.Fields.Status.index
        relation = model.relation(fk_col)
        rel_model = model.relationModel(fk_col)

        if not relation or rel_model is None:
            return

        color_value = None
        display_value = index.sibling(index.row(), model.Fields.Status.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        for r in range(rel_model.rowCount()):
            rec = rel_model.record(r)
            if rec.value(relation.displayColumn()) == display_value:
                color_value = rec.value("color")
                break

        if color_value == "#000000" and theme_icon_manager.get_theme() == Theme.DARK:
            color_value = theme_icon_manager.get_theme_color().name(QtGui.QColor.NameFormat.HexRgb)
        
        if color_value:
            option.palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(color_value))




#################################################################
#                        EvidenceTab
#################################################################

class EvidenceTab(BaseTab):
    sigOpenDocument = Signal(object, QtCore.QModelIndex)
    sigCreateSignage = Signal(str, str)
    sigCreateChildSignage = Signal(int, str)
    sigUpdateReviewProgress = Signal()

    def __init__(self,
                 model: EvidenceModel,
                 signage_model: SignageModel,
                 startSpinner: callable = None,
                 stopSpinner: callable = None,
                 parent=None):
        super(EvidenceTab, self).__init__(parent)
        self._model = model
        self.proxy_model = ProxyModel(self._model)
        self.proxy_model.setUserFilter('',
                                       [f.index for f in self._model.Fields.fields() if f.visible])
        self.proxy_model.setDynamicSortFilter(False)
        self.signage_model = signage_model
        self.startSpinner = startSpinner
        self.stopSpinner = stopSpinner
        self.createAction()
        self.initUI()

    def initUI(self):
        # --- Left Pane ---
        self.doc_filter = FolderExplorer()
        self.doc_filter.setRootPath(AppDatabase.activeWorkspace().evidence_path)
        self.doc_filter.rowClicked.connect(self.onFolderFilterClicked)
        self.left_pane.addTab(self.doc_filter, theme_icon_manager.get_icon(":node-tree"), "")

        self.signage_filter = SignageFilter(self.signage_model)
        self.signage_filter.table.clicked.connect(self.onRequestFilterClicked)
        self.left_pane.addTab(self.signage_filter, theme_icon_manager.get_icon(":request"), "")

        # --- Table ---
        self.table = QtWidgets.QTreeView()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers) # ReadOnly
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.customContextMenuRequested.connect(self.showContextMenu)
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(self._model.Fields.Refkey.index,
                                Qt.SortOrder.AscendingOrder)

        for field in self._model.Fields.fields():
            if not field.visible:
                self.table.hideColumn(field.index)

        # Table's connections
        self.table.clicked.connect(self.onCellClicked)
        self.table.selectionModel().selectionChanged.connect(self.updateAction)
        self.table.doubleClicked.connect(self.onTableDoubleClicked)

        # Table's delegates
        title_delegate = TitleColumnDelegate(self)
        note_delegate = NoteColumnDelegate(self.table)
        status_delegate = StatusColorDelegate(self)

        self.table.setItemDelegate(status_delegate)
        self.table.setItemDelegateForColumn(self._model.Fields.Note.index, note_delegate)

        combo_delegate = CompositeDelegate([status_delegate, title_delegate], self.table)
        self.table.setItemDelegateForColumn(self._model.Fields.Title.index, combo_delegate)

        # --- Right Pane ---
        self.status = QtWidgets.QComboBox()
        self.status.setModel(self._model.relationModel(4))
        self.status.setModelColumn(self._model.relationModel(4).fieldIndex('name'))
        
        self.title = FitContentTextEdit(False)
        self.refkey = QtWidgets.QLineEdit()
        self.subtitle = QtWidgets.QLineEdit()
        self.reference = QtWidgets.QLineEdit()
        self.filename = FitContentTextEdit(True)
        self.filename.setStyleSheet("color: grey;")
        self.note = RichTextEditor.fromMapper(bar=False, parent=self)
        
        self.signage_id = ReadOnlyLineEdit()

        formlayout = QtWidgets.QFormLayout()
        info_widget = QtWidgets.QWidget()
        info_widget.setLayout(formlayout)
        formlayout.addRow("Status", self.status)
        formlayout.addRow("Refkey", self.refkey)
        formlayout.addRow("Title", self.title)
        formlayout.addRow("SubTitle", self.subtitle)
        formlayout.addRow("Reference", self.reference)
        formlayout.addRow("Filename", self.filename)
        formlayout.addRow("Signage id", self.signage_id)
        spacer = QtWidgets.QSpacerItem(20,
                                       40,
                                       QtWidgets.QSizePolicy.Policy.Minimum,
                                       QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)
        self.right_pane.addTab(info_widget, "Info")
        self.right_pane.addTab(self.note, "Note")

        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(self._model)
        self.mapper.setItemDelegate(QtSql.QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.status, self._model.Fields.Status.index)
        self.mapper.addMapping(self.refkey, self._model.Fields.Refkey.index)
        self.mapper.addMapping(self.title, self._model.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.subtitle, self._model.Fields.Subtitle.index)
        self.mapper.addMapping(self.reference, self._model.Fields.Reference.index)
        self.mapper.addMapping(self.filename, self._model.Fields.Filepath.index, b"plainText")
        self.mapper.addMapping(self.note.editor, self._model.Fields.Note.index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)
        self.mapper.currentIndexChanged.connect(self._on_mapper_index_changed)
  
        self.status.currentIndexChanged[int].connect(self.mapper.submit)

         # --- Connections ---
        self.search_tool.textChanged.connect(self.searchfor)
        self.status.activated.connect(self.sigUpdateReviewProgress)
        self.refkey.editingFinished.connect(self.sigUpdateReviewProgress)
        self.refkey.editingFinished.connect(AppDatabase.update_document_signage_id)

        # --- Toolbar ---
        self.toolbar.insertAction(self.action_separator, self.load_file)
        self.toolbar.insertAction(self.action_separator, self.action_auto_refkey)        
        self.toolbar.insertAction(self.action_separator, self.action_filter_dlg)
        self.toolbar.insertAction(self.action_separator, self.action_resetfilter)
        self.toolbar.insertAction(self.action_separator, self.action_create_signage)       
        self.toolbar.insertAction(self.action_separator, self.action_create_child_signage)
        self.toolbar.insertAction(self.action_separator, self.action_cite)
        self.toolbar.insertAction(self.action_separator, self.action_delete_rows)

        # --- Shortcuts ---
        self.shortcut_create_childsignage = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+H"),
                                                            self,
                                                            self.createChildSignage,
                                                            context=QtCore.Qt.ShortcutContext.WindowShortcut)

        # --- Dialogs ---
        self.filter_dialog: FilterDialog = None

        # --- Layout ---
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.right_pane)
        self.splitter.setSizes([150, 500, 100])   

        # Restore view geometry
        self.restoreTableColumnWidth()

    def createAction(self):
        self.load_file = QtGui.QAction(theme_icon_manager.get_icon(":folder_upload"),
                                       "Load file",
                                       self,
                                       triggered=self.loadEvidence)
        self.action_auto_refkey = QtGui.QAction(theme_icon_manager.get_icon(":refkey"),
                                           "Detect refkey",
                                           self,
                                           triggered=self.autoRefKey)
        self.action_filter_dlg = QtGui.QAction(theme_icon_manager.get_icon(":filter-line"),
                                       "Filter",
                                       self,
                                       triggered=self.setFilters)
        self.action_resetfilter = QtGui.QAction(theme_icon_manager.get_icon(":filter-off-line"),
                                             "Reset Filters",
                                             self,
                                             triggered=self.onResetFilters)
        self.action_create_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line"),
                                                   "Create Signage (Ctrl + R)",
                                                   self,
                                                   triggered = self.createSignage)
        self.action_create_child_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line-child"),
                                                         "Create Child Signage (Ctrl + N)",
                                                         self,
                                                         triggered = self.createChildSignage)
        
        # --- Context Menu action ---
        self.action_delete_rows = QtGui.QAction(theme_icon_manager.get_icon(":delete-bin2"),
                                                "Delete",
                                                self,
                                                triggered=self.removeRows)
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
        self.action_copy_path = QtGui.QAction("Copy Path",
                                              self,
                                              triggered=self.copyPath)
        self.shortcut_action_cite = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+C"),
                                                    self,
                                                    self.cite,
                                                    context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.action_cite.setShortcut(QtGui.QKeySequence("Ctrl+Alt+C"))


        self.action_locate = QtGui.QAction(theme_icon_manager.get_icon(":search-line"),
                                           "Locate",
                                           self,
                                           triggered=self.locate)

        self.action_setRefKey = QtGui.QAction(theme_icon_manager.get_icon(":key-2-line"),
                                              "Set RefKey",
                                              self,
                                              triggered=self.setRefKey)

    def showContextMenu(self, pos: QtCore.QPoint):
        """Triggered when user right-clicks on the table."""
        indexes = self.table.selectedIndexes()
        if not indexes:
            return
        
        status_menu = QtWidgets.QMenu("Status", self)
        status_model = self._model.relationModel(self._model.Fields.Status.index)

        for row in range(status_model.rowCount()):
            record = status_model.record(row)
            status_id = record.value("uid") 
            status_name = record.value("name")
            action = status_menu.addAction(status_name)
            action.triggered.connect(lambda checked=False, sid=status_id: self.setStatus(sid))

        menu = QtWidgets.QMenu(self)
        menu.addMenu(status_menu)
        menu.addAction(self.action_create_child_signage)
        menu.addAction(self.action_open)
        menu.addAction(self.action_open_externally)
        menu.addAction(self.action_open_folder)
        menu.addAction(self.action_cite)
        menu.addAction(self.action_copy_path)
        menu.addAction(self.action_auto_refkey)
        menu.addAction(self.action_setRefKey)
        menu.addAction(self.action_locate)
        menu.addAction(self.action_resetfilter)
        menu.addAction(self.action_delete_rows)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_mapper_index_changed(self, row: int):
        """Workaround to solve mapper fail state due to foreign key "Signage_id" being null"""
        record = self._model.record(row)
        value = record.value(self._model.Fields.SignageID.index)
        self.signage_id.setText("" if value is None else str(value))
        
    def selectedRows(self) -> set[int]:
        """Source model's selected rows"""
        proxy_indexes = self.table.selectedIndexes()
        rows = set()
        for idx in proxy_indexes:
            src_idx = self.proxy_model.mapToSource(idx)
            rows.add(src_idx.row())
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

        if len(self.selectedRows()) == 0:
            self.action_open.setEnabled(False)
            self.action_open_externally.setEnabled(False)
            self.action_open_folder.setEnabled(False)
            self.action_cite.setEnabled(False)
            self.action_delete_rows.setEnabled(False)
            self.action_auto_refkey.setEnabled(False)
            self.action_setRefKey.setEnabled(False)
            self.action_locate.setEnabled(False)

        if len(self.selectedRows()) > 1:
            self.action_open.setEnabled(False)
            self.action_open_externally.setEnabled(False)
            self.action_open_folder.setEnabled(False)
            self.action_cite.setEnabled(False)
            self.action_delete_rows.setEnabled(True)
            self.action_auto_refkey.setEnabled(True)
            self.action_setRefKey.setEnabled(True)
            self.action_locate.setEnabled(False)
        
        msg = f"[Document selected: {len(self.selectedRows())}]"
        status_signal.status_message.emit(msg, 5000)
    
    def removeRows(self):
        msgbox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Question,
                                       "Delete document",
                                       "Are you sure you want to delete?",
                                       QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No,
                                       self)
        confirm = msgbox.exec()
        
        if not confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            return

        rows = self.selectedRows()
        msg = self._model.deleteRows(rows)
        status_signal.status_message.emit(msg, 5000)

    def autoRefKey(self):
        self._model.autoRefKey(self.selectedRows())

    def openFile(self):
        index: QtCore.QModelIndex = self.table.selectionModel().currentIndex()
        self.onTableDoubleClicked(index)

    def openWith(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(self.table.selectionModel().currentIndex())
        filepath = index.sibling(index.row(), self._model.Fields.Filepath.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        open_file(filepath)

    def openFolder(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(self.table.selectionModel().currentIndex())
        filepath = index.sibling(index.row(), self._model.Fields.Filepath.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        open_file(filepath, "folder")

    def cite(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(self.table.selectionModel().currentIndex())
        refkey = index.sibling(index.row(), self._model.Fields.Refkey.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        title = index.sibling(index.row(), self._model.Fields.Title.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        subtitle = index.sibling(index.row(), self._model.Fields.Subtitle.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        reference = index.sibling(index.row(), self._model.Fields.Reference.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        filepath: str = index.sibling(index.row(), self._model.Fields.Filepath.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        extension = f"'{filepath.split('.')[-1]}'"

        refkey = "refkey: " + refkey if refkey != "" else None
        title = f'"{title}"'
        citation = "; ".join(x for x in [refkey, title, subtitle, reference, extension] if x)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(f"[{citation}]")

    def copyPath(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(self.table.selectionModel().currentIndex())
        filepath: str = index.sibling(index.row(), self._model.Fields.Filepath.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(filepath)

    def locate(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(self.table.selectionModel().currentIndex())
        fileid = index.sibling(index.row(), self._model.Fields.FileID.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        filepath = queryFileNameByID(fileid)

        if Path(filepath).exists():
            folder = Path(filepath).parent.as_posix()
        else:
            folder = AppDatabase.activeWorkspace().evidence_path

        filepath = QtWidgets.QFileDialog.getOpenFileName(caption='Locate the file...', directory=folder)

        if filepath[0] != "":
            self._model.updateFilePath(index, filepath[0])

    def setRefKey(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Update refKey", "New refKey:")
        if ok and text != "":
            self._model.updateRefKey(self.selectedRows(), text)           

    def setStatus(self, status_id):
        if not self.selectedRows():
            return

        ok = self._model.updateStatus(self.selectedRows(), status_id)
        if not ok:
            status_signal.status_message.emit("[Evidence: failed to update status]", 7000)
            return
        
        status_signal.status_message.emit("[Evidence: status updated]", 7000)

        # Force refresh of the table view
        self.table.viewport().update()

        if hasattr(self, "mapper"):
            self.mapper.revert()  # revert caches   

    @Slot()
    def setFilters(self):
        if self.filter_dialog is None:
            status_model = self._model.relationModel(self._model.Fields.Status.index)
            status_list = []
            for row in range(status_model.rowCount()):
                record = status_model.record(row)
                status_id = record.value("uid") 
                status_name = record.value("name")
                status_list.append(status_name)

            self.filter_dialog = FilterDialog(status_list,
                                              self)
            self.filter_dialog.accepted.connect(self.applyFilters)

            # Move the dialog below the button
            ph = self.toolbar.widgetForAction(self.action_filter_dlg).geometry().height()
            pw = self.toolbar.widgetForAction(self.action_filter_dlg).geometry().width()
            px = self.toolbar.widgetForAction(self.action_filter_dlg).geometry().x()
            py = self.toolbar.widgetForAction(self.action_filter_dlg).geometry().y()
            dw = self.filter_dialog.width()
            dh = self.filter_dialog.height()   
            self.filter_dialog.setGeometry(px + int(dw / 2), py + (ph * 2) + (dh * 2), dw, dh )

        self.filter_dialog.exec()

    @Slot()
    def applyFilters(self):
        self.proxy_model.setSatusFilter(self.filter_dialog.statusFilter(),
                                        self._model.Fields.Status.index)
        self.proxy_model.invalidateFilter()
    
    @Slot(QtCore.QModelIndex)
    def onTableDoubleClicked(self, index: QtCore.QModelIndex):
        sidx = self.proxy_model.mapToSource(index) # Source index
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

        self.sigOpenDocument.emit(doc, sidx)

    @Slot()
    def searchfor(self):
        pattern = self.search_tool.text()
        self.proxy_model.setUserFilter(pattern,
                                    [self._model.Fields.Refkey.index,
                                        self._model.Fields.Status.index,
                                        self._model.Fields.Title.index,
                                        self._model.Fields.Note.index,
                                        self._model.Fields.Reference.index,
                                        self._model.Fields.Subtitle.index,
                                        self._model.Fields.Filepath.index])
        self.proxy_model.invalidateFilter()

    def onCellClicked(self, index: QtCore.QModelIndex):
        """ Update mapper """
        source_index = self.proxy_model.mapToSource(index)
        self.mapper.setCurrentModelIndex(source_index)

    @Slot(str)
    def onFolderFilterClicked(self, path: str):
        self.proxy_model.setUserFilter(path, [self._model.Fields.Filepath.index])
        self.proxy_model.invalidateFilter()

    @Slot(QtCore.QModelIndex)
    def onRequestFilterClicked(self, index: QtCore.QModelIndex):
        """Filter the Evidence table on Request Refkey clicked"""
        if index.isValid():
            signage_refkey = index.sibling(index.row(), SignageSqlModel.Fields.Refkey.index).data(Qt.ItemDataRole.DisplayRole)
            self.proxy_model.setUserFilter(f"{signage_refkey}", [self._model.Fields.Refkey.index])
            self.proxy_model.invalidateFilter()

    @Slot(str)
    def filterWithRefkey(self, refkey: str):
        self.proxy_model.setUserFilter(f"{refkey}", [self._model.Fields.Refkey.index])
        self.proxy_model.invalidateFilter()

    @Slot()
    def createSignage(self):
        source = f'{{"application":"InspectorMate", "module":"Evidence"}}'
        self.sigCreateSignage.emit("", source)

    @Slot()
    def createChildSignage(self):
        index = self.table.selectionModel().currentIndex()

        if not index.isValid():
            return

        sidx = self.proxy_model.mapToSource(index)
        signage_id = (sidx.sibling(sidx.row(),
                                   self._model.Fields.SignageID.index)
                                   .data(QtCore.Qt.ItemDataRole.DisplayRole))
        if not signage_id:
            return

        title = sidx.sibling(sidx.row(), self._model.Fields.Title.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        uid = sidx.sibling(sidx.row(), self._model.Fields.ID.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        source = f'{{"application":"InspectorMate", "module":"Evidence", "item":"document", "item_title":"{title}", "item_id":"{uid}"}}'
        self.sigCreateChildSignage.emit(signage_id, source)

    def _on_load_ended(self, m:str = ""):
        self.sigUpdateReviewProgress.emit()
        self.stopSpinner(m)

    @Slot()
    def loadEvidence(self):
        self.startSpinner()
        self._model.insertDocumentAsync(on_finished=self._on_load_ended)

    @Slot()
    def onResetFilters(self):
        """Reset Evidence Table Filters"""
        self.proxy_model.setUserFilter("", [self._model.Fields.Refkey.index])
        self.proxy_model.setSatusFilter([], self._model.Fields.Status.index)
        self.proxy_model.setTypeFilter([], self._model.Fields.Type.index)
        self.proxy_model.invalidateFilter()
        self.table.sortByColumn(self._model.Fields.Refkey.index, QtCore.Qt.SortOrder.AscendingOrder)

        self.search_tool.clear()

        if self.filter_dialog is not None:
            self.filter_dialog.resetFields()
    
    def restoreTableColumnWidth(self):
        """Restore table column width upon GUI initialization"""
        settings.beginGroup("evidence")
        for column in range(self._model.columnCount()):
            self.table.setColumnWidth(column, settings.value(f"column-{column}", 100, int))
        settings.endGroup()

    def saveTableColumnWidth(self):
        """Save table column width upon closing"""
        settings.beginGroup("evidence")
        for column in range(self._model.columnCount()):
            settings.setValue(f"column-{column}", self.table.columnWidth(column))
        settings.endGroup()

    @Slot()
    def refresh(self):
        self._model.refresh()
        self.doc_filter.setRootPath(AppDatabase.activeWorkspace().evidence_path)

    def closeEvent(self, a0):
        self.saveTableColumnWidth()
        self.mapper.submit()
        return super().closeEvent(a0)
