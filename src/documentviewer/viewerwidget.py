import logging
from qtpy import (Qt, QtCore, QtWidgets, QtGui, Slot, Signal)
from PyQt6.QtSql import QSqlRelationalDelegate

from evidence.evidencemodel import EvidenceModel
from database.dbstructure import Document

from widgets.toolbar import ToolBar
from widgets.fitcontenteditor import FitContentTextEdit
from widgets.richtexteditor import RichTextEditor

from snipping.snippingtool import Capture

from qt_theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


class ViewerWidget(QtWidgets.QWidget):
    sigCreateChildSignage = Signal(int, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document: Document = None

        self.createToolbar(parent)

        self.left_pane_folded = False
        self.right_pane_folded = False

        # Splitter
        self.splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        
        # Left pane
        self.left_pane = QtWidgets.QTabWidget(self)
        self.left_pane.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.left_pane.setMovable(False)
        self.splitter.addWidget(self.left_pane)

        # Central Widget
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.scroll_area.setMinimumSize(QtCore.QSize(500, 0)) 
        self.scroll_area.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 500, 500))
        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.splitter.addWidget(self.scroll_area)

        # Right pane
        self.right_pane = QtWidgets.QTabWidget(self)
        self.right_pane.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        self.right_pane.setMovable(False)

        self.createInfoTab()
        self.createNoteTab()

        self.splitter.addWidget(self.right_pane)

        self.splitter.setSizes([100, 600, 100])
        
        self.vbox  = QtWidgets.QVBoxLayout()
        self.vbox.addWidget(self._toolbar)
        self.vbox.addWidget(self.splitter)
        self.setLayout(self.vbox)
        
        self.onFoldRightSidebarTriggered()

    @classmethod
    def viewerName(cls):
        return cls.__name__
    
    @classmethod
    def supportedFormats(cls):
        return [""]
    
    @property
    def document(self):
        return self._document
    
    @document.setter
    def document(self, doc: Document):
        self._document = doc
    
    def createInfoTab(self):
        self.info_tab = QtWidgets.QWidget(self)
        formlayout = QtWidgets.QFormLayout(self.info_tab)
        self.info_tab.setLayout(formlayout)
        self.status = QtWidgets.QComboBox(self.info_tab)
        self.title = FitContentTextEdit(False)
        self.subtitle = QtWidgets.QLineEdit()
        self.reference = QtWidgets.QLineEdit()
        self.filename = FitContentTextEdit(True)
        self.filename.setStyleSheet("color: grey;")
        self.refKey = QtWidgets.QLineEdit()
        self.signage_id = QtWidgets.QLineEdit()
        self.signage_id.setReadOnly(True)
        self.signage_id.setStyleSheet("color: grey;")

        formlayout.addRow('Status', self.status)
        formlayout.addRow('RefKey', self.refKey)
        formlayout.addRow('Title', self.title)
        formlayout.addRow('Subtitle', self.subtitle)
        formlayout.addRow('Reference', self.reference)
        formlayout.addRow('Filename', self.filename)
        formlayout.addRow('Signage id', self.signage_id)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)
        self.right_pane.addTab(self.info_tab, "Info")

    def createTagTab(self):
        ...

    def createNoteTab(self):
        self.note_tab = RichTextEditor.fromMapper(bar=False, parent=self)
        self.right_pane.addTab(self.note_tab, "Note")

    def createToolbar(self, parent=None) :
        self._toolbar = QtWidgets.QToolBar(parent)

        # Fold Left Pane
        self.fold_left_pane = QtGui.QAction(theme_icon_manager.get_icon(':sidebar-fold-line'), "Fold left pane", self)
        self.fold_left_pane.triggered.connect(self.onFoldLeftSidebarTriggered)
        self._toolbar.addAction(self.fold_left_pane)

        # Separator
        spacer = QtWidgets.QWidget(self)
        spacer.setContentsMargins(0,0,0,0)
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.action_first_separator = self._toolbar.addSeparator()

        # Spacer
        self._toolbar_spacer = self._toolbar.addWidget(spacer)

        # Create Child Signage
        # Action inserted to toolbar after init
        self.action_create_child_signage = QtGui.QAction(theme_icon_manager.get_icon(":signpost-line-child"),
                                                         "Create Child Signage (Ctrl + N)",
                                                         self,
                                                         triggered = self.createChildSignage)
        self.action_create_child_signage.setShortcut(QtGui.QKeySequence("Ctrl+N"))

        # Fold Right Pane
        self.fold_right_pane = QtGui.QAction(theme_icon_manager.get_icon(":sidebar-unfold-line"), "Fold right pane", self)
        self.fold_right_pane.triggered.connect(self.onFoldRightSidebarTriggered)
        self._toolbar.addAction(self.fold_right_pane)

    def toolbar(self) -> ToolBar:
        return self._toolbar

    def toolbarFreeSpace(self):
        return self._toolbar_spacer
    
    def createMapper(self, model: EvidenceModel, index: QtCore.QModelIndex):
        self.status_model = model.relationModel(model.Fields.Status.index)
        self.status.setModel(self.status_model)
        self.status.setModelColumn(1)

        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(model)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))

        # Info tab
        self.mapper.addMapping(self.status, model.Fields.Status.index)
        self.mapper.addMapping(self.refKey, model.Fields.Refkey.index)
        self.mapper.addMapping(self.title, model.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.subtitle, model.Fields.Subtitle.index)
        self.mapper.addMapping(self.reference, model.Fields.Reference.index)
        self.mapper.addMapping(self.filename, model.Fields.Filepath.index, b"plainText")
        self.mapper.addMapping(self.signage_id, model.Fields.SignageID.index)

        # Note tab
        self.mapper.addMapping(self.note_tab.editor, model.Fields.Note.index)
        self.mapper.setCurrentModelIndex(index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)

    def setMapperIndex(self, index: QtCore.QModelIndex):
        self.mapper.setCurrentModelIndex(index)
    
    @Slot()
    def onFoldLeftSidebarTriggered(self):
        self.left_pane_folded = not self.left_pane_folded

        if self.left_pane_folded:
            self.left_pane.hide()
            self.fold_left_pane.setIcon(theme_icon_manager.get_icon(':sidebar-unfold-line'))
        else:
            self.left_pane.show()
            self.fold_left_pane.setIcon(theme_icon_manager.get_icon(':sidebar-fold-line'))
    
    @Slot()
    def onFoldRightSidebarTriggered(self):
        self.right_pane_folded = not self.right_pane_folded

        if self.right_pane_folded:
            self.right_pane.hide()
            self.fold_right_pane.setIcon(theme_icon_manager.get_icon(':sidebar-fold-line'))
        else:
            self.right_pane.show()
            self.fold_right_pane.setIcon(theme_icon_manager.get_icon(':sidebar-unfold-line'))

    @Slot()
    def cite(self, citation):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(citation)

    @Slot()
    def capture(self, citation):
        self.capturer = Capture(source=citation, parent=self)
        self.capturer.show()

    def source(self) -> str:
        ...

    @Slot()
    def createChildSignage(self):
        signage_id = self.signage_id.text()

        try:
            signage_id = int(self.signage_id.text())
        except Exception as e:
            signage_id = -1

        self.sigCreateChildSignage.emit(signage_id, "", self.source())

    def showEvent(self, event: QtGui.QShowEvent):
        super().showEvent(event)


