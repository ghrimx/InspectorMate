from qtpy import (Qt, QtWidgets, QtGui)

from widgets.toolbar import ToolBar

class BaseTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.createToolbar()

        self.left_splitter_size = 150
        self.central_splitter_size = 500
        self.right_splitter_size = 100
        
        # Left pane
        self.left_pane = QtWidgets.QTabWidget(parent)
        self.left_pane.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.left_pane.setMovable(False)
        
        # Splitter
        self.splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.left_pane)
        self.splitter.setSizes([self.left_splitter_size, self.central_splitter_size, self.right_splitter_size])

        self.vbox  = QtWidgets.QVBoxLayout(parent)
        self.vbox.addWidget(self.toolbar)
        self.vbox.addWidget(self.splitter)
        self.setLayout(self.vbox)

    def createToolbar(self, parent=None) :
        self.toolbar = ToolBar(parent, icon_size=(24,24))

        # Fold Left Pane
        self.btn_fold_left_pane = QtWidgets.QPushButton()
        self.btn_fold_left_pane.setIcon(QtGui.QIcon(':sidebar-fold-line'))
        self.btn_fold_left_pane.setToolTip('Fold Pane')
        self.btn_fold_left_pane.setCheckable(True)
        self.btn_fold_left_pane.clicked.connect(self.onFoldLeftSidebarTriggered)
        self.action_fold_left_sidebar = self.toolbar.addWidget(self.btn_fold_left_pane)

        # Search LineEdit
        self.search_tool = QtWidgets.QLineEdit(parent)
        self.search_tool.setPlaceholderText("Search...")
        self.search_tool.setFixedWidth(180)
        self.action_search = self.toolbar.addWidget(self.search_tool)

        # Separator
        self.toolbar.addSeparator()

        # Spacer
        self.action_separator = self.toolbar.add_spacer()

        # Fold Right Pane
        self.btn_fold_right_pane = QtWidgets.QPushButton()
        self.btn_fold_right_pane.setIcon(QtGui.QIcon(":sidebar-unfold-line"))
        self.btn_fold_right_pane.setToolTip("Fold Pane")
        self.btn_fold_right_pane.setCheckable(True)
        self.btn_fold_right_pane.clicked.connect(self.onFoldRightSidebarTriggered)
        self.action_fold_right_sidebar = self.toolbar.addWidget(self.btn_fold_right_pane)

    def onFoldLeftSidebarTriggered(self):
        if self.btn_fold_left_pane.isChecked():
            self.left_splitter_size = 0
            self.btn_fold_left_pane.setIcon(QtGui.QIcon(':sidebar-unfold-line'))
        else:
            self.left_splitter_size = 150
            self.btn_fold_left_pane.setIcon(QtGui.QIcon(':sidebar-fold-line'))

        self.splitter.setSizes([self.left_splitter_size, 500, self.right_splitter_size])
    
    def onFoldRightSidebarTriggered(self):
        if self.btn_fold_right_pane.isChecked():
            self.right_splitter_size = 0
            self.btn_fold_right_pane.setIcon(QtGui.QIcon(':sidebar-fold-line'))
        else:
            self.right_splitter_size = 100
            self.btn_fold_right_pane.setIcon(QtGui.QIcon(':sidebar-unfold-line'))

        self.splitter.setSizes([self.left_splitter_size, 500, self.right_splitter_size])

     

    
