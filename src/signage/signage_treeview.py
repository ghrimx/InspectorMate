import base64
import logging
import html2text

from qtpy import QtWidgets, QtGui, QtCore, Signal, Slot
from signage.signage_style import TABLE_STYLE
from widgets.treeview import TreeView
from theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


class SignageTreeView(TreeView):
    
    class Signals(QtCore.QObject):
        delete = Signal()
        resetFilters = Signal()
        updateStatus = Signal(int)
        updateOwner = Signal(str)
        updateType = Signal()

    def __init__(self, statuses: dict, owners: list, parent=None):
        super(SignageTreeView, self).__init__(parent=parent)
        self.signals = self.Signals()
        self.context_menu = QtWidgets.QMenu(self)
        
        # Context Menu
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.createAction(statuses, owners)
        self.setStyleSheet(TABLE_STYLE)

    def focusOutEvent(self, a0):
        return super().focusOutEvent(a0)      

    def createAction(self, statuses: dict = None, owners: list = None):
        self.action_delete_rows = QtGui.QAction(theme_icon_manager.get_icon(":delete-bin2"),
                                                "Delete",
                                                self,
                                                triggered=self.signals.delete)

        # self.action_openLink = QtGui.QAction(theme_icon_manager.get_icon(":link-m"),
        #                                      "Open Link",
        #                                      self,
        #                                      triggered=self.openLink)

        # Status menu
        self.status_menu = QtWidgets.QMenu("Status", self)
        if statuses is not None:
            for signage_status in statuses.values():
                action_update_status = self.status_menu.addAction(signage_status.name)
                action_update_status.setData(signage_status)
            self.status_menu.triggered.connect(self.handleUpdateActionSignal)

        # Owner menu
        self.owner_menu = QtWidgets.QMenu("Owner", self)
        if owners is not None:
            for owner in owners:
                self.owner_menu.addAction(owner)
            self.owner_menu.triggered.connect(self.handleUpdateActionSignal)

        self.action_resetfilter = QtGui.QAction(theme_icon_manager.get_icon(":filter-off-line"),
                                                "Reset filters",
                                                self,
                                                triggered=self.signals.resetFilters)
        self.action_expandAll = QtGui.QAction(theme_icon_manager.get_icon(":expand-vertical-line"),
                                                "Expand All",
                                                self,
                                                triggered=self.expandAll)
        self.action_collapseAll = QtGui.QAction(theme_icon_manager.get_icon(":collapse-vertical-line"),
                                                "Collapse All",
                                                self,
                                                triggered=self.collapseAll)

        # self.selectionModel().selectionChanged.connect(self.updateAction)

        self.updateAction()
    
    @Slot(QtGui.QAction)
    def handleUpdateActionSignal(self, action: QtGui.QAction):
        sender = self.sender()

        match sender:
            case self.status_menu:
                status = action.data()
                self.signals.updateStatus.emit(status.uid)
            case self.owner_menu:
                value = action.text()
                self.signals.updateOwner.emit(value)
            case _:
                return

    def contextMenuEvent(self, event: QtGui.QMouseEvent):
        """Creating a context menu"""
        self.context_menu.addMenu(self.status_menu)
        self.context_menu.addMenu(self.owner_menu)
        self.context_menu.addAction(self.action_delete_rows)
        # self.context_menu.addAction(self.action_openLink)
        self.context_menu.addAction(self.action_resetfilter)
        self.context_menu.addAction(self.action_expandAll)
        self.context_menu.addAction(self.action_collapseAll)
        self.context_menu.exec(QtGui.QCursor().pos())

    def updateAction(self):
        pass
        # if len(self.selectedRows()) == 1:
        #     self.action_delete_rows.setEnabled(True)
        #     self.owner_menu.setEnabled(True)
        #     self.status_menu.setEnabled(True)

        # if len(self.selectedRows()) == 0:
        #     self.action_delete_rows.setEnabled(False)
        #     self.action_openLink.setEnabled(False)
        #     self.owner_menu.setEnabled(False)
        #     self.status_menu.setEnabled(False)

        # if len(self.selectedRows()) > 1:
        #     self.action_delete_rows.setEnabled(True)
        #     self.action_openLink.setEnabled(False)
        #     self.owner_menu.setEnabled(True)
        #     self.status_menu.setEnabled(True)

    def selectedProxyIndexes(self) -> list[QtCore.QModelIndex]:
        """Return a list of all selected indexes mapped to the source model indexes"""
        proxy_model = self.model()
        indexes = self.selectedIndexes()
        selected_indexes = []
        for index in indexes:
            selected_indexes.append(proxy_model.mapToSource(index))

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

class TitleDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, signage_type: dict, type_column: int, parent=None):
        super().__init__(parent=parent)
        self._signage_type = signage_type
        self._type_column = type_column

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super().initStyleOption(option, index)

        title = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        type_id = index.sibling(index.row(), self._type_column).data(QtCore.Qt.ItemDataRole.DisplayRole)

        signage_type = self._signage_type.get(type_id)

        pix = QtGui.QPixmap()

        if signage_type is not None:
            img64str = signage_type.icon.strip()
            try:
                icon_bytearray = base64.b64decode(img64str)
            except UnicodeError:
                logger.error('Cannot decode string to bytes')
            except Exception as e:
                logger.error(e)
            else:
                pix.loadFromData(icon_bytearray)

        signage_type_icon = QtGui.QIcon(pix)

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = signage_type_icon
        option.text = title
        option.decorationSize = QtCore.QSize(self.parent().header().geometry().height(), self.parent().header().geometry().height())

class TypeDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, signage_type: dict, parent=None):
        super().__init__(parent=parent)
        self._signage_type = signage_type

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super().initStyleOption(option, index)

        type_id = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        signage_type = self._signage_type.get(type_id)

        if signage_type is not None:
            option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDisplay
            option.text = signage_type.name
        else:
            option.text = str(type_id)

class StatusDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, signage_status: dict, status_column: int, parent=None):
        super().__init__(parent=parent)
        self._signage_status = signage_status
        self._status_column = status_column

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super().initStyleOption(option, index)

        if index.column() == self._status_column:
            status_id = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
            signage_status = self._signage_status.get(status_id)

            if signage_status is not None:
                option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDisplay
                option.text = signage_status.name
            else:
                option.text = str(status_id)


class PrivateNoteDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: SignageTreeView = None):
        super(PrivateNoteDelegate, self).__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)

        note = index.data(QtCore.Qt.ItemDataRole.DisplayRole)

        if note is not None:
            raw_note: str = html2text.html2text(note)

            if raw_note.strip() != "":
                option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
                option.icon = theme_icon_manager.get_icon(':quill-pen-fill')
                option.text = ""
                option.decorationSize = QtCore.QSize(self.parent().columnWidth(index.column()), self.parent().header().geometry().height())
                option.displayAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
                option.decorationAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
            else:
                option.text = ""

class PublicNoteDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: SignageTreeView = None):
        super(PublicNoteDelegate, self).__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)

        note = index.data(QtCore.Qt.ItemDataRole.DisplayRole)

        if note is not None:
            raw_note: str = html2text.html2text(note)

            if raw_note.strip() != "":
                option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
                option.icon = theme_icon_manager.get_icon(':quill-pen-fill-red')
                option.text = ""
                option.decorationSize = QtCore.QSize(self.parent().columnWidth(index.column()), self.parent().header().geometry().height())
                option.displayAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
                option.decorationAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
            else:
                option.text = ""


class EvidenceDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: SignageTreeView = None):
        super(EvidenceDelegate, self).__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)

        evidence_count = index.data(QtCore.Qt.ItemDataRole.DisplayRole)

        if evidence_count is not None:

            if int(evidence_count) > 0:
                option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
                option.icon = theme_icon_manager.get_icon(':file-text-line')
                option.text = ""
                option.decorationSize = QtCore.QSize(self.parent().columnWidth(index.column()), self.parent().header().geometry().height())
                option.displayAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
                option.decorationAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
            else:
                option.text = ""


class ProgressBarDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, evidence_column: int, parent=None):
        super().__init__(parent)
        self._evidence_column = evidence_column
            
    def paint(self, painter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):

        evidence_eol = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        evidence_count = index.sibling(index.row(), self._evidence_column).data(QtCore.Qt.ItemDataRole.DisplayRole)

        if evidence_count is not None:
            if int(evidence_count) > 0:
                progress = int((evidence_eol / evidence_count) * 100)
        
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
                option.text = "n/a"
                # super().paint(painter, option, index)
                
    
