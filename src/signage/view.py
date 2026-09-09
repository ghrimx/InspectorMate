import logging
from ast import literal_eval
from base64 import b64decode
from functools import partial

from my_pyqt_widgets import FitContentTextEdit, MultiCheckableComboBox, ReadOnlyLineEdit, DatePickerWidget
from pyqt6_richtexteditor import RichTextEdit
from qt_theme_manager import Theme, theme_icon_manager

from base_delegates import CompositeDelegate, NoteColumnDelegate
from common import ConnectorType, Signage, SignageOrigin, SignageStatus
from database.database import AppDatabase
from qtpy import Qt, QtCore, QtGui, QtSql, QtWidgets, Signal, Slot
from signage.connector_model import ConnectorModel
from signage.dialogs import ExportDialog, ImportDialog, SignageDialog
from signage.model import DataService, SignageModel, SignageSqlModel
from signage.signage_style import DARK_TABLE_STYLE, TABLE_STYLE
from utilities.decorators import status_signal
from utilities.settings import get_settings
from utilities.utils import open_file
from widgets.basetab import BaseTab
from widgets.generic_filter_dialog import FilterField, GenericFilterDialog
from widgets.generic_proxymodel import FilterKind, GenericFilterProxyModel

logger = logging.getLogger(__name__)


class TypeDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def initStyleOption(
        self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ):
        super().initStyleOption(option, index)
        title = index.data(Qt.ItemDataRole.DisplayRole)
        sqlmodel: SignageSqlModel = index.model().sourceModel().rootModel()
        fk_col = SignageSqlModel.Fields.Type.index
        relation: QtSql.QSqlRelation = sqlmodel.relation(fk_col)
        relmodel: QtSql.QSqlTableModel = sqlmodel.relationModel(fk_col)

        if not relation or relmodel is None:
            return

        img64str = None
        display_value = index.sibling(
            index.row(), SignageSqlModel.Fields.Type.index
        ).data(QtCore.Qt.ItemDataRole.DisplayRole)
        for r in range(relmodel.rowCount()):
            rec = relmodel.record(r)
            if rec.value(relation.displayColumn()) == display_value:
                img64str = rec.value("icon")
                break

        pix = QtGui.QPixmap()

        if img64str is not None:
            try:
                icon_bytearray = b64decode(img64str)
            except Exception as e:
                logger.debug(e)
            else:
                pix.loadFromData(icon_bytearray)

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = QtGui.QIcon(pix)
        option.text = title


class StatusColorDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def initStyleOption(
        self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ) -> None:
        super().initStyleOption(option, index)

        color_value = None
        display_status = index.sibling(
            index.row(), SignageSqlModel.Fields.Status.index
        ).data(QtCore.Qt.ItemDataRole.DisplayRole)

        if not display_status:
            return

        status_object: SignageStatus = AppDatabase.cache_signage_status.get(
            display_status
        )

        if status_object:
            color_value = status_object.color

        if color_value == "#000000" and theme_icon_manager.get_theme() == Theme.DARK:
            color_value = theme_icon_manager.get_theme_color().name(
                QtGui.QColor.NameFormat.HexRgb
            )

        if color_value:
            option.palette.setColor(
                QtGui.QPalette.ColorRole.Text, QtGui.QColor(color_value)
            )


class CellBackgroundDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        color: str = index.sibling(
            index.row(), SignageSqlModel.Fields.Background.index
        ).data(Qt.ItemDataRole.DisplayRole)

        if color:
            painter.save()
            painter.fillRect(option.rect, QtGui.QColor(color))
            painter.restore()

        super().paint(painter, option, index)


# TODO: see CellBackgroundDelegate
class RoundedColorDotDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        # Only paint dot in the first column
        if index.column() != 0:
            super().paint(painter, option, index)
            return

        # Get color from model (Qt.UserRole + 1 for example)
        color: str = index.sibling(
            index.row(), SignageSqlModel.Fields.Background.index
        ).data(Qt.ItemDataRole.DisplayRole)
        if color.strip() == "":
            super().paint(painter, option, index)
            return

        color = QtGui.QColor(color)

        painter.save()

        # Draw the default item (text)
        super().paint(painter, option, index)

        if not color:
            painter.restore()
            return

        # Determine dot size & position
        rect = option.rect
        padding = 2
        diameter = min(rect.height() - 2 * padding, 12)  # max ~12 px
        radius = diameter / 2

        center_x = rect.right() - padding - radius
        center_y = rect.y() + rect.height() / 2

        # Draw circle
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(color)
        painter.setPen(QtGui.QPen(QtGui.QColor("#202020"), 1))

        painter.drawEllipse(QtCore.QPointF(center_x, center_y), radius, radius)

        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 18))  # Ensure space for dot
        return size


class VirtualProgressBarDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(
        self, painter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ):
        percentage = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        total = index.sibling(index.row(), SignageSqlModel.Fields.DocCount.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )

        try:
            progress = int(percentage)
        except (ValueError, TypeError):
            return  # skip invalid values

        if percentage >= 0 and total > 0:
            progress = int(percentage)
            progressBarOption = QtWidgets.QStyleOptionProgressBar()
            progressBarOption.rect = option.rect
            progressBarOption.minimum = 0
            progressBarOption.maximum = 100
            progressBarOption.progress = progress
            progressBarOption.text = f"{progress}%"
            progressBarOption.textVisible = True
            progressBarOption.state |= QtWidgets.QStyle.StateFlag.State_Horizontal

            QtWidgets.QApplication.style().drawControl(
                QtWidgets.QStyle.ControlElement.CE_ProgressBar,
                progressBarOption,
                painter,
            )
        else:
            opt = QtWidgets.QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            opt.text = ""
            style = (
                QtWidgets.QApplication.style()
                if opt.widget is None
                else opt.widget.style()
            )
            style.drawControl(
                QtWidgets.QStyle.ControlElement.CE_ItemViewItem, opt, painter
            )


#################################################################
#                       SignageTab
#################################################################

class SignageTab(BaseTab):
    sigSignageDoubleClicked = Signal(str)
    sigOpenNote = Signal(str, str)
    sigOpenEvidence = Signal(int, str)

    def __init__(
        self,
        model: SignageModel,
        startSpinner: callable | None = None,
        stopSpinner: callable | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.model = model
        self.proxymodel = GenericFilterProxyModel(self.model)
        self.startSpinner = startSpinner
        self.stopSpinner = stopSpinner
        self.initUI()
        self.createAction()

    def initUI(self):
        # --- Left Pane ---
        self.left_pane.hide()
        self.toolbar.removeAction(self.fold_left_pane)

        # --- Table ---
        self.table = QtWidgets.QTreeView(self)
        self.table.setAlternatingRowColors(False)
        self.table.setModel(self.proxymodel)
        # self.table.header().sortIndicatorChanged.connect(self.proxymodel.sortTree)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )  # ReadOnly
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.sortByColumn(
            SignageSqlModel.Fields.ID.index, QtCore.Qt.SortOrder.AscendingOrder
        )

        if theme_icon_manager.get_theme() == Theme.DARK:
            self.table.setStyleSheet(DARK_TABLE_STYLE)
        else:
            self.table.setStyleSheet(TABLE_STYLE)

        for field in SignageSqlModel.Fields.fields():
            if not field.visible:
                self.table.hideColumn(field.index)

        # Table's connections
        self.table.selectionModel().selectionChanged.connect(self.onTableSelectionChanged)
        self.table.doubleClicked.connect(self.onTableDoubleClicked)

        # Table's delegates
        type_delegate = TypeDelegate(self.table)
        note_delegate = NoteColumnDelegate(self.table)
        public_note_delegate = NoteColumnDelegate(self.table, True)
        status_delegate = StatusColorDelegate(self.table)
        cell_color_delegate = CellBackgroundDelegate(self.table)
        self.progress_delegate = VirtualProgressBarDelegate(self.table)

        self.table.setItemDelegate(status_delegate)
        self.table.setItemDelegateForColumn(
            SignageSqlModel.Fields.Refkey.index, cell_color_delegate
        )
        self.table.setItemDelegateForColumn(
            SignageSqlModel.Fields.Note.index, note_delegate
        )
        self.table.setItemDelegateForColumn(
            SignageSqlModel.Fields.PublicNote.index, public_note_delegate
        )
        self.table.setItemDelegateForColumn(
            SignageSqlModel.Fields.Progress.index, self.progress_delegate
        )

        combo_delegate = CompositeDelegate([status_delegate, type_delegate], self.table)
        self.table.setItemDelegateForColumn(
            SignageSqlModel.Fields.Title.index, combo_delegate
        )

        # --- Right Pane ---
        self.title_textedit = FitContentTextEdit(False)
        self.title_textedit.setAcceptRichText(False)

        self.status_combobox = QtWidgets.QComboBox()
        for key, item in AppDatabase.cache_signage_status.items():
            self.status_combobox.insertItem(key, item.name, item)

        self.refkey_field = QtWidgets.QLineEdit()
        self.type_line = ReadOnlyLineEdit()
        self.owner_lineinput = QtWidgets.QLineEdit()
        self.source_label = FitContentTextEdit(True)
        self.source_label.setStyleSheet("color: grey;")

        self.evidence_label = ReadOnlyLineEdit()
        self.id_label = ReadOnlyLineEdit()
        self.parentid_label = ReadOnlyLineEdit()
        self.creation_date = ReadOnlyLineEdit()
        self.due_date_edit = DatePickerWidget()

        # Private & Public Note
        self.note = RichTextEdit(":memory", ":memory", "")

        private_note_layout = QtWidgets.QVBoxLayout()
        private_note_widget = QtWidgets.QWidget()
        private_note_widget.setLayout(private_note_layout)
        to_private = QtWidgets.QPushButton(
            theme_icon_manager.get_icon(":share-forward-2-line"), "Sent to private note"
        )

        to_private.clicked.connect(self.sentToPrivate)
        private_note_layout.addWidget(to_private)
        self.public_note = RichTextEdit(":memory", ":memory", "")
        self.public_note.setStyleSheet("border: 2px solid red;")
        private_note_layout.addWidget(self.public_note)

        formlayout = QtWidgets.QFormLayout()
        info_widget = QtWidgets.QWidget()
        info_widget.setLayout(formlayout)
        formlayout.addRow("Title", self.title_textedit)
        formlayout.addRow("Refkey", self.refkey_field)
        formlayout.addRow("Status", self.status_combobox)
        formlayout.addRow("Type", self.type_line)
        formlayout.addRow("Owner", self.owner_lineinput)
        formlayout.addRow("Source", self.source_label)
        formlayout.addRow("Evidence", self.evidence_label)
        formlayout.addRow("ID", self.id_label)
        formlayout.addRow("ParentID", self.parentid_label)
        formlayout.addRow("Creation date", self.creation_date)
        formlayout.addRow("Due date", self.due_date_edit)

        spacer = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        formlayout.addItem(spacer)
        self.right_pane.addTab(info_widget, "Info")
        self.right_pane.addTab(
            self.note, theme_icon_manager.get_icon(":lock-2"), "Private Note"
        )
        self.right_pane.addTab(
            private_note_widget,
            theme_icon_manager.get_icon(":glasses-2"),
            "Public Note",
        )

        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setItemDelegate(QtSql.QSqlRelationalDelegate(self))
        self.mapper.addMapping(
            self.status_combobox, SignageSqlModel.Fields.Status.index
        )
        self.mapper.addMapping(
            self.title_textedit, SignageSqlModel.Fields.Title.index, b"plainText"
        )
        self.mapper.addMapping(self.refkey_field, SignageSqlModel.Fields.Refkey.index)
        self.mapper.addMapping(self.type_line, SignageSqlModel.Fields.Type.index)
        self.mapper.addMapping(self.owner_lineinput, SignageSqlModel.Fields.Owner.index)
        self.mapper.addMapping(
            self.source_label, SignageSqlModel.Fields.Source.index, b"plainText"
        )
        self.mapper.addMapping(
            self.due_date_edit, SignageSqlModel.Fields.DueDate.index, b"isoDate"
        )
        self.mapper.addMapping(self.note, SignageSqlModel.Fields.Note.index)
        self.mapper.addMapping(
            self.public_note, SignageSqlModel.Fields.PublicNote.index
        )
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)

        self.refkey_field.editingFinished.connect(self.updateReviewProgess)
        self.refkey_field.editingFinished.connect(
            AppDatabase.update_document_signage_id
        )
        self.due_date_edit.sigDateSelected.connect(self.mapper.submit)

        # --- Dialogs ---
        self.signage_dialog: SignageDialog = None
        self.export_dialog: ExportDialog = None
        self.import_dialog: ImportDialog = None
        self.filter_dialog: GenericFilterDialog = None

        # --- Layout ---
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.right_pane)
        self.splitter.setSizes([0, 800, 100])

        # Restore view geometry
        self.restoreTableColumnWidth()

        # --- Connections ---
        self.search_tool.textChanged.connect(self.searchfor)

        self.model.updateReviewProgess()

    def createAction(self):

        self.action_create_child_signage = self.toolbar.add_action(
            "create_child_signage",
            "Create Child Signage",
            self._createChildSignage,
            theme_icon_manager.get_icon(":signpost-line-child"),
            "Ctrl+H",
            context=Qt.ShortcutContext.WindowShortcut,
            before="spacer",
        )
        self.action_delete_signage = self.toolbar.add_action(
            "delete_signage",
            "Delete Signage",
            self.deleteRow,
            theme_icon_manager.get_icon(":delete-bin2"),
            before="spacer",
        )

        self.action_filtering = self.toolbar.add_action(
            "filter_signage",
            "Filters",
            self.openFilterDialog,
            theme_icon_manager.get_icon(":filter-line"),
            before="spacer",
        )

        self.reset_filtering = self.toolbar.add_action(
            "reset_filter",
            "Reset Filters",
            self.onResetFilters,
            theme_icon_manager.get_icon(":filter-off-line"),
            before="spacer",
        )

        self.action_expandAll = self.toolbar.add_action(
            "expand_all",
            "Expand All",
            self.table.expandAll,
            theme_icon_manager.get_icon(":expand-vertical-line"),
            before="spacer",
        )

        self.action_collapseAll = self.toolbar.add_action(
            "collapse_all",
            "Collapse All",
            self.table.collapseAll,
            theme_icon_manager.get_icon(":collapse-vertical-line"),
            before="spacer",
        )

        self.action_cite = self.toolbar.add_action(
            "cite",
            "Cite",
            self.cite,
            theme_icon_manager.get_icon(":double-quotes"),
            "Ctrl+C",
            context=Qt.ShortcutContext.WindowShortcut,
            tooltip="Copy to clipboard the Signage refkey and its title",
            before="spacer",
        )

        self.action_reach_source = self.toolbar.add_action(
            "go_to_source",
            "Go to Source",
            self.reachSource,
            theme_icon_manager.get_icon(":share-forward-2-line"),
            before="spacer",
        )

        self.action_highlight = self.toolbar.add_action(
            "highlight",
            "Highlight",
            self.colorCell,
            theme_icon_manager.get_icon(":mark_pen"),
            before="spacer",
        )
        
        self.connector_menu = QtWidgets.QMenu(self.toolbar)
        for c in ConnectorType:
            action = self.connector_menu.addAction(c.name)
            slot_func = partial(self.importFromConnector, c)
            action.triggered.connect(slot_func)

        self.toolbar.add_button(
            "import_from_connector",
            "Import from connector",
            None,
            icon=theme_icon_manager.get_icon(":links-line"),
            menu=self.connector_menu,
            popup_mode=QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup,
            before="spacer",
        )

        # Status menu
        self.status_menu = QtWidgets.QMenu("Status", self)
        status_type: SignageStatus
        for status_type in AppDatabase.cache_signage_status.values():
            action = self.status_menu.addAction(status_type.name)
            slot_func = partial(self.setStatus, status_type.name)
            action.triggered.connect(slot_func)

        # Owner menu
        self.owner_menu = QtWidgets.QMenu("Owner", self)
        owners: list = get_settings().get_owners()
        for owner in owners:
            action = self.owner_menu.addAction(owner)
            slot_func = partial(self.updateOwner, owner)
            action.triggered.connect(slot_func)

    def _refresh_readonly_labels(self, idx: QtCore.QModelIndex) -> None:
        if not idx.isValid():
            return

        id_value = idx.sibling(idx.row(), SignageSqlModel.Fields.ID.index).data()
        parent_id = idx.sibling(idx.row(), SignageSqlModel.Fields.ParentID.index).data()
        creation_datetime = idx.sibling(idx.row(), SignageSqlModel.Fields.CreationDatetime.index).data()
        doc_count = idx.sibling(idx.row(), SignageSqlModel.Fields.DocCount.index).data()
        
        self.id_label.setText(str(id_value) or "-")
        self.parentid_label.setText(str(parent_id) or "-")
        self.creation_date.setText(creation_datetime)
        self.evidence_label.setText(str(doc_count) or "-")

    def onTableSelectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        selection_model = self.table.selectionModel()
        selected_rows = selection_model.selectedRows()
        single_row_selected = len(selected_rows) == 1

        if single_row_selected:
            proxy_index = selected_rows[0]
            currentIndex = self.proxymodel.mapToSource(proxy_index)
            self.mapper.setRootIndex(currentIndex.parent())
            self.mapper.setCurrentModelIndex(currentIndex)
            self._refresh_readonly_labels(currentIndex)

        self.action_delete_signage.setEnabled(single_row_selected)
        self.action_create_child_signage.setEnabled(single_row_selected)
        self.action_highlight.setEnabled(single_row_selected)
        self.action_cite.setEnabled(single_row_selected)
        self.action_reach_source.setEnabled(single_row_selected)
        self.status_menu.setEnabled(single_row_selected)
        self.owner_menu.setEnabled(single_row_selected)

        msg = f"[Signage selected: {len(selected_rows)}]"
        status_signal.status_message.emit(msg, 5000)

    def show_table_context_menu(self, pos: QtCore.QPoint):
        """Triggered when user right-clicks on the table."""
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        if len(self.table.selectionModel().selectedRows()) != 1:
            return

        menu = QtWidgets.QMenu(self)
        menu.addMenu(self.status_menu)
        menu.addMenu(self.owner_menu)
        menu.addAction(self.action_create_child_signage)
        menu.addAction(self.action_delete_signage)
        menu.addAction(self.action_cite)
        menu.addAction(self.action_reach_source)
        menu.addAction(self.action_highlight)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _selectedProxyToSource(self) -> QtCore.QModelIndex:
        proxy_index = self.table.selectionModel().currentIndex()
        if not proxy_index.isValid():
            return
        source_index = self.proxymodel.mapToSource(proxy_index)
        if not source_index.isValid():
            return
        return source_index

    @Slot(QtCore.QModelIndex)
    def onTableDoubleClicked(self, index: QtCore.QModelIndex):
        signage_type = index.sibling(
            index.row(), SignageSqlModel.Fields.Type.index
        ).data(QtCore.Qt.ItemDataRole.DisplayRole)

        if signage_type != AppDatabase.cache_signage_type.get("Request").name:
            return

        refkey = index.sibling(index.row(), SignageSqlModel.Fields.Refkey.index).data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )
        self.sigSignageDoubleClicked.emit(refkey)

    @Slot()
    def setStatus(self, status_id):
        source_index = self._selectedProxyToSource()
        if not source_index:
            return
        status_index = source_index.sibling(
            source_index.row(), SignageSqlModel.Fields.Status.index
        )
        self.model.setData(status_index, status_id, Qt.ItemDataRole.EditRole)

    def updateReviewProgess(self):
        """Update Progressbar

        Delay the refresh to allow the database to commit the changes
        """
        QtCore.QTimer.singleShot(1000, self.model.updateReviewProgess)

    @Slot()
    def updateOwner(self, owner: str):
        source_index = self._selectedProxyToSource()
        if not source_index:
            return
        owner_index = source_index.sibling(
            source_index.row(), SignageSqlModel.Fields.Owner.index
        )
        self.model.setData(owner_index, owner, Qt.ItemDataRole.EditRole)

    @Slot()
    def openSignageDialog(self, title):
        """
        Open the signage dialog
        data: [title, source]
        """
        if self.signage_dialog is None:
            self.signage_dialog = SignageDialog(parent=None)

        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.updateRefkeyField()
        self.signage_dialog.signage_title_lineedit.setText(title)
        self.signage_dialog.signage_title_lineedit.setFocus()

        result = self.signage_dialog.exec()
        return result

    @Slot(str, dict)
    def createSignage(self, signage_origin: SignageOrigin, title: str = ""):
        """Create Parent Signage"""
        if self.signage_dialog is None:
            self.signage_dialog = SignageDialog(parent=None)

        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.updateRefkeyField()
        self.signage_dialog.signage_title_lineedit.setText(title)
        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.parent_signage_id.clear()
        self.signage_dialog.parent_signage_refkey.clear()
        self.signage_dialog.parent_signage_widget.setVisible(False)

        if not self.signage_dialog.exec():
            return False

        # Get signage from the dialog
        signage = self.signage_dialog.signage()
        signage.source = signage_origin.as_str()

        # Insert signage into the database and into the model
        if self.model.insertSignage(signage=signage):
            status_signal.status_message.emit("✔️ Signage created", 7000)
            self.updateReviewProgess()
            return True
        else:
            status_signal.status_message.emit("⚠️ Fail to create Signage", 7000)
            return False

    @Slot(int, object)
    def createChildSignage(self, parent_id: str, signage_origin: SignageOrigin):
        """Create Child Signage"""
        if self.signage_dialog is None:
            self.signage_dialog = SignageDialog(parent=None)

        parent_index = self.model.findIndexById(
            int(parent_id), SignageSqlModel.Fields.ID.index
        )
        if not parent_index:
            return
        parent_refkey = parent_index.sibling(
            parent_index.row(), SignageSqlModel.Fields.Refkey.index
        ).data(QtCore.Qt.ItemDataRole.DisplayRole)

        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.updateRefkeyField()
        self.signage_dialog.signage_title_lineedit.clear()
        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.parent_signage_id.setText(
            "" if parent_id is None else str(parent_id)
        )
        self.signage_dialog.parent_signage_refkey.setText(
            "" if parent_refkey is None else str(parent_refkey)
        )
        self.signage_dialog.parent_signage_widget.setVisible(True)

        if not self.signage_dialog.exec():
            return

        signage = self.signage_dialog.signage()
        signage.parentID = parent_id
        signage.source = signage_origin.as_str()
        if self.model.insertSignage(signage=signage):
            status_signal.status_message.emit("✔️ Signage created", 7000)
            self.updateReviewProgess()
            return True
        else:
            status_signal.status_message.emit("⚠️ Fail to create Signage", 7000)
            return False

    def _createChildSignage(self):
        index = self.table.selectionModel().currentIndex()
        source_index = self.proxymodel.mapToSource(index)

        parent_id = source_index.sibling(
            source_index.row(), SignageSqlModel.Fields.ID.index
        ).data(QtCore.Qt.ItemDataRole.DisplayRole)
        signage_orginine = SignageOrigin(get_settings().APP_NAME, "Signage")
        self.createChildSignage(parent_id, signage_orginine)

    @Slot()
    def deleteRow(self) -> None:
        """Trigger Delete row from the QSqlTableModel and TreeModel"""
        index: QtCore.QModelIndex = self.table.selectionModel().currentIndex()
        source_index = self.proxymodel.mapToSource(index)
        if self.model.deleteRow(source_index):
            AppDatabase.update_document_signage_id()
            status_signal.status_message.emit("✔️ Signage deleted", 7000)
        else:
            status_signal.status_message.emit("⚠️ Fail to delete Signage", 7000)

    @Slot(str)
    def searchfor(self, text: str):
        cols = [
            SignageSqlModel.Fields.Refkey.index,
            SignageSqlModel.Fields.Status.index,
            SignageSqlModel.Fields.Title.index,
            SignageSqlModel.Fields.Note.index,
            SignageSqlModel.Fields.PublicNote.index,
            SignageSqlModel.Fields.Owner.index,
            SignageSqlModel.Fields.Source.index,
        ]
        self.proxymodel.set_search_text(text, cols)

    @Slot()
    def openFilterDialog(self):
        if self.filter_dialog is None:
            fields = [
                FilterField(
                    key="status",
                    label="Status",
                    column=SignageSqlModel.Fields.Status.index,
                    kind=FilterKind.EXACT_LIST,
                    items=[
                        (item.name, item.name)
                        for item in AppDatabase.cache_signage_status.values()
                    ],
                    widget_class=MultiCheckableComboBox,
                ),
                FilterField(
                    key="type",
                    label="Type",
                    column=SignageSqlModel.Fields.Type.index,
                    kind=FilterKind.EXACT_LIST,
                    items=[
                        (item.name, item.name)
                        for item in AppDatabase.cache_signage_type.values()
                    ],
                    widget_class=MultiCheckableComboBox,
                ),
                FilterField(
                    key="owner",
                    label="Owner",
                    column=SignageSqlModel.Fields.Owner.index,
                    kind=FilterKind.EXACT_LIST,
                    items=[(item, item) for item in get_settings().get_owners()],
                    widget_class=MultiCheckableComboBox,
                ),
                FilterField(
                    key="doc",
                    label="Evidence",
                    column=SignageSqlModel.Fields.DocCount.index,
                    kind=FilterKind.TRISTATE_BOOL,
                    items=[
                        ("all", QtCore.Qt.CheckState.PartiallyChecked),
                        ("without", QtCore.Qt.CheckState.Unchecked),
                        ("with only", QtCore.Qt.CheckState.Checked),
                    ],
                ),
            ]

            self.filter_dialog = GenericFilterDialog(fields, self)

        button = self.toolbar.widgetForAction(self.action_filtering)
        if button is not None:
            self.filter_dialog.popupNear(button)
            if self.filter_dialog.exec():
                for key, kwargs in self.filter_dialog.get_filters().items():
                    self.proxymodel.set_filter(key, **kwargs)

    @Slot()
    def onResetFilters(self):
        """Reset Signage Table Filters"""
        self.search_tool.clear()
        self.proxymodel.clear_filters()

        if self.filter_dialog is not None:
            self.filter_dialog.resetFields()

    def _on_signage_ready(self, signage: Signage):
        self.model.insertSignage(signage=signage)

    def _on_load_connector_finished(self, cache, msg=""):
        """Called after batch insert"""
        self.model.connector_cache = cache
        self.stopSpinner(msg)
        AppDatabase.update_document_signage_id()
        self.updateReviewProgess()

    def importFromConnector(self, connector_type: ConnectorType):
        connectors: dict = ConnectorModel.connectors().get(connector_type.value)

        if not connectors:
            QtWidgets.QMessageBox.information(self, "Connector", "No connector defined!")
            return

        regex = get_settings().get_signage_pattern()

        self.startSpinner()
        if connector_type == ConnectorType.DOCX:
            DataService.loadFromDocx(
                connectors=connectors,
                regex=regex,
                cache=self.model.connector_cache,
                on_ready=self._on_signage_ready,
                on_finished=self._on_load_connector_finished,
            )
        elif connector_type == ConnectorType.ONENOTE:
            DataService.loadFromOneNote(
                connectors=connectors,
                regex=regex,
                cache=self.model.connector_cache,
                on_ready=self._on_signage_ready,
                on_finished=self._on_load_connector_finished,
            )

    def cite(self):
        index: QtCore.QModelIndex = self.table.selectionModel().currentIndex()

        if not index.isValid():
            return

        src_index = self.proxymodel.mapToSource(index)
        refkey_idx = src_index.sibling(
            src_index.row(), SignageSqlModel.Fields.Refkey.index
        )
        refkey = self.model.data(refkey_idx, Qt.ItemDataRole.DisplayRole)
        type_idx = src_index.sibling(src_index.row(), SignageSqlModel.Fields.Type.index)
        type = self.model.data(type_idx, Qt.ItemDataRole.DisplayRole)
        title_idx = src_index.sibling(
            src_index.row(), SignageSqlModel.Fields.Title.index
        )
        title = self.model.data(title_idx, Qt.ItemDataRole.DisplayRole)

        citation = f"{type} {refkey} - {title}"
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(f"{citation}")

    def sentToPrivate(self):
        public_text = self.public_note.toHtml()
        self.note.append(public_text)

        index = self.table.selectionModel().currentIndex()
        src_index = self.proxymodel.mapToSource(index)

        public_note_index = src_index.sibling(
            src_index.row(), SignageSqlModel.Fields.PublicNote.index
        )
        private_note_index = src_index.sibling(
            src_index.row(), SignageSqlModel.Fields.Note.index
        )

        if self.model.setData(
            private_note_index, self.note.toHtml(), Qt.ItemDataRole.EditRole
        ):
            self.public_note.clear()
            self.model.setData(public_note_index, "", Qt.ItemDataRole.EditRole)

    @Slot()
    def onExportTriggered(self):
        if self.export_dialog is None:
            self.export_dialog = ExportDialog()

        if not self.export_dialog.exec():
            return

        self.startSpinner()
        DataService.export2Excel(
            self.model.rootModel(),
            self.export_dialog.export_params,
            self.stopSpinner,
        )

    @Slot()
    def onImportTriggered(self):
        if self.import_dialog is None:
            self.import_dialog = ImportDialog()

        if not self.import_dialog.exec():
            return

        selected_files = self.import_dialog.selectedFiles()
        update_title = self.import_dialog.update_title

        self.startSpinner()
        DataService.loadFromExcel(
            self.model,
            selected_files,
            update_title,
            self._on_signage_ready,
            self.stopSpinner,
        )

    def reachSource(self):
        index: QtCore.QModelIndex = self.table.selectionModel().currentIndex()

        if not index.isValid():
            return

        src_index = self.proxymodel.mapToSource(index)
        source_idx = src_index.sibling(
            src_index.row(), SignageSqlModel.Fields.Source.index
        )
        source = self.model.data(source_idx, Qt.ItemDataRole.DisplayRole)
        try:
            source_dict: dict = literal_eval(source)
        except:
            status_signal.status_message.emit("⚠️ Unable to identify the source !", 5000)
            return

        app = source_dict.get("application")
        module = source_dict.get("module")
        target = source_dict.get("target", None)
        anchor = source_dict.get("anchor", "")
        item_id = source_dict.get("item_id", None)

        if target is None:
            return

        if app == "InspectorMate" and module == "RichTextEditor":
            self.sigOpenNote.emit(target, anchor)
        elif app == "InspectorMate" and module == "DocViewer" and item_id:
            self.sigOpenEvidence.emit(item_id, anchor)
        elif app =="Ms OneNote" and module == "loadFromOnenote":
                QtGui.QDesktopServices.openUrl(QtCore.QUrl(target))
        else:
            status_signal.status_message.emit("Opening target...", 5000)
            try:
                open_file(target)
            except Exception as e:
                logger.error(e)
                status_signal.status_message.emit("⚠️ Unable to open the target!")
            else:
                status_signal.status_message.emit("Target opened!", 3000)

    def colorCell(self):
        indexes = self.table.selectedIndexes()

        if not indexes:
            return

        color: QtGui.QColor = QtWidgets.QColorDialog.getColor(QtGui.QColor(), self)
        if not color.isValid():
            return

        if (
            color.name(QtGui.QColor.NameFormat.HexRgb) == "#ffffff"
            and theme_icon_manager.get_theme() == Theme.LIGHT
        ) or (
            color.name(QtGui.QColor.NameFormat.HexRgb) == "#000000"
            and theme_icon_manager.get_theme() == Theme.DARK
        ):
            color_value = ""
        else:
            color_value = color.name(QtGui.QColor.NameFormat.HexRgb)

        for idx in indexes:
            src_idx = self.proxymodel.mapToSource(idx)
            bg_idx = src_idx.sibling(
                src_idx.row(), SignageSqlModel.Fields.Background.index
            )
            self.model.setData(bg_idx, color_value, Qt.ItemDataRole.EditRole)

    def restoreTableColumnWidth(self):
        """Restore table column width upon GUI initialization"""
        settings = get_settings()
        for column in range(self.model.columnCount()):
            width = settings.get_column_width("signage", column)
            self.table.setColumnWidth(column, width)

    def saveTableColumnWidth(self):
        """Save table column width upon closing"""
        settings = get_settings()
        for column in range(self.model.columnCount()):
            width = self.table.columnWidth(column)
            settings.set_column_width("signage", column, width)

    def closeEvent(self, a0):
        self.saveTableColumnWidth()
        self.mapper.submit()
        return super().closeEvent(a0)
