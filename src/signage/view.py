import logging
from json import loads
from base64 import b64decode
from functools import partial
from qtpy import Qt, QtGui, QtCore, Signal, Slot, QtWidgets, QtSql

from database.database import AppDatabase

from utilities import config as mconf
from utilities.config import settings
from utilities.decorators import status_signal
from utilities.utils import open_file
from common import Signage, SignageStatus, ConnectorType
from base_delegates import NoteColumnDelegate, CompositeDelegate

from signage.model import SignageModel, SignageSqlModel, SignageProxyModel, DataService
from signage.signage_style import TABLE_STYLE, DARK_TABLE_STYLE
from signage.connector_model import ConnectorModel
from signage.dialogs import SignageDialog, FilterDialog, ExportDialog, ImportDialog

from widgets.basetab import BaseTab
from widgets.richtexteditor import RichTextEditor
from widgets.fitcontenteditor import FitContentTextEdit
from widgets.readonly_linedit import ReadOnlyLineEdit


from qt_theme_manager import theme_icon_manager, Theme


logger = logging.getLogger(__name__)


class TypeDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super().initStyleOption(option, index)
        title = index.data(Qt.ItemDataRole.DisplayRole)
        sqlmodel: SignageSqlModel = index.model().sourceModel().rootModel()
        fk_col = SignageSqlModel.Fields.Type.index
        relation: QtSql.QSqlRelation = sqlmodel.relation(fk_col)
        relmodel: QtSql.QSqlTableModel = sqlmodel.relationModel(fk_col)

        if not relation or relmodel is None:
            return

        img64str = None
        display_value = index.sibling(index.row(), SignageSqlModel.Fields.Type.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        for r in range(relmodel.rowCount()):
            rec = relmodel.record(r)
            if rec.value(relation.displayColumn()) == display_value:
                img64str = rec.value("icon")
                break

        pix = QtGui.QPixmap()

        if img64str is not None:
            try:
                icon_bytearray = b64decode(img64str)
            except:
                pass
            else:
                pix.loadFromData(icon_bytearray)

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = QtGui.QIcon(pix)
        option.text = title


class StatusColorDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)

        color_value = None
        display_status = (index.sibling(index.row(),
                                       SignageSqlModel.Fields.Status.index)
                                       .data(QtCore.Qt.ItemDataRole.DisplayRole))
        
        if not display_status:
            return

        status_object: SignageStatus = AppDatabase.cache_signage_status.get(display_status)
        
        if status_object:
            color_value = status_object.color

        if color_value == "#000000" and theme_icon_manager.get_theme() == Theme.DARK:
            color_value = theme_icon_manager.get_theme_color().name(QtGui.QColor.NameFormat.HexRgb)
        
        if color_value:
            option.palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(color_value))


class VirtualProgressBarDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
            
    def paint(self, painter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        percentage = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        total = index.sibling(index.row(), SignageSqlModel.Fields.DocCount.index).data(QtCore.Qt.ItemDataRole.DisplayRole)

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

            QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.ControlElement.CE_ProgressBar,
                                                        progressBarOption,
                                                        painter)
        else:
            opt = QtWidgets.QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            opt.text = ""  
            style = QtWidgets.QApplication.style() if opt.widget is None else opt.widget.style()
            style.drawControl(QtWidgets.QStyle.ControlElement.CE_ItemViewItem, opt, painter)



#################################################################
#                       SignageTab
#################################################################

