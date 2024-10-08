import logging

from PyQt6.QtSql import QSqlRelationalDelegate
from qtpy import (Qt, QtWidgets, QtGui, QtCore, Signal, Slot)

from evidence.evidencemodel import (DocTableModel, DocExplorerModel, DocStatusSummary)
from evidence.evidencetable import DocTable
from signage.signagemodel import SignageTablelModel

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
        self.status_table.verticalHeader().setVisible(False)
        self.status_table.horizontalHeader().setVisible(True)
        self.status_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.status_table.horizontalHeader().setStretchLastSection(True)
        self.status_table.setModel(self._model)
        self._model.refresh()

        vbox.addWidget(self.status_table)

    def refreshWidget(self):
        self._model.refresh()
        self.count_evidence.setText(str(self._evidence_model.rowCount()))


class RefKeyTab(QtWidgets.QWidget):
    def __init__(self, model: SignageTablelModel = None, parent=None):
        super().__init__(parent)

        self.model = model
        self.table_proxy_model = ProxyModel(self.model)
        self.table_proxy_model.setPermanentFilter('request', [self.model.Fields.Type.index])
        self.table_proxy_model.setUserFilter('', self.model.visible_fields())
        self.table_proxy_model.setDynamicSortFilter(False)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        form = QtWidgets.QFormLayout()
        vbox.addLayout(form)

        self.count_request = QtWidgets.QLabel()
        form.addRow("Total request:", self.count_request)

        self.request_list = TreeView(self)
        self.request_list.setModel(self.table_proxy_model)
        self.request_list.hide_columns(set(range(self.model.columnCount())) - {self.model.Fields.RefKey.index, self.model.Fields.Title.index})
        self.request_list.resizeColumnToContents(self.model.Fields.RefKey.index)
        self.request_list.resizeColumnToContents(self.model.Fields.Title.index)

        self.request_list.setRootIsDecorated(False)
        self.request_list.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.request_list.setAutoScroll(False)

        vbox.addWidget(self.request_list)

        self.count_request.setText(str(self.table_proxy_model.rowCount()))

    @Slot()
    def updateCounter(self):
        self.count_request.setText(f"{AppDatabase.countRequest()}")

class FilterDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

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
        return '|'.join([f"({x})" for x in self.status_combobox.currentData()])


class DocTab(BaseTab):
    sig_open_document = Signal(QtCore.QModelIndex)
    sig_load_file = Signal()

    def __init__(self, model: DocTableModel):
        self.create_models(model=model)
        self.initUI()
        self.connect_signals()

    def initUI(self):
        super().__init__()

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
        self.info_widget_dict = {}
        self.info_area = QtWidgets.QStackedLayout()
        self.info_placeholder = QtWidgets.QWidget()
        self.info_placeholder.setLayout(self.info_area)
        self.right_pane.addTab(self.info_placeholder, "Info")

        self.note_widget_dict = {}
        self.note_area = QtWidgets.QStackedLayout()
        self.note_placeholder = QtWidgets.QWidget()
        self.note_placeholder.setLayout(self.note_area)
        self.right_pane.addTab(self.note_placeholder, "Note")

        self.splitter.addWidget(self.right_pane)

        self.splitter.setSizes([150, 500, 100])

        # Toolbar
        self.load_file = QtGui.QAction(QtGui.QIcon(":folder_upload"), "Load file", self, triggered=self.handle_load_file)
        self.toolbar.insertAction(self.action_separator, self.load_file)

        self.btn_detect_refkey = QtWidgets.QPushButton()
        self.btn_detect_refkey.setIcon(QtGui.QIcon(":refkey"))
        self.btn_detect_refkey.setToolTip("Detect refkey")
        self.btn_detect_refkey.clicked.connect(lambda: self.doctable_model.updateRefKey(self.table.selectedRows()))
        self.toolbar.insertWidget(self.action_separator, self.btn_detect_refkey)

        self.btn_filter = QtWidgets.QPushButton()
        self.btn_filter.setIcon(QtGui.QIcon(":filter-line"))
        self.btn_filter.setToolTip("Filter")
        self.btn_filter.clicked.connect(self.setFilters)
        self.toolbar.insertWidget(self.action_separator, self.btn_filter)

    def createRefKeyFilterPane(self, model):
        self.request_filter_tab = RefKeyTab(model=model)
        self.request_filter_tab.request_list.clicked.connect(self.onRequestFilterClicked)
        self.request_filter_tab.request_list.sortByColumn(SignageTablelModel.Fields.RefKey.index, Qt.SortOrder.AscendingOrder)
        self.left_pane.insertTab(1, self.request_filter_tab, QtGui.QIcon(":request"), "")

    @Slot()
    def setFilters(self):
        if self.filter_dialog is None:
            self.filter_dialog = FilterDialog(self)
        res = self.filter_dialog.exec()

        if res == 1:
            self.applyFilters()

    def applyFilters(self):
        self.doctable_proxy_model.setUserFilter(self.filter_dialog.filters(), [self.doctable_model.Fields.Status.index])
        self.doctable_proxy_model.invalidateFilter()

    def create_models(self, model: DocTableModel):
        self.doctable_model = model
        self.doctable_proxy_model = ProxyModel(self.doctable_model)
        self.doctable_proxy_model.setUserFilter('', self.doctable_model.visible_fields())
        self.doctable_proxy_model.setDynamicSortFilter(False)
        self.doc_explorer_model = DocExplorerModel()

    def connect_signals(self):
        self.table.selectionModel().selectionChanged.connect(self.onRecordSelected)
        self.table.doubleClicked.connect(self.sig_open_document)
        self.doc_filter.selectionModel().selectionChanged.connect(self.onFolderFilterClicked)
        self.search_tool.textChanged.connect(self.searchfor)
        self.doctable_model.layoutChanged.connect(self.doctable_proxy_model.layoutChanged)
        self.doctable_model.layoutChanged.connect(self.doctable_proxy_model.invalidateFilter)
        self.doctable_model.layoutChanged.connect(lambda: self.doctable_proxy_model.setDynamicSortFilter(True))

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
    def onRecordSelected(self, selected: QtCore.QItemSelection, deseleted: QtCore.QItemSelection):
        """Refresh dependent model and view when the selection change in the central widget"""

        if len(self.table.selectedRows()) == 1:
            self.selected_index = self.doctable_proxy_model.mapToSource(self.table.selectionModel().currentIndex())

            doc: Document = self.table.document()

            if doc is not None:
                info_stack_widget_index = self.info_widget_dict.get(doc.id)
                if info_stack_widget_index is None:
                    info_widget = DocInfoWidget(self.doctable_model, self.selected_index, doc)
                    info_stack_widget_index = self.info_area.addWidget(info_widget)
                    self.info_widget_dict[doc.id] = info_stack_widget_index

                self.info_area.setCurrentIndex(info_stack_widget_index)

                note_stack_widget_index = self.note_widget_dict.get(doc.id)
                if note_stack_widget_index is None:
                    note_widget = info_widget.note
                    note_stack_widget_index = self.note_area.addWidget(note_widget)
                    self.note_widget_dict[doc.id] = note_stack_widget_index
                    self.right_pane.currentChanged.connect(info_widget.submitMapper)
                    info_widget.refKey.textChanged.connect(info_widget.submitMapper)

                self.note_area.setCurrentIndex(note_stack_widget_index)

                info_widget: DocInfoWidget = self.info_area.currentWidget()
                info_widget.setMapperIndex(self.selected_index)

    @Slot()
    def onFolderFilterClicked(self):
        selected_index = self.doc_filter.selectionModel().currentIndex()
        folderpath = self.doc_explorer_model.get_path(selected_index)
        self.doctable_proxy_model.setUserFilter(folderpath.as_posix(), [self.doctable_model.Fields.Filepath.index])
        self.doctable_proxy_model.invalidateFilter()
        self.table.updateAction()

    @Slot(QtCore.QModelIndex)
    def onRequestFilterClicked(self, index: QtCore.QModelIndex):
        """Filter the Evidence table on Request Refkey clicked"""
        idx = self.request_filter_tab.request_list.model().index(index.row(), SignageTablelModel.Fields.RefKey.index)
        refkey = self.request_filter_tab.request_list.model().data(idx, Qt.ItemDataRole.DisplayRole)
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
