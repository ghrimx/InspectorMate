import logging
from pathlib import Path

from my_pyqt_widgets import (
    FileSystem,
    FitContentTextEdit,
    MultiCheckableComboBox,
    QToolTipper,
    ReadOnlyLineEdit,
)
from pyqt6_richtexteditor import RichTextEdit
from qt_theme_manager import Theme, theme_icon_manager

from base_delegates import CompositeDelegate, NoteColumnDelegate
from common import Document, SignageOrigin
from database.database import AppDatabase
from evidence.model import EvidenceModel
from evidence.style import TABLE_STYLE
from qtpy import Qt, QtCore, QtGui, QtSql, QtWidgets, Signal, Slot
from signage.model import SignageModel, SignageSqlModel
from utilities.decorators import status_signal
from utilities.settings import get_settings
from utilities.utils import open_file, queryFileNameByID
from widgets.basetab import BaseTab
from widgets.clipboard import ClipboardExporter
from widgets.generic_filter_dialog import FilterField, GenericFilterDialog
from widgets.generic_proxymodel import FilterKind, GenericFilterProxyModel

logger = logging.getLogger(__name__)


class SignageFilter(QtWidgets.QWidget):
    def __init__(self, model: SignageModel, parent=None):
        super().__init__(parent)

        self._model = model.rootModel()
        self._proxy_model = GenericFilterProxyModel(self._model)
        self._proxy_model.set_filter(
            "request", SignageSqlModel.Fields.Type.index, FilterKind.REGEX, "Request"
        )

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
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )  # Make ReadOnly
        self.table.setModel(self._proxy_model)
        tooltipper = QToolTipper(self.table)
        self.table.viewport().installEventFilter(tooltipper)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.table.setSelectionBehavior(
            QtWidgets.QTableView.SelectionBehavior.SelectRows
        )
        self.table.setAutoScroll(False)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        for field in SignageSqlModel.Fields.fields():
            self.table.hideColumn(field.index)
        self.table.showColumn(SignageSqlModel.Fields.Refkey.index)
        self.table.showColumn(SignageSqlModel.Fields.Title.index)

        vbox.addWidget(self.table)

        # Connection
        self._model.dataChanged.connect(self.updateCounter)
        self._model.modelReset.connect(self.updateCounter)
        self.search_field.textChanged.connect(self.searchFor)

        self.restoreTableColumnWidth()

    @Slot()
    def updateCounter(self):
        self.count_request.setText(str(self._proxy_model.rowCount()))

    def searchFor(self):
        pattern = self.search_field.text()
        self._proxy_model.set_search_text(
            pattern,
            [SignageSqlModel.Fields.Refkey.index, SignageSqlModel.Fields.Title.index],
        )

    def restoreTableColumnWidth(self):
        """Restore table column width upon GUI initialization"""
        settings = get_settings()
        for column in range(self._model.columnCount()):
            width = settings.get_column_width("signage_filter", column)
            self.table.setColumnWidth(column, width)

    def saveTableColumnWidth(self):
        """Save table column width upon closing"""
        settings = get_settings()
        for column in range(self._model.columnCount()):
            width = self.table.columnWidth(column)
            settings.set_column_width("signage_filter", column, width)

    def closeEvent(self, a0):
        self.saveTableColumnWidth()
        return super().closeEvent(a0)


class TitleColumnDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.cache_icon = {}
        self.icon_provider = QtWidgets.QFileIconProvider()

    def initStyleOption(
        self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ) -> None:
        super().initStyleOption(option, index)

        model: EvidenceModel = index.model().sourceModel()
        title = index.data(Qt.ItemDataRole.DisplayRole)
        file_path = index.sibling(index.row(), model.Fields.Filepath.index).data(
            Qt.ItemDataRole.DisplayRole
        )

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

    def initStyleOption(
        self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ) -> None:
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
        display_value = index.sibling(index.row(), model.Fields.Status.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        for r in range(rel_model.rowCount()):
            rec = rel_model.record(r)
            if rec.value(relation.displayColumn()) == display_value:
                color_value = rec.value("color")
                break

        if color_value == "#000000" and theme_icon_manager.get_theme() == Theme.DARK:
            color_value = theme_icon_manager.get_theme_color().name(
                QtGui.QColor.NameFormat.HexRgb
            )

        if color_value:
            option.palette.setColor(
                QtGui.QPalette.ColorRole.Text, QtGui.QColor(color_value)
            )


#################################################################
#                        EvidenceTab
#################################################################


class EvidenceTab(BaseTab):
    sigOpenDocument = Signal(object, QtCore.QModelIndex, str)
    sigCreateSignage = Signal(str, dict)
    sigCreateChildSignage = Signal(int, object)
    sigUpdateReviewProgress = Signal()

    def __init__(
        self,
        model: EvidenceModel,
        signage_model: SignageModel,
        startSpinner: callable | None = None,
        stopSpinner: callable | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._model = model
        self.proxy_model = GenericFilterProxyModel(self._model)
        self.signage_model = signage_model
        self.startSpinner = startSpinner
        self.stopSpinner = stopSpinner
        self.createAction()
        self.initUI()

    def initUI(self):
        # --- Left Pane ---
        self.doc_filter = FileSystem(
            AppDatabase.activeWorkspace().evidence_path,
            mode=FileSystem.Mode.FolderOnly,
            read_only=True,
        )
        self.doc_filter.sigSingleClicked.connect(self.onFolderFilterClicked)
        self.left_pane.addTab(
            self.doc_filter, theme_icon_manager.get_icon(":node-tree"), ""
        )

        self.signage_filter = SignageFilter(self.signage_model)
        self.signage_filter.table.clicked.connect(self.onRequestFilterClicked)
        self.left_pane.addTab(
            self.signage_filter, theme_icon_manager.get_icon(":request"), ""
        )

        # --- Table ---
        self.table = QtWidgets.QTreeView()
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )  # ReadOnly
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setModel(self.proxy_model)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.table.customContextMenuRequested.connect(self.showContextMenu)
        self.table.setSortingEnabled(True)

        for field in self._model.Fields.fields():
            if not field.visible:
                self.table.hideColumn(field.index)

        # Table's connections
        self.table.selectionModel().selectionChanged.connect(
            self.onTableSelectionChanged
        )
        self.table.doubleClicked.connect(self.onTableDoubleClicked)

        # Table's delegates
        title_delegate = TitleColumnDelegate(self)
        note_delegate = NoteColumnDelegate(self.table)
        status_delegate = StatusColorDelegate(self)

        self.table.setItemDelegate(status_delegate)
        self.table.setItemDelegateForColumn(
            self._model.Fields.Note.index, note_delegate
        )

        combo_delegate = CompositeDelegate(
            [status_delegate, title_delegate], self.table
        )
        self.table.setItemDelegateForColumn(
            self._model.Fields.Title.index, combo_delegate
        )

        if theme_icon_manager.get_theme() == Theme.LIGHT:
            self.table.setStyleSheet(TABLE_STYLE)

        tooltip = QToolTipper(self.table)

        # --- Right Pane ---
        self.status = QtWidgets.QComboBox()
        self.status.setModel(self._model.relationModel(4))
        self.status.setModelColumn(self._model.relationModel(4).fieldIndex("name"))

        self.title = FitContentTextEdit(False)
        self.refkey = QtWidgets.QLineEdit()
        self.subtitle = QtWidgets.QLineEdit()
        self.reference = QtWidgets.QLineEdit()
        self.filepath_edit = FitContentTextEdit(True)
        self.note = RichTextEdit(":memory", ":memory", "")

        self.signage_id = ReadOnlyLineEdit()
        self.uploaded_on_edit = ReadOnlyLineEdit()

        formlayout = QtWidgets.QFormLayout()
        info_widget = QtWidgets.QWidget()
        info_widget.setLayout(formlayout)
        formlayout.addRow("Status", self.status)
        formlayout.addRow("Refkey", self.refkey)
        formlayout.addRow("Title", self.title)
        formlayout.addRow("SubTitle", self.subtitle)
        formlayout.addRow("Reference", self.reference)
        formlayout.addRow("Filepath", self.filepath_edit)
        formlayout.addRow("Signage id", self.signage_id)
        formlayout.addRow("Uploaded on", self.uploaded_on_edit)

        spacer = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
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
        self.mapper.addMapping(
            self.filepath_edit, self._model.Fields.Filepath.index, b"plainText"
        )
        self.mapper.addMapping(
            self.uploaded_on_edit, self._model.Fields.UploadedDatetime.index
        )
        self.mapper.addMapping(self.note, self._model.Fields.Note.index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)
        self.mapper.currentIndexChanged.connect(self._on_mapper_index_changed)

        # --- Connections ---
        self.search_tool.textChanged.connect(self.searchfor)
        self.status.activated.connect(self.sigUpdateReviewProgress)
        self.refkey.editingFinished.connect(self.sigUpdateReviewProgress)
        self.refkey.editingFinished.connect(AppDatabase.update_document_signage_id)
        self.refkey.editingFinished.connect(
            lambda: self._model.updateRefKey(
                [self.table.currentIndex().row()], self.refkey.text()
            )
        )

        # --- Dialogs ---
        self.filter_dialog: GenericFilterDialog = None

        # --- Layout ---
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.right_pane)
        self.splitter.setSizes([150, 500, 100])

        # Restore view geometry
        self.restoreTableColumnWidth()

        self.onTableSelectionChanged()

    def createAction(self):
        self.load_file = self.toolbar.add_action(
            "load_file",
            "Load file",
            self.loadEvidence,
            theme_icon_manager.get_icon(":folder_upload"),
            before="spacer",
        )
        self.action_auto_refkey = self.toolbar.add_action(
            "detect_refkey",
            "Detect refkey",
            self.autoRefKey,
            theme_icon_manager.get_icon(":refkey"),
            before="spacer",
        )
        self.action_open_filter_dlg = self.toolbar.add_action(
            "filter",
            "Filter",
            self.openFilterDialog,
            theme_icon_manager.get_icon(":filter-line"),
            before="spacer",
        )
        self.action_resetfilter = self.toolbar.add_action(
            "reset_filter",
            "Reset Filters",
            self.onResetFilters,
            theme_icon_manager.get_icon(":filter-off-line"),
            before="spacer",
        )
        self.action_create_child_signage = self.toolbar.add_action(
            "create_child_signage",
            "Create Child Signage",
            self.createChildSignage,
            theme_icon_manager.get_icon(":signpost-line-child"),
            "Ctrl+H",
            context=Qt.ShortcutContext.WindowShortcut,
            before="spacer",
        )

        # --- Context Menu action ---
        self.action_delete_rows = self.toolbar.add_action(
            "delete_evidence",
            "Delete",
            self.removeRows,
            theme_icon_manager.get_icon(":delete-bin2"),
            before="spacer",
        )
        self.action_open = self.toolbar.add_action(
            "open_evidence",
            "Open...",
            self.openFile,
            theme_icon_manager.get_icon(":file-4-line"),
            before="spacer",
        )
        self.action_open_externally = self.toolbar.add_action(
            "open_with",
            "Open with...",
            self.openWith,
            theme_icon_manager.get_icon(":share-forward-2-line"),
            before="spacer",
        )
        self.action_open_folder = self.toolbar.add_action(
            "open_folder",
            "Open folder",
            self.openFolder,
            theme_icon_manager.get_icon(":folder-open-line"),
            before="spacer",
        )
        self.action_cite = self.toolbar.add_action(
            "cite_evidence",
            "Cite",
            self.cite,
            theme_icon_manager.get_icon(":double-quotes"),
            "Ctrl+C",
            context=Qt.ShortcutContext.WindowShortcut,
            before="spacer",
        )
        self.action_copy_path = self.toolbar.add_action(
            "copy_path",
            "Copy Path",
            self.copyPath,
            theme_icon_manager.get_icon(":slash-commands-2"),
            before="spacer",
        )
        self.action_locate = self.toolbar.add_action(
            "locate_evidence",
            "Locate",
            self.locate,
            theme_icon_manager.get_icon(":search-line"),
            before="spacer",
        )
        self.action_setRefKey = self.toolbar.add_action(
            "set_refkey_evidence",
            "Set RefKey",
            self.setRefKey,
            theme_icon_manager.get_icon(":key-2-line"),
            before="spacer",
        )

        # Status Menu
        self.status_menu = QtWidgets.QMenu("Status", self.toolbar)
        status_model = self._model.relationModel(self._model.Fields.Status.index)

        for row in range(status_model.rowCount()):
            record = status_model.record(row)
            status_id = record.value("uid")
            status_name = record.value("name")
            action = self.status_menu.addAction(status_name)
            action.triggered.connect(
                lambda checked=False, sid=status_id: self.setStatus(sid)
            )

    def showContextMenu(self, pos: QtCore.QPoint):
        """Triggered when user right-clicks on the table."""
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        menu = QtWidgets.QMenu(self)
        menu.addMenu(self.status_menu)
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

    def onTableSelectionChanged(self):
        selection_model = self.table.selectionModel()
        selected_rows = selection_model.selectedRows()
        is_row_selected = len(selected_rows) != 0
        single_row_selected = len(selected_rows) == 1

        if single_row_selected:
            proxy_index = selected_rows[0]
            currentIndex = self.proxy_model.mapToSource(proxy_index)
            self.mapper.setCurrentModelIndex(currentIndex)

        self.action_open.setEnabled(single_row_selected)
        self.action_open_externally.setEnabled(single_row_selected)
        self.action_open_folder.setEnabled(single_row_selected)
        self.action_cite.setEnabled(single_row_selected)
        self.action_delete_rows.setEnabled(is_row_selected)
        self.action_auto_refkey.setEnabled(is_row_selected)
        self.action_setRefKey.setEnabled(is_row_selected)
        self.action_locate.setEnabled(single_row_selected)
        self.action_copy_path.setEnabled(single_row_selected)

        msg = f"[Document selected: {len(selected_rows)}]"
        status_signal.status_message.emit(msg, 5000)

    def removeRows(self):
        msgbox = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Question,
            "Delete document",
            "Are you sure you want to delete?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            self,
        )
        confirm = msgbox.exec()

        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
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
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(
            self.table.selectionModel().currentIndex()
        )
        filepath = index.sibling(index.row(), self._model.Fields.Filepath.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        open_file(filepath)

    def openFolder(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(
            self.table.selectionModel().currentIndex()
        )
        filepath = index.sibling(index.row(), self._model.Fields.Filepath.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        open_file(filepath, "folder")

    def cite(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(
            self.table.selectionModel().currentIndex()
        )
        refkey = index.sibling(index.row(), self._model.Fields.Refkey.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        title = index.sibling(index.row(), self._model.Fields.Title.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        subtitle = index.sibling(index.row(), self._model.Fields.Subtitle.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        reference = index.sibling(index.row(), self._model.Fields.Reference.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        filepath: str = index.sibling(
            index.row(), self._model.Fields.Filepath.index
        ).data(QtCore.Qt.ItemDataRole.DisplayRole)
        if filepath:
            extension = f"'{filepath.split('.')[-1]}'"

        refkey = "refkey: " + refkey if refkey != "" else None
        title = f'"{title}"'
        citation = "; ".join(
            x for x in [refkey, title, subtitle, reference, extension] if x
        )
        ClipboardExporter.toClipboard(filepath, f"[{citation}]")

    def copyPath(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(
            self.table.selectionModel().currentIndex()
        )
        filepath: str = index.sibling(
            index.row(), self._model.Fields.Filepath.index
        ).data(QtCore.Qt.ItemDataRole.DisplayRole)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(filepath)

    def locate(self):
        index: QtCore.QModelIndex = self.proxy_model.mapToSource(
            self.table.selectionModel().currentIndex()
        )
        fileid = index.sibling(index.row(), self._model.Fields.FileID.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        filepath = queryFileNameByID(fileid)

        if Path(filepath).exists():
            folder = Path(filepath).parent.as_posix()
        else:
            folder = AppDatabase.activeWorkspace().evidence_path

        filepath = QtWidgets.QFileDialog.getOpenFileName(
            caption="Locate the file...", directory=folder
        )

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
            status_signal.status_message.emit(
                "[Evidence: failed to update status]", 7000
            )
            return

        status_signal.status_message.emit("[Evidence: status updated]", 7000)

        # Force update of the table view
        self.table.viewport().update()

        if hasattr(self, "mapper"):
            self.mapper.revert()  # revert caches

    @Slot()
    def openFilterDialog(self):
        if self.filter_dialog is None:
            fields = [
                FilterField(
                    key="status",
                    label="Status",
                    column=EvidenceModel.Fields.Status.index,
                    kind=FilterKind.EXACT_LIST,
                    items=[
                        (item.name, item.name)
                        for item in AppDatabase.cache_document_status.values()
                    ],
                    widget_class=MultiCheckableComboBox,
                )
            ]

            self.filter_dialog = GenericFilterDialog(fields, self)

        button = self.toolbar.widgetForAction(self.action_open_filter_dlg)
        if button is not None:
            self.filter_dialog.popupNear(button)
            if self.filter_dialog.exec():
                for key, kwargs in self.filter_dialog.get_filters().items():
                    self.proxy_model.set_filter(key, **kwargs)

    def openById(self, id: int, anchor: str = ""):
        indexes = self._model.rowById(id)

        if indexes:
            idx = indexes[0]
            doc = self._model.getDocbyIndex(idx)
            if doc:
                self.sigOpenDocument.emit(doc, idx, anchor)

    @Slot(QtCore.QModelIndex)
    def onTableDoubleClicked(self, index: QtCore.QModelIndex):
        """
        Params: 
            index: ProxyModel's index
        """
        sidx = self.proxy_model.mapToSource(index)  # Source index
        r = sidx.row()  # row

        doc = Document(
            refkey=sidx.sibling(r, self._model.Fields.Refkey.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            title=sidx.sibling(r, self._model.Fields.Title.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            subtitle=sidx.sibling(r, self._model.Fields.Subtitle.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            reference=sidx.sibling(r, self._model.Fields.Reference.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            status=sidx.sibling(r, self._model.Fields.Status.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            type=sidx.sibling(r, self._model.Fields.Type.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            note=sidx.sibling(r, self._model.Fields.Note.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            id=sidx.sibling(r, self._model.Fields.ID.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            fileid=sidx.sibling(r, self._model.Fields.FileID.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            workspace_id=sidx.sibling(r, self._model.Fields.Workspace.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
            signage_id=sidx.sibling(r, self._model.Fields.SignageID.index).data(
                QtCore.Qt.ItemDataRole.DisplayRole
            ),
        )

        doc.filepath = sidx.sibling(r, self._model.Fields.Filepath.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )

        self.sigOpenDocument.emit(doc, sidx, "")

    @Slot()
    def searchfor(self):
        pattern = self.search_tool.text()
        cols = [
            self._model.Fields.Refkey.index,
            self._model.Fields.Status.index,
            self._model.Fields.Title.index,
            self._model.Fields.Note.index,
            self._model.Fields.Reference.index,
            self._model.Fields.Subtitle.index,
            self._model.Fields.Filepath.index,
        ]
        self.proxy_model.set_search_text(pattern, cols)

    @Slot(str)
    def onFolderFilterClicked(self, path: str):
        self.proxy_model.set_search_text(path, [self._model.Fields.Filepath.index])

    @Slot(QtCore.QModelIndex)
    def onRequestFilterClicked(self, index: QtCore.QModelIndex):
        """Filter the Evidence table on Request Refkey clicked"""
        if index.isValid():
            signage_refkey = index.sibling(
                index.row(), SignageSqlModel.Fields.Refkey.index
            ).data(Qt.ItemDataRole.DisplayRole)
            self.proxy_model.set_search_text(
                f"{signage_refkey}", [self._model.Fields.Refkey.index]
            )

    @Slot(str)
    def filterWithRefkey(self, refkey: str):
        self.proxy_model.set_search_text(f"{refkey}", [self._model.Fields.Refkey.index])

    @Slot()
    def createSignage(self):
        source = {"application": "InspectorMate", "module": "Evidence"}
        self.sigCreateSignage.emit("", source)

    @Slot()
    def createChildSignage(self):
        index = self.table.selectionModel().currentIndex()

        if not index.isValid():
            return

        sidx = self.proxy_model.mapToSource(index)
        r = sidx.row()
        signage_id = sidx.sibling(r, self._model.Fields.SignageID.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        if not signage_id:
            return

        title = sidx.sibling(r, self._model.Fields.Title.index).data(
            Qt.ItemDataRole.DisplayRole
        )
        filepath = sidx.sibling(r, self._model.Fields.Filepath.index).data(
            Qt.ItemDataRole.DisplayRole
        )
        uid = sidx.sibling(r, self._model.Fields.ID.index).data(
            Qt.ItemDataRole.DisplayRole
        )
        source = SignageOrigin(
            get_settings().APP_NAME, "Evidence", "document", title, uid, filepath
        )
        self.sigCreateChildSignage.emit(signage_id, source)

    def _on_load_ended(self, m: str = ""):
        self.sigUpdateReviewProgress.emit()
        self.stopSpinner(m)
        self.table.sortByColumn(
            EvidenceModel.Fields.Title.index, QtCore.Qt.SortOrder.AscendingOrder
        )
        self.table.sortByColumn(
            EvidenceModel.Fields.Refkey.index, QtCore.Qt.SortOrder.AscendingOrder
        )

    @Slot()
    def loadEvidence(self):
        self.startSpinner()
        self._model.insertDocumentAsync(on_finished=self._on_load_ended)

    @Slot()
    def onResetFilters(self):
        """Reset Evidence Table Filters"""
        self.proxy_model.clear_filters()
        self.table.sortByColumn(
            self._model.Fields.Refkey.index, QtCore.Qt.SortOrder.AscendingOrder
        )

        self.search_tool.clear()

        if self.filter_dialog is not None:
            self.filter_dialog.resetFields()

    def restoreTableColumnWidth(self):
        """Restore table column width upon GUI initialization"""
        settings = get_settings()
        for column in range(self._model.columnCount()):
            width = settings.get_column_width("evidence", column)
            self.table.setColumnWidth(column, width)

    def saveTableColumnWidth(self):
        """Save table column width upon closing"""
        settings = get_settings()
        for column in range(self._model.columnCount()):
            width = self.table.columnWidth(column)
            settings.set_column_width("evidence", column, width)

    @Slot()
    def refresh(self):
        self._model.refresh()
        self.doc_filter.set_root_path(AppDatabase.activeWorkspace().evidence_path)
        self.onResetFilters()

    def closeEvent(self, a0):
        self.saveTableColumnWidth()
        self.signage_filter.close()
        self.mapper.submit()
        return super().closeEvent(a0)