class SignageTab(BaseTab):
    sigSignageDoubleClicked = Signal(str)
    sigOpenNote = Signal(str, str)

    def __init__(self,
                 model: SignageModel,
                 startSpinner: callable = None,
                 stopSpinner: callable = None,
                 parent=None):
        super(SignageTab, self).__init__(parent)
        self.model = model
        self.proxymodel = SignageProxyModel(self.model)
        self.proxymodel.setDynamicSortFilter(False)
        self.startSpinner = startSpinner
        self.stopSpinner = stopSpinner
        self.createAction()
        self.initUI()

    def signageSource(self) -> str:
        return '{"application":"InspectorMate", "module":"Signage"}'

    def initUI(self):
        # --- Left Pane ---
        self.left_pane.hide()
        self.toolbar.removeAction(self.fold_left_pane)

        # --- Table ---
        self.table = QtWidgets.QTreeView(self)
        self.table.setAlternatingRowColors(False)
        self.table.setModel(self.proxymodel)
        # self.table.header().sortIndicatorChanged.connect(self.table.model().sortTree)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers) # ReadOnly
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.sortByColumn(SignageSqlModel.Fields.ID.index,
                                QtCore.Qt.SortOrder.AscendingOrder)

        if theme_icon_manager.get_theme() == Theme.DARK:
            self.table.setStyleSheet(DARK_TABLE_STYLE)
        else:
            self.table.setStyleSheet(TABLE_STYLE)

        for field in SignageSqlModel.Fields.fields():
            if not field.visible:
                self.table.hideColumn(field.index)

        # Table's connections
        self.table.clicked.connect(self.onCellClicked)
        self.table.selectionModel().selectionChanged.connect(self.updateAction)
        self.table.doubleClicked.connect(self.onTableDoubleClicked)

        # Table's delegates
        type_delegate = TypeDelegate(self.table)
        note_delegate = NoteColumnDelegate(self.table)
        public_note_delegate = NoteColumnDelegate(self.table, True)
        status_delegate = StatusColorDelegate(self.table)
        self.progress_delegate = VirtualProgressBarDelegate(self.table)

        self.table.setItemDelegate(status_delegate)
        self.table.setItemDelegateForColumn(SignageSqlModel.Fields.Note.index, note_delegate)
        self.table.setItemDelegateForColumn(SignageSqlModel.Fields.PublicNote.index, public_note_delegate)
        self.table.setItemDelegateForColumn(SignageSqlModel.Fields.Progress.index, self.progress_delegate)

        combo_delegate = CompositeDelegate([status_delegate, type_delegate], self.table)
        self.table.setItemDelegateForColumn(SignageSqlModel.Fields.Title.index, combo_delegate)

        # --- Right Pane ---
        self.title_textedit = FitContentTextEdit(False)
        self.title_textedit.setAcceptRichText(False)

        self.status_combobox = QtWidgets.QComboBox()
        for key, item in AppDatabase.cache_signage_status.items():
            self.status_combobox.insertItem(key, item.name, item)

        self.refkey_field = QtWidgets.QLineEdit()
        self.type_line = ReadOnlyLineEdit()
        self.owner_lineinput= QtWidgets.QLineEdit()
        self.source_label = FitContentTextEdit(True)
        self.source_label.setStyleSheet("color: grey;")

        self.evidence_label = ReadOnlyLineEdit()
        self.id_label = ReadOnlyLineEdit()
        self.parentid_label = ReadOnlyLineEdit()
        self.creation_date = ReadOnlyLineEdit()

        # Private & Public Note
        self.note = RichTextEditor.fromMapper(bar=False, parent=self)

        private_note_layout = QtWidgets.QVBoxLayout()
        private_note_widget = QtWidgets.QWidget()
        private_note_widget.setLayout(private_note_layout)
        to_private = QtWidgets.QPushButton(theme_icon_manager.get_icon(':share-forward-2-line'),
                                           "Sent to private note")
        
        to_private.clicked.connect(self.sentToPrivate)
        private_note_layout.addWidget(to_private)
        self.public_note = RichTextEditor.fromMapper(bar=False, parent=self)
        self.public_note.editor.setStyleSheet("border: 2px solid red;")
        private_note_layout.addWidget(self.public_note)

        formlayout = QtWidgets.QFormLayout()
        info_widget = QtWidgets.QWidget()
        info_widget.setLayout(formlayout)
        formlayout.addRow('Title', self.title_textedit)
        formlayout.addRow('Refkey', self.refkey_field)
        formlayout.addRow('Status', self.status_combobox)
        formlayout.addRow('Type', self.type_line)
        formlayout.addRow('Owner', self.owner_lineinput)
        formlayout.addRow('Source', self.source_label)
        formlayout.addRow('Evidence', self.evidence_label)
        formlayout.addRow('id', self.id_label)
        formlayout.addRow('Creation date', self.creation_date)

        spacer = QtWidgets.QSpacerItem(20,
                                       40,
                                       QtWidgets.QSizePolicy.Policy.Minimum,
                                       QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)
        self.right_pane.addTab(info_widget, "Info")
        self.right_pane.addTab(self.note, theme_icon_manager.get_icon(':lock-2'), "Private Note")
        self.right_pane.addTab(private_note_widget, theme_icon_manager.get_icon(':glasses-2'), "Public Note")

        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setItemDelegate(QtSql.QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.status_combobox, SignageSqlModel.Fields.Status.index)
        self.mapper.addMapping(self.title_textedit, SignageSqlModel.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.refkey_field, SignageSqlModel.Fields.Refkey.index)
        self.mapper.addMapping(self.type_line, SignageSqlModel.Fields.Type.index)
        self.mapper.addMapping(self.owner_lineinput, SignageSqlModel.Fields.Owner.index)
        self.mapper.addMapping(self.source_label, SignageSqlModel.Fields.Source.index, b"plainText")
        self.mapper.addMapping(self.evidence_label, SignageSqlModel.Fields.DocCount.index)
        self.mapper.addMapping(self.id_label, SignageSqlModel.Fields.ID.index)
        self.mapper.addMapping(self.parentid_label, SignageSqlModel.Fields.ParentID.index)
        self.mapper.addMapping(self.creation_date, SignageSqlModel.Fields.CreationDatetime.index)
        self.mapper.addMapping(self.note.editor, SignageSqlModel.Fields.Note.index)
        self.mapper.addMapping(self.public_note.editor, SignageSqlModel.Fields.PublicNote.index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)

        self.refkey_field.editingFinished.connect(self.updateReviewProgess)
        self.refkey_field.editingFinished.connect(AppDatabase.update_document_signage_id)

        # --- Toolbar ---
        self.toolbar.insertAction(self.action_separator, self.action_create_signage)
        self.toolbar.insertAction(self.action_separator, self.action_create_child_signage)
        self.toolbar.insertAction(self.action_separator, self.toolbar.addSeparator())
        self.toolbar.insertAction(self.action_separator, self.action_delete_signage)
        self.toolbar.insertAction(self.action_separator, self.filtering)
        self.toolbar.insertAction(self.action_separator, self.reset_filtering)
        self.toolbar.insertAction(self.action_separator, self.action_expandAll)
        self.toolbar.insertAction(self.action_separator, self.action_collapseAll)
        self.toolbar.insertAction(self.action_separator, self.toolbar.addSeparator())
        self.toolbar.insertAction(self.action_separator, self.action_cite)
        self.toolbar.insertAction(self.action_separator, self.action_reach_source)

        connector_menu_btn = QtWidgets.QToolButton(self)
        connector_menu_btn.setIcon(theme_icon_manager.get_icon(':links-line'))
        connector_menu_btn.setText("Import from Connector")
        connector_menu_btn.setToolTip("Import from Connector")
        connector_menu_btn.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        connector_menu_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        connector_menu = QtWidgets.QMenu()

        for c in ConnectorType:
            action = connector_menu.addAction(c.name)
            slot_func = partial(self.importFromConnector, c)
            action.triggered.connect(slot_func)

        connector_menu_btn.setMenu(connector_menu)
        self.toolbar.insertWidget(self.action_separator, connector_menu_btn)

        # --- Shortcuts ---
        self.shortcut_create_childsignage = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+H"),
                                                            self,
                                                            self._createChildSignage,
                                                            context=QtCore.Qt.ShortcutContext.WindowShortcut)

        # --- Dialogs ---
        self.signage_dialog: SignageDialog = None
        self.export_dialog: ExportDialog = None
        self.import_dialog: ImportDialog = None
        self.filter_dialog: FilterDialog = None

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
        self.action_create_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line"),
                                                   "Create Signage (Ctrl + R)",
                                                   self,
                                                   triggered = lambda: self.createSignage(source=self.signageSource()))
        self.action_create_child_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line-child"),
                                                         "Create Child Signage (Ctrl + H)",
                                                         self,
                                                         triggered = self._createChildSignage)
        self.action_delete_signage = QtGui.QAction(theme_icon_manager.get_icon(":delete-bin2"),
                                                   "Delete Signage",
                                                   self,
                                                   triggered = self.deleteRow)
        self.filtering = QtGui.QAction(theme_icon_manager.get_icon(":filter-line"),
                                       "Filters",
                                       self,
                                       triggered=self.setFilters)
        self.reset_filtering = QtGui.QAction(theme_icon_manager.get_icon(":filter-off-line"),
                                             "Reset Filters",
                                             self,
                                             triggered=self.onResetFilters)
        self.action_expandAll = QtGui.QAction(theme_icon_manager.get_icon(":expand-vertical-line"),
                                                "Expand All",
                                                self,
                                                triggered=self.expandAll)
        self.action_collapseAll = QtGui.QAction(theme_icon_manager.get_icon(":collapse-vertical-line"),
                                                "Collapse All",
                                                self,
                                                triggered=self.collapseAll)
        self.action_edit_owner = QtGui.QAction(theme_icon_manager.get_icon(":collapse-vertical-line"),
                                                "Collapse All",
                                                self,
                                                triggered=self.collapseAll)
        self.action_cite = QtGui.QAction(theme_icon_manager.get_icon(":double-quotes"),
                                         "Cite",
                                         self,
                                         triggered=self.cite)
        self.action_reach_source = QtGui.QAction(theme_icon_manager.get_icon(":share-forward-2-line"),
                                         "Go to Source",
                                         self,
                                         triggered=self.reachSource)
        
    def selectedRows(self) -> set[int]:
        """Source model's selected rows"""
        proxy_indexes = self.table.selectedIndexes()
        rows = set()
        for idx in proxy_indexes:
            src_idx = self.proxymodel.mapToSource(idx)
            rows.add(src_idx.row())
        return rows

    def updateAction(self):
        if len(self.selectedRows()) == 1:
            self.action_delete_signage.setEnabled(True)
            self.action_edit_owner.setEnabled(True)
            self.action_create_child_signage.setEnabled(True)

        if len(self.selectedRows()) == 0:
            self.action_delete_signage.setEnabled(False)
            self.action_edit_owner.setEnabled(False)
            self.action_create_child_signage.setEnabled(False)

        if len(self.selectedRows()) > 1:
            self.action_delete_signage.setEnabled(False)
            self.action_edit_owner.setEnabled(False)
            self.action_create_child_signage.setEnabled(False)

        msg = f"[Signage selected: {len(self.selectedRows())}]"
        status_signal.status_message.emit(msg, 5000)

    def show_table_context_menu(self, pos: QtCore.QPoint):
        """Triggered when user right-clicks on the table."""
        indexes = self.table.selectedIndexes()
        if not indexes:
            return
        
        # Status menu
        status_menu = QtWidgets.QMenu("Status", self)
        status_type: SignageStatus
        for status_type in AppDatabase.cache_signage_status.values():
            action = status_menu.addAction(status_type.name)
            slot_func = partial(self.setStatus, status_type.name)
            action.triggered.connect(slot_func)

        # Owner menu
        owner_menu = QtWidgets.QMenu("Owner", self)
        owners: list = mconf.settings.value("owners", [], "QStringList")
        for owner in owners:
            action = owner_menu.addAction(owner)
            slot_func = partial(self.updateOwner, owner)
            action.triggered.connect(slot_func)

        menu = QtWidgets.QMenu(self)
        menu.addMenu(status_menu)
        menu.addMenu(owner_menu)
        menu.addAction(self.action_create_child_signage)
        menu.addAction(self.action_delete_signage)
        menu.addAction(self.action_cite)
        menu.addAction(self.action_reach_source)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def onCellClicked(self, index: QtCore.QModelIndex):
        """ Update mapper """
        currentIndex = self.proxymodel.mapToSource(index)
        self.mapper.setRootIndex(currentIndex.parent())
        self.mapper.setCurrentModelIndex(currentIndex)

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
        signage_type = (index.sibling(index.row(), SignageSqlModel.Fields.Type.index)
                        .data(QtCore.Qt.ItemDataRole.DisplayRole))
        
        if signage_type != AppDatabase.cache_signage_type.get('Request').name:
            return

        refkey = (index.sibling(index.row(), SignageSqlModel.Fields.Refkey.index)
                  .data(QtCore.Qt.ItemDataRole.DisplayRole))
        self.sigSignageDoubleClicked.emit(refkey)

    @Slot()
    def setStatus(self, status_id):
        source_index = self._selectedProxyToSource()
        if not source_index:
            return
        status_index = source_index.sibling(source_index.row(), SignageSqlModel.Fields.Status.index)
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
        owner_index = source_index.sibling(source_index.row(), SignageSqlModel.Fields.Owner.index)
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

    @Slot(str, str)
    def createSignage(self, title: str = "", source: str = ""):
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
        signage.source = source

        # source:
        # '{"application":"InspectorMate", "module":"Notebook", "item":"note", "item_title":"1.3 Line Listing session", "item_id":"1.3 Line Listing session.html", "position":"anchor123"}'
        # '{"application":"InspectorMate", "module":"Evidence", "item":"doc", "item_title":"document[:25]", "item_id":"6", "position":"page2"}'
        # '{"application":"InspectorMate", "module":"Signage", "item":"Request", "item_title":"signage[:25]", "item_id":"2", "position":"child2"}'
        # '{"application":"InspectorMate", "module":"ImportFromOneNote", "item":"Page", "item_title":"title[:25]", "item_id":"id", "position":"link"}'
        # '{"application":"InspectorMate", "module":"ImportFromExcel", "item":"xlsx", "item_title":"filename", "item_id":"fileid", "position":"link to file"}'

        # Insert signage into the database and into the model
        if self.model.insertSignage(signage=signage):
            status_signal.status_message.emit("✔️ Signage created", 7000)
            self.updateReviewProgess()
            return True
        else:
            status_signal.status_message.emit("⚠️ Fail to create Signage", 7000)
            return False

    @Slot(int, str)
    def createChildSignage(self, parent_id: str, source: str = ""):
        """Create Child Signage"""
        if self.signage_dialog is None:
            self.signage_dialog = SignageDialog(parent=None)

        parent_index = self.model.findIndexById(int(parent_id),
                                                SignageSqlModel.Fields.ID.index)
        if not parent_index:
            return
        parent_refkey = (parent_index.sibling(parent_index.row(),
                                              SignageSqlModel.Fields.Refkey.index)
                                              .data(QtCore.Qt.ItemDataRole.DisplayRole))

        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.updateRefkeyField()
        self.signage_dialog.signage_title_lineedit.clear()
        self.signage_dialog.signage_title_lineedit.setFocus()
        self.signage_dialog.parent_signage_id.setText("" if parent_id is None else str(parent_id))
        self.signage_dialog.parent_signage_refkey.setText("" if parent_refkey is None else str(parent_refkey))
        self.signage_dialog.parent_signage_widget.setVisible(True)
        
        if not self.signage_dialog.exec():
            return
        
        signage = self.signage_dialog.signage()
        signage.parentID = parent_id
        signage.source = source
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

        parent_id = (source_index.sibling(source_index.row(),
                                          SignageSqlModel.Fields.ID.index)
                                          .data(QtCore.Qt.ItemDataRole.DisplayRole))
        self.createChildSignage(parent_id, self.signageSource())

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
        self.proxymodel.setUserFilter(text,
                                       [SignageSqlModel.Fields.Refkey.index,
                                        SignageSqlModel.Fields.Status.index,
                                        SignageSqlModel.Fields.Title.index,
                                        SignageSqlModel.Fields.Note.index,
                                        SignageSqlModel.Fields.PublicNote.index,
                                        SignageSqlModel.Fields.Owner.index])

        self.proxymodel.invalidateFilter()

    @Slot()
    def setFilters(self):
        """Open Signage Filter Dialog"""
        if self.filter_dialog is None:
            self.filter_dialog = FilterDialog(parent=self)    
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

        self.proxymodel.setSatusFilter(self.filter_dialog.statusFilter(), SignageSqlModel.Fields.Status.index)
        self.proxymodel.setTypeFilter(self.filter_dialog.typeFilter(), SignageSqlModel.Fields.Type.index)
        self.proxymodel.setOwnerFilter(self.filter_dialog.ownerFilter(), SignageSqlModel.Fields.Owner.index)
        self.proxymodel.setEvidenceFilter(self.filter_dialog.evidenceFilter(), SignageSqlModel.Fields.DocCount.index)
        self.proxymodel.invalidateFilter()

    @Slot()
    def onResetFilters(self):
        """Reset Signage Table Filters"""
        self.proxymodel.setSatusFilter([], SignageSqlModel.Fields.Status.index)
        self.proxymodel.setTypeFilter([], SignageSqlModel.Fields.Type.index)
        self.proxymodel.setOwnerFilter([], SignageSqlModel.Fields.Owner.index)
        self.proxymodel.setEvidenceFilter([], SignageSqlModel.Fields.DocCount.index)
        self.proxymodel.setUserFilter("", [])
        self.search_tool.setText("")
        self.proxymodel.invalidateFilter()

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
            return

        regex = (mconf.default_regex if mconf.settings.value("regex") is None 
                 or mconf.settings.value("regex") == "" else mconf.settings.value("regex"))

        self.startSpinner()
        if connector_type == ConnectorType.DOCX:
            DataService.loadFromDocx(connectors=connectors,
                                     regex=regex,
                                     cache=self.model.connector_cache,
                                     on_ready=self._on_signage_ready,
                                     on_finished=self._on_load_connector_finished)
        elif connector_type == ConnectorType.ONENOTE:
            DataService.loadFromOneNote(connectors=connectors,
                                        regex=regex,
                                        cache=self.model.connector_cache,
                                        on_ready=self._on_signage_ready,
                                        on_finished=self._on_load_connector_finished)

    def expandAll(self):
        self.table.expandAll()

    def collapseAll(self):
        self.table.collapseAll()
    
    def cite(self):
        index: QtCore.QModelIndex = self.table.selectionModel().currentIndex()
        
        if not index.isValid():
            return
        
        src_index = self.proxymodel.mapToSource(index)
        refkey_idx = src_index.sibling(src_index.row(), SignageSqlModel.Fields.Refkey.index)
        refkey = self.model.data(refkey_idx, Qt.ItemDataRole.DisplayRole)
        type_idx = src_index.sibling(src_index.row(), SignageSqlModel.Fields.Type.index)
        type = self.model.data(type_idx, Qt.ItemDataRole.DisplayRole)
        title_idx = src_index.sibling(src_index.row(), SignageSqlModel.Fields.Title.index)
        title = self.model.data(title_idx, Qt.ItemDataRole.DisplayRole)

        citation = f"{type} {refkey} - {title}"
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(f"{citation}")

    def sentToPrivate(self):
        public_text = self.public_note.editor.toHtml()
        self.note.editor.append(public_text)

        index = self.table.selectionModel().currentIndex()
        src_index = self.proxymodel.mapToSource(index)

        public_note_index = src_index.sibling(src_index.row(), SignageSqlModel.Fields.PublicNote.index)
        private_note_index = src_index.sibling(src_index.row(), SignageSqlModel.Fields.Note.index)

        if self.model.setData(private_note_index, self.note.editor.toHtml(), Qt.ItemDataRole.EditRole):
            self.public_note.editor.clear()
            self.model.setData(public_note_index, "", Qt.ItemDataRole.EditRole)

    @Slot()
    def onExportTriggered(self):
        if self.export_dialog is None:
            self.export_dialog = ExportDialog()

        if not self.export_dialog.exec():
            return
        
        selected_types = self.export_dialog.selected_types
        selected_statuses = self.export_dialog.selected_statuses
        outfile_destination = self.export_dialog.outfile_destination 
        include_public_note = self.export_dialog.include_public_note 

        self.startSpinner()
        DataService.export2Excel(self.model.rootModel(),
                                 selected_types,
                                 selected_statuses,
                                 outfile_destination,
                                 include_public_note,
                                 self.stopSpinner)

    @Slot()
    def onImportTriggered(self):
        if self.import_dialog is None:
            self.import_dialog = ImportDialog()

        if not self.import_dialog.exec():
            return
        
        selected_files = self.import_dialog.selectedFiles()
        update_title = self.import_dialog.update_title
        
        self.startSpinner()
        DataService.loadFromExcel(self.model, 
                                  selected_files,
                                  update_title,
                                  self._on_signage_ready,
                                  self.stopSpinner)
        
    def reachSource(self):
        index: QtCore.QModelIndex = self.table.selectionModel().currentIndex()
        
        if not index.isValid():
            return
        
        src_index = self.proxymodel.mapToSource(index)
        source_idx = src_index.sibling(src_index.row(), SignageSqlModel.Fields.Source.index)
        source = self.model.data(source_idx, Qt.ItemDataRole.DisplayRole)
        source_dict: dict = loads(source)

        app = source_dict.get("application")
        module = source_dict.get("module")

        if app == "InspectorMate":
            target = source_dict.get("item_title")
            anchor = source_dict.get("anchor", "")
            if target:
                fpath = f"{AppDatabase.activeWorkspace().notebook_path}/{target}"
                self.sigOpenNote.emit(fpath, anchor)
        else:
            if module == "loadFromDocx":
                target = source_dict.get("file")
                open_file(target)
            elif module == "loadFromOnenote":
                target = source_dict.get("link")
                QtGui.QDesktopServices.openUrl(QtCore.QUrl(target))

    def restoreTableColumnWidth(self):
        """Restore table column width upon GUI initialization"""
        settings.beginGroup("signage")
        for column in range(self.model.columnCount()):
            # if settings.contains(f"column-{column}"):
            self.table.setColumnWidth(column, settings.value(f"column-{column}", 100, int))
        settings.endGroup()

    def saveTableColumnWidth(self):
        """Save table column width upon closing"""
        settings.beginGroup("signage")
        for column in range(self.model.columnCount()):
            settings.setValue(f"column-{column}", self.table.columnWidth(column))
        settings.endGroup()

    def closeEvent(self, a0):
        self.saveTableColumnWidth()
        self.mapper.submit()
        return super().closeEvent(a0)