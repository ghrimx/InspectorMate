import logging

from qtpy import (QtWidgets, QtCore, QtSql, QtGui, Signal, Slot)

from signage.signagemodel import SignageTablelModel
from signage.signagedialog import (CreateDialog, ExportDialog, ImportDialog)
from signage.signagetable import SignageTable
from models.model import ProxyModel

from db.dbstructure import Signage
from db.database import AppDatabase

from widgets.basetab import BaseTab
from widgets.richtexteditor import RichTextEditor
from widgets.fitcontenteditor import FitContentTextEdit
from widgets.combobox import CheckableComboBox

logger = logging.getLogger(__name__)


class SignageInfoWidget(QtWidgets.QWidget):
    def __init__(self, model: SignageTablelModel, index: QtCore.QModelIndex = QtCore.QModelIndex(), signage: Signage = None, parent=None):
        super().__init__(parent=parent)
        self._model = model
        self._index = index
        self._signage = signage

        formlayout = QtWidgets.QFormLayout(self)
        self.setLayout(formlayout)

        self.signage_status = QtWidgets.QLineEdit()
        self.signage_status.setReadOnly(True)

        self.title = FitContentTextEdit(False)
        self.ref_key = QtWidgets.QLineEdit()
        self.type_combobox = QtWidgets.QComboBox()
        self.type_model = model.relationModel(model.Fields.Type.index)
        self.type_combobox.setModel(self.type_model)
        self.type_combobox.setModelColumn(1)
        self.owner_combobox = QtWidgets.QLineEdit()

        self.note = RichTextEditor.fromMapper(bar=False, parent=self)

        formlayout.addRow('Title', self.title)
        formlayout.addRow('RefKey', self.ref_key)
        formlayout.addRow('Status', self.signage_status)
        formlayout.addRow('Type', self.type_combobox)
        formlayout.addRow('Owner', self.owner_combobox)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)

        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(self._model)
        self.mapper.setItemDelegate(QtSql.QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.signage_status, self._model.Fields.Status.index)
        self.mapper.addMapping(self.title, self._model.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.ref_key, self._model.Fields.RefKey.index)
        self.mapper.addMapping(self.type_combobox, self._model.Fields.Type.index)
        self.mapper.addMapping(self.owner_combobox, self._model.Fields.Owner.index)
        self.mapper.addMapping(self.note.editor, self._model.Fields.Note.index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)

    def index(self):
        return self._index()

    def setMapperIndex(self, index: QtCore.QModelIndex):
        self.mapper.setCurrentModelIndex(index)

    def submitMapper(self):
        self.mapper.submit()


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
        self.status_combobox.addItems(AppDatabase.cache_signage_status.keys())
        form.addRow("Status:", self.status_combobox)

        # _owners: list = mconf.settings.value("owners", [], "QStringList")
        # self.owner_combobox = CheckableComboBox()
        # self.owner_combobox.addItems(_owners)
        # form.addRow("Owner:", self.owner_combobox)

        self.document_received = QtWidgets.QCheckBox(self)
        form.addRow("Doc received:", self.document_received)

        form.addWidget(self.buttonBox)

    def accept(self):
        super().accept()

    def filters(self):
        return '|'.join([f"({x})" for x in self.status_combobox.currentData()])
    
    def chainedFilters(self):
        status_filter = '|'.join([f"({x})" for x in self.status_combobox.currentData()])
        if self.document_received.isChecked():
            doc_received_filter = "[1-9]"
        else:
            doc_received_filter = "[0-9]"

        return status_filter, doc_received_filter
        

    # def ownerFilter(self):
    #     return '|'.join([f"({x})" for x in self.owner_combobox.currentData()])


