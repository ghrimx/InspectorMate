import logging
from qtpy import (Qt, QtCore, QtWidgets, QtGui, Slot)
from PyQt6.QtSql import QSqlRelationalDelegate

from evidence.evidencemodel import DocTableModel
from db.dbstructure import Document

from widgets.toolbar import ToolBar
from widgets.fitcontenteditor import FitContentTextEdit
from widgets.richtexteditor import RichTextEditor

from snipping.snippingtool import Capture
from utilities import config as mconf

logger = logging.getLogger(__name__)

class ViewerWidget(QtWidgets.QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self._document: Document = None
        self.model: DocTableModel = model

        self.createToolbar(parent)

        self.left_splitter_size = 150
        self.central_splitter_size = 500
        self.right_splitter_size = 100

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

        self.splitter.setSizes([self.left_splitter_size, self.central_splitter_size, self.right_splitter_size])
        
        self.vbox  = QtWidgets.QVBoxLayout(self)
        self.vbox.addWidget(self._toolbar)
        self.vbox.addWidget(self.splitter)
        self.setLayout(self.vbox)

    @classmethod
    def viewerName(cls):
        return "AbstractViewer"
    
    @classmethod
    def supportedFormats(cls):
        return [""]
    
    def createInfoTab(self):
        self.info_tab = QtWidgets.QWidget(self)
        formlayout = QtWidgets.QFormLayout(self.info_tab)
        self.info_tab.setLayout(formlayout)
        self.status = QtWidgets.QComboBox(self.info_tab)
        self.title = FitContentTextEdit(False)
        self.subtitle = QtWidgets.QLineEdit()
        self.reference = QtWidgets.QLineEdit()
        self.filename = FitContentTextEdit(True)
        self.refKey = QtWidgets.QLineEdit()

        formlayout.addRow('Status', self.status)
        formlayout.addRow('RefKey', self.refKey)
        formlayout.addRow('Title', self.title)
        formlayout.addRow('Subtitle', self.subtitle)
        formlayout.addRow('Reference', self.reference)
        formlayout.addRow('Filename', self.filename)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)
        self.right_pane.addTab(self.info_tab, "Info")

    def createTagTab(self):
        ...

    def createNoteTab(self):
        self.note_tab = RichTextEditor.fromMapper(bar=False, parent=self)
        self.right_pane.addTab(self.note_tab, "Note")

    def createToolbar(self, parent=None) :
        self._toolbar = ToolBar(self, icon_size=(24,24))

        # Fold Left Pane
        self.fold_left_pane = QtGui.QAction(QtGui.QIcon(':sidebar-fold-line'), "Fold left pane", self._toolbar)
        self.fold_left_pane.setCheckable(True)
        self.fold_left_pane.triggered.connect(self.onFoldLeftSidebarTriggered)
        self._toolbar.addAction(self.fold_left_pane)

        # Separator
        self.action_first_separator = self._toolbar.addSeparator()

        # Spacer
        self._toolbar_spacer = self._toolbar.add_spacer()

        # Fold Right Pane
        self.fold_right_pane = QtGui.QAction(QtGui.QIcon(":sidebar-unfold-line"), "Fold right pane", self._toolbar)
        self.fold_right_pane.setCheckable(True)
        self.fold_right_pane.triggered.connect(self.onFoldRightSidebarTriggered)
        self._toolbar.addAction(self.fold_right_pane)

    def toolbar(self) -> ToolBar:
        return self._toolbar

    def toolbarFreeSpace(self):
        return self._toolbar_spacer
    
    def createMapper(self, model_index: QtCore.QModelIndex):
        self.model_index = model_index

        self.status_model = self.model.relationModel(self.model.Fields.Status.index)
        self.status.setModel(self.status_model)
        self.status.setModelColumn(1)

        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))

        # Info tab
        self.mapper.addMapping(self.status, self.model.Fields.Status.index)
        self.mapper.addMapping(self.refKey, self.model.Fields.RefKey.index)
        self.mapper.addMapping(self.title, self.model.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.subtitle, self.model.Fields.Subtitle.index)
        self.mapper.addMapping(self.reference, self.model.Fields.Reference.index)
        self.mapper.addMapping(self.filename, self.model.Fields.Filename.index, b"plainText")

        # Note tab
        self.mapper.addMapping(self.note_tab.editor, self.model.Fields.Note.index)
        self.mapper.setCurrentModelIndex(self.model_index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)

    def setMapperIndex(self, index: QtCore.QModelIndex):
        self.mapper.setCurrentModelIndex(index)

    @Slot()
    def onFoldLeftSidebarTriggered(self):
        if self.fold_left_pane.isChecked():
            self.left_splitter_size = 0
            self.fold_left_pane.setIcon(QtGui.QIcon(':sidebar-unfold-line'))
        else:
            self.left_splitter_size = 150
            self.fold_left_pane.setIcon(QtGui.QIcon(':sidebar-fold-line'))

        self.splitter.setSizes([self.left_splitter_size, 500, self.right_splitter_size])
    
    @Slot()
    def onFoldRightSidebarTriggered(self):
        if self.fold_right_pane.isChecked():
            self.right_splitter_size = 0
            self.fold_right_pane.setIcon(QtGui.QIcon(':sidebar-fold-line'))
        else:
            self.right_splitter_size = 100
            self.fold_right_pane.setIcon(QtGui.QIcon(':sidebar-unfold-line'))

        self.splitter.setSizes([self.left_splitter_size, 500, self.right_splitter_size])

    @Slot()
    def cite(self, citation):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(citation)

    @Slot()
    def capture(self, citation):
        self.capturer = Capture(source=citation)
        self.capturer.show()  
        
    