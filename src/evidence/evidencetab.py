import logging

from PyQt6.QtSql import QSqlRelationalDelegate
from qtpy import (Qt, QtWidgets, QtGui, QtCore, Signal, Slot)

from evidence.evidencemodel import (DocTableModel, DocExplorerModel, DocStatusSummary)
from evidence.evidencetable import DocTable

from signage.signagemodel import SignageTablelModel
from signage.signagetable import SignageTable

from models.model import ProxyModel

from db.database import AppDatabase
from db.dbstructure import Document

from widgets.basetab import BaseTab
from widgets.treeview import TreeView
from widgets.fitcontenteditor import FitContentTextEdit
from widgets.richtexteditor import RichTextEditor
from widgets.combobox import CheckableComboBox
from widgets.waitingspinner import WaitingSpinner

logger = logging.getLogger(__name__)


class LoadDocThread(QtCore.QThread):
    sig_load_ended = Signal()

    def __init__(self, model: DocTableModel, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._model = model

    def run(self):
        self._model.insertDocument()
        self.sig_load_ended.emit()


class DocInfoWidget(QtWidgets.QWidget):

    def __init__(self, model: DocTableModel, index: QtCore.QModelIndex, document: Document = None, parent=None):
        super().__init__(parent=parent)
        self._model = model
        self._index = index
        self._document = document

        formlayout = QtWidgets.QFormLayout(self)
        self.setLayout(formlayout)

        self.status = QtWidgets.QComboBox()
        self.status_model = self._model.relationModel(self._model.Fields.Status.index)
        self.status.setModel(self.status_model)
        self.status.setModelColumn(1)

        self.title = FitContentTextEdit(False)
        self.refKey = QtWidgets.QLineEdit()
        self.subtitle = QtWidgets.QLineEdit()
        self.reference = QtWidgets.QLineEdit()
        self.filename = FitContentTextEdit(True)
        self.note = RichTextEditor.fromMapper(bar=False, parent=self)

        formlayout.addRow("Status", self.status)
        formlayout.addRow("RefKey", self.refKey)
        formlayout.addRow("Title", self.title)
        formlayout.addRow("SubTitle", self.subtitle)
        formlayout.addRow("Reference", self.reference)
        formlayout.addRow("Filename", self.filename)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)

        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(self._model)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.status, self._model.Fields.Status.index)
        self.mapper.addMapping(self.refKey, self._model.Fields.RefKey.index)
        self.mapper.addMapping(self.title, self._model.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.subtitle, self._model.Fields.Subtitle.index)
        self.mapper.addMapping(self.reference, self._model.Fields.Reference.index)
        self.mapper.addMapping(self.filename, self._model.Fields.Filename.index, b"plainText")
        self.mapper.addMapping(self.note.editor, self._model.Fields.Note.index)
        self.mapper.setCurrentModelIndex(self._index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)

        self.status.activated.connect(self.submitMapper)

    def index(self):
        return self._index()

    def submitMapper(self):
        self.mapper.submit()

    def setMapperIndex(self, index: QtCore.QModelIndex):
        self.mapper.setCurrentModelIndex(index)

    def document(self):
        return self._document


class SummaryTab(QtWidgets.QWidget):
    def __init__(self, evidence_model: DocTableModel, parent=None):
        super().__init__(parent=parent)

        self._evidence_model = evidence_model
        self._model = DocStatusSummary()

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        form = QtWidgets.QFormLayout()
        vbox.addLayout(form)

        self.count_evidence = QtWidgets.QLabel()
        form.addRow("Total evidence:", self.count_evidence)

        self.status_table = QtWidgets.QTableView(self)
        self.status_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.status_table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.status_table.verticalHeader().setVisible(False)
        self.status_table.horizontalHeader().setVisible(True)
        self.status_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # self.status_table.horizontalHeader().setStretchLastSection(True)
        self.status_table.setModel(self._model)
        self._model.refresh()

        vbox.addWidget(self.status_table)

    def refreshWidget(self):
        self._model.refresh()
        self.count_evidence.setText(str(self._evidence_model.rowCount()))


class RefKeyTab(QtWidgets.QWidget):
    def __init__(self, model: SignageTablelModel = None, parent=None):
        super().__init__(parent)

        self._model = model
        self.table_proxy_model = ProxyModel(self._model)
        self.table_proxy_model.setPermanentFilter('request', [self._model.Fields.Type.index])
        self.table_proxy_model.setUserFilter('', self._model.visible_fields())
        self.table_proxy_model.setDynamicSortFilter(False)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        form = QtWidgets.QFormLayout()
        vbox.addLayout(form)

        self.count_request = QtWidgets.QLabel()
        form.addRow("Total request:", self.count_request)

        self.table = SignageTable(self._model, self.table_proxy_model)
        self.table.hide_columns(set(range(self._model.columnCount())) - {self._model.Fields.RefKey.index, self._model.Fields.Title.index})

        vbox.addWidget(self.table)

        self.count_request.setText(str(self.table_proxy_model.rowCount()))

    @Slot()
    def updateCounter(self):
        self.count_request.setText(f"{AppDatabase.countRequest()}")

class FilterDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        self.status_combobox = CheckableComboBox()
        self.status_combobox.addItems(AppDatabase.cache_doc_status.keys())

        form.addRow("Status:", self.status_combobox)
        form.addWidget(self.buttonBox)

    def accept(self):
        super().accept()

    def filters(self):
        return [x for x in self.status_combobox.currentData()]


class DocTab(BaseTab):
    sig_open_document = Signal(QtCore.QModelIndex)
    sig_load_file = Signal()

    def __init__(self, model: DocTableModel, parent=None):
        super().__init__(parent)
        self.create_models(model=model)
        self.initUI()
        self.connect_signals()

    def initUI(self):
        # Dialogs
        self.filter_dialog: FilterDialog = None

        # Left pane
        self.doc_filter = TreeView(parent=self, border=False)
        self.doc_filter.setModel(self.doc_explorer_model.proxy_model)
        self.doc_filter.setRootIndex(self.doc_explorer_model.proxy_index)
        self.doc_filter.hide_columns(range(1, self.doc_explorer_model.columnCount()))
        self.doc_filter.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.doc_filter.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        action_reset_doc_explorer_filter = QtGui.QAction("Reset filter", self.doc_filter)
        action_reset_doc_explorer_filter.triggered.connect(self.reset_doc_explorer_filter)
        self.doc_filter.addAction(action_reset_doc_explorer_filter)

        # Tag filter tab
        self.tag_filter = QtWidgets.QListView(self)

        # Summary tab
        self.summary_tab = SummaryTab(self.doctable_model)
        self.summary_tab.refreshWidget()

        self.left_pane.addTab(self.doc_filter, QtGui.QIcon(":node-tree"), "")
        self.left_pane.addTab(self.tag_filter, QtGui.QIcon(":tags"), "")
        self.left_pane.addTab(self.summary_tab, QtGui.QIcon(":percent-line"), "")

        # Central widget
        self.table = DocTable(model=self.doctable_model, proxy_model=self.doctable_proxy_model)
        self.table.hide_columns(self.doctable_model.hidden_fields())
        self.table.resizeColumnToContents(self.doctable_model.Fields.RefKey.index)
        self.table.resizeColumnToContents(self.doctable_model.Fields.Status.index)
        self.table.resizeColumnToContents(self.doctable_model.Fields.Note.index)
        self.table.resizeColumnToContents(self.doctable_model.Fields.Title.index)
        self.table.header().setSectionResizeMode(self.doctable_model.Fields.Reference.index, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.sortByColumn(self.doctable_model.Fields.RefKey.index, Qt.SortOrder.AscendingOrder)
        self.splitter.addWidget(self.table)

        # Right pane
        self.doc_info_tab = DocInfoWidget(self.doctable_model, QtCore.QModelIndex(), None)
        self.right_pane.addTab(self.doc_info_tab, "Info")
        self.right_pane.addTab(self.doc_info_tab.note, "Note")

        self.splitter.addWidget(self.right_pane)

        self.splitter.setSizes([150, 500, 100])

        # Toolbar
        self.load_file = QtGui.QAction(QtGui.QIcon(":folder_upload"), "Load file", self, triggered=self.handle_load_file)
        self.toolbar.insertAction(self.action_separator, self.load_file)

        self.detect_refkey = QtGui.QAction(QtGui.QIcon(":refkey"), "Detect refkey", self, triggered=self.table.autoRefKey)
        self.toolbar.insertAction(self.action_separator, self.detect_refkey)

        self.filtering = QtGui.QAction(QtGui.QIcon(":filter-line"), "Filter", self, triggered=self.setFilters)
        self.toolbar.insertAction(self.action_separator, self.filtering)

    def createRefKeyFilterPane(self, model):
        self.request_filter_tab = RefKeyTab(model=model)
        self.request_filter_tab.table.clicked.connect(self.onRequestFilterClicked)
        self.request_filter_tab.table.sortByColumn(SignageTablelModel.Fields.RefKey.index, Qt.SortOrder.AscendingOrder)
        self.left_pane.insertTab(1, self.request_filter_tab, QtGui.QIcon(":request"), "")

    @Slot()
    def setFilters(self):
        if self.filter_dialog is None:
            self.filter_dialog = FilterDialog(self)
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

    def applyFilters(self):
        self.doctable_proxy_model.setSatusFilter(self.filter_dialog.filters(), self.doctable_model.Fields.Status.index)
        self.doctable_proxy_model.invalidateFilter()

    def create_models(self, model: DocTableModel):
        self.doctable_model = model
        self.doctable_proxy_model = ProxyModel(self.doctable_model)
        self.doctable_proxy_model.setUserFilter('', self.doctable_model.visible_fields())
        self.doctable_proxy_model.setDynamicSortFilter(False)
        self.doc_explorer_model = DocExplorerModel()

    def connect_signals(self):
        self.table.selectionModel().selectionChanged.connect(self.onRowSelected)
        self.table.doubleClicked.connect(self.sig_open_document)
        self.doc_filter.selectionModel().selectionChanged.connect(self.onFolderFilterClicked)
        self.search_tool.textChanged.connect(self.searchfor)
        self.doctable_model.layoutChanged.connect(self.doctable_proxy_model.layoutChanged)
        self.doctable_model.layoutChanged.connect(self.doctable_proxy_model.invalidateFilter)
        self.doctable_model.layoutChanged.connect(lambda: self.doctable_proxy_model.setDynamicSortFilter(True))
        self.table.sig_doc_status_update.connect(self.summary_tab.refreshWidget)

    def selectedIndex(self) -> QtCore.QModelIndex:
        return self.selected_index

    @Slot()
    def searchfor(self):
        pattern = self.search_tool.text()
        self.doctable_proxy_model.setUserFilter(pattern,
                                                [self.doctable_model.Fields.RefKey.index,
                                                 self.doctable_model.Fields.Status.index,
                                                 self.doctable_model.Fields.Title.index,
                                                 self.doctable_model.Fields.Note.index,
                                                 self.doctable_model.Fields.Reference.index,
                                                 self.doctable_model.Fields.Subtitle.index,
                                                 self.doctable_model.Fields.Filepath.index])
        self.doctable_proxy_model.invalidateFilter()

    @Slot()
    def refresh(self):
        self.doctable_model.refresh()
        self.doc_explorer_model.refresh()
        self.doc_filter.setModel(self.doc_explorer_model.proxy_model)
        self.doc_filter.setRootIndex(self.doc_explorer_model.proxy_index)

    @Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def onRowSelected(self, selected: QtCore.QItemSelection, deseleted: QtCore.QItemSelection):
        if len(self.table.selectedRows()) == 1:
            self.selected_index = self.doctable_proxy_model.mapToSource(self.table.selectionModel().currentIndex())
            self.doc_info_tab.setMapperIndex(self.selected_index)

    @Slot()
    def onFolderFilterClicked(self):
        try:
            selected_index = self.doc_filter.selectionModel().currentIndex()
        except Exception as e:
            logger.error(e)
        else:
            folderpath = self.doc_explorer_model.get_path(selected_index)
            self.doctable_proxy_model.setUserFilter(folderpath.as_posix(), [self.doctable_model.Fields.Filepath.index])
            self.doctable_proxy_model.invalidateFilter()
            self.table.updateAction()

    @Slot(QtCore.QModelIndex)
    def onRequestFilterClicked(self, index: QtCore.QModelIndex):
        """Filter the Evidence table on Request Refkey clicked"""
        try:
            idx = self.request_filter_tab.table.model().index(index.row(), SignageTablelModel.Fields.RefKey.index)
        except Exception as e:
            logger.error(e)
        else:
            refkey = self.request_filter_tab.table.model().data(idx, Qt.ItemDataRole.DisplayRole)
            self.doctable_proxy_model.setUserFilter(f"{refkey}", [self.doctable_model.Fields.RefKey.index])
            self.doctable_proxy_model.invalidateFilter()

    @Slot()
    def reset_doc_explorer_filter(self):
        """Clear the document filter"""
        self.doc_filter.selectionModel().clearSelection()
        self.doctable_model.refresh()
        self.doctable_proxy_model.setUserFilter("", [self.doctable_model.Fields.Filepath.index])
        self.doctable_proxy_model.invalidateFilter()

    @Slot()
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
        self.doctable_model.apply_filter('doc_id', doclist)

    @Slot()
    def handle_load_file(self):
        self.docloadspinner = WaitingSpinner(self, True, True, Qt.WindowModality.WindowModal)
        self.docloadspinner.start()

        self.loaddoc_thread = LoadDocThread(self.doctable_model, parent=None)

        self.loaddoc_thread.sig_load_ended.connect(self.handleLoadEnded)
        self.loaddoc_thread.start()

    def close(self) -> bool:
        err = self.submitMapper()
        return err

    def handleLoadEnded(self):
        self.loaddoc_thread.quit()
        self.docloadspinner.stop()
        self.sig_load_file.emit()
        self.summary_tab.refreshWidget()

    @Slot()
    def submitMapper(self) -> bool:
        if self.doctable_model.lastError().text():
            err = True
            logger.info(f"Utility pane mapper submitted: {err}")
            logger.error(f'Mapper failed to submit - {self.doctable_model.lastError().text()}')
        else:
            self.doctable_model.submitAll()
            self.doctable_model.refresh()
            err = False
        return err