class SignageTab(BaseTab):
    sig_signage_model_changed = Signal()

    def __init__(self, model: SignageTablelModel, signage_type: str, parent=None):
        super().__init__(parent=parent)
        self.signage_type = signage_type
        self.table_model = model
        self.table_proxy_model = ProxyModel(self.table_model)

        self.table_proxy_model.setPermanentFilter(self.signage_type, [self.table_model.Fields.Type.index])
        self.table_proxy_model.setUserFilter('', self.table_model.visible_fields())
        self.table_proxy_model.setDynamicSortFilter(False)

        self.initUI()
        self.connectSignals()

    def proxyModel(self) -> ProxyModel:
        return self.table_proxy_model

    def signageType(self):
        return self.signage_type

    def initUI(self):
        self.export_dialog = None
        self.create_dialog = None
        self.filter_dialog: FilterDialog = None

        # Toolbar
        self.btn_import_from_onenote = QtWidgets.QPushButton()
        self.btn_import_from_onenote.setIcon(QtGui.QIcon(":onenote"))
        self.btn_import_from_onenote.setToolTip("Import signage from OneNote")
        self.btn_import_from_onenote.clicked.connect(self.import_from_onenote)
        self.toolbar.insertWidget(self.action_separator, self.btn_import_from_onenote)

        self.btn_filter = QtWidgets.QPushButton()
        self.btn_filter.setIcon(QtGui.QIcon(":filter-line"))
        self.btn_filter.setToolTip("Filter")
        self.btn_filter.clicked.connect(self.setFilters)
        self.toolbar.insertWidget(self.action_separator, self.btn_filter)

        # Left pane

        # Central widget
        self.table = SignageTable(model=self.table_model, proxy_model=self.table_proxy_model)
        if self.signage_type == "request":
            hidden_fields = self.table_model.hidden_fields()
            hidden_fields.add(self.table_model.Fields.Type.index)
        else:
            hidden_fields = self.table_model.hidden_fields()
            hidden_fields.add(self.table_model.Fields.EvidenceEOL.index)
            hidden_fields.add(self.table_model.Fields.Evidence.index)

        self.table.hide_columns(hidden_fields)
        self.table.resizeColumnToContents(self.table_model.Fields.Evidence.index)
        self.table.resizeColumnToContents(self.table_model.Fields.RefKey.index)
        self.table.resizeColumnToContents(self.table_model.Fields.Status.index)
        self.table.setColumnWidth(self.table_model.Fields.EvidenceEOL.index, 60)
        self.table.resizeColumnToContents(self.table_model.Fields.Type.index)
        self.table.resizeColumnToContents(self.table_model.Fields.Note.index)
        self.table.resizeColumnToContents(self.table_model.Fields.Owner.index)
        self.table.resizeColumnToContents(self.table_model.Fields.Title.index)

        self.table.setUniformRowHeights(True)
        self.table.sortByColumn(SignageTablelModel.Fields.RefKey.index, QtCore.Qt.SortOrder.AscendingOrder)

        self.splitter.addWidget(self.table)

        # Right pane
        self.right_pane = QtWidgets.QTabWidget(self)
        self.info_tab = SignageInfoWidget(self.table_model)
        self.right_pane.addTab(self.info_tab, "Info")
        self.right_pane.addTab(self.info_tab.note, "Note")
        self.splitter.addWidget(self.right_pane)

        self.splitter.setSizes([150, 500, 100])

        # Remove the left pane and the button
        self.left_pane.hide()
        self.toolbar.removeAction(self.action_fold_left_sidebar)

    def refresh(self):
        pass

    def connectSignals(self):
        self.table.selectionModel().currentRowChanged.connect(self.onCurrentRowChanged)
        self.search_tool.textChanged.connect(self.searchfor)

    @Slot()
    def import_from_onenote(self):
        self.table_model.fetch_onenote()

    @Slot()
    def searchfor(self):
        pattern = self.search_tool.text()
        self.table_proxy_model.setUserFilter(pattern,
                                             [self.table_model.Fields.RefKey.index,
                                              self.table_model.Fields.Status.index,
                                              self.table_model.Fields.Title.index,
                                              self.table_model.Fields.Note.index,
                                              self.table_model.Fields.Owner.index])

        self.table_proxy_model.invalidateFilter()

    @Slot(QtCore.QModelIndex, QtCore.QModelIndex)
    def onCurrentRowChanged(self, currentIndex, previousIndex):
        currentIndex = self.table_proxy_model.mapToSource(currentIndex)
        self.info_tab.mapper.setCurrentModelIndex(currentIndex)

    @Slot()
    def handle_type_changed(self):
        self.submit_mapper()

    @Slot()
    def setFilters(self):
        if self.filter_dialog is None:
            self.filter_dialog = FilterDialog(self)
        res = self.filter_dialog.exec()

        if res == 1:
            self.applyFilters()

    def applyFilters(self):
        self.table_proxy_model.setUserFilter(self.filter_dialog.filters(), [self.table_model.Fields.Status.index])
        # self.table_proxy_model.setUserFilter(self.filter_dialog.ownerFilter(), [self.table_model.Fields.Owner.index])
        filters = self.filter_dialog.chainedFilters()
        columns = [self.table_model.Fields.Status.index, self.table_model.Fields.Evidence.index]

        self.table_proxy_model.setChainedFilters(filters, columns)

        self.table_proxy_model.invalidateFilter()

    def exportSignage(self):
        if self.export_dialog is None:
            self.export_dialog = ExportDialog(model=self.table_model)

        self.export_dialog.exec()

    def createSignage(self, text=""):
        if self.create_dialog is None:
            self.create_dialog = CreateDialog(model=self.table_model, parent=None)
        self.create_dialog.signage_title_lineedit.setText(text)
        self.create_dialog.signage_title_lineedit.setFocus()
        self.create_dialog.signage_type_combobox.setCurrentIndex(0)
        self.create_dialog.update_refKey_fields()
        res = self.create_dialog.exec()
        return res

    def importRequest(self):
        self.import_signage_dlg = ImportDialog(model=self.table_model)
        self.import_signage_dlg.exec()

    def close(self) -> bool:
        err = self.submit_mapper()
        return err

    @Slot()
    def submit_mapper(self) -> bool:
        if self.table_model.lastError().text():
            err = True
            logger.error(f'Signage Table Model Error - {self.table_model.lastError().text()}')
        else:
            self.table_model.submitAll()
            self.table_model.refresh()
            err = False
        return err
