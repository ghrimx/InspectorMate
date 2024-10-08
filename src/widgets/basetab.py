from qtpy import (Qt, QtWidgets, QtGui)

from widgets.toolbar import ToolBar

class BaseTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.createToolbar()

        self.left_pane_folded = False
        self.right_pane_folded = False
        
        # Left pane
        self.left_pane = QtWidgets.QTabWidget(parent)
        self.left_pane.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.left_pane.setMovable(False)

        self.right_pane = QtWidgets.QTabWidget(parent)
        self.right_pane.setMovable(False)
        
        # Splitter
        self.splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.left_pane)
        self.splitter.addWidget(self.right_pane)

        self.vbox  = QtWidgets.QVBoxLayout(parent)
        self.vbox.addWidget(self.toolbar)
        self.vbox.addWidget(self.splitter)
        self.setLayout(self.vbox)

    def createToolbar(self, parent=None) :
        self.toolbar = ToolBar(parent, icon_size=(24,24))

        # Fold Left Pane
        self.fold_left_pane = QtGui.QAction(QtGui.QIcon(':sidebar-fold-line'), "Fold left pane", self, triggered=self.onFoldLeftSidebarTriggered)
        self.toolbar.addAction(self.fold_left_pane)

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
        self.fold_right_pane = QtGui.QAction(QtGui.QIcon(":sidebar-unfold-line"), "Fold right pane", self, triggered=self.onFoldRightSidebarTriggered)
        self.toolbar.addAction(self.fold_right_pane)

    def onFoldLeftSidebarTriggered(self):
        self.left_pane_folded = not self.left_pane_folded

        if self.left_pane_folded:
            self.left_pane.hide()
            self.fold_left_pane.setIcon(QtGui.QIcon(':sidebar-unfold-line'))
        else:
            self.left_pane.show()
            self.fold_left_pane.setIcon(QtGui.QIcon(':sidebar-fold-line'))

    def onFoldRightSidebarTriggered(self):
        self.right_pane_folded = not self.right_pane_folded

        if self.right_pane_folded:
            self.right_pane.hide()
            self.fold_right_pane.setIcon(QtGui.QIcon(':sidebar-fold-line'))
        else:
            self.right_pane.show()
            self.fold_right_pane.setIcon(QtGui.QIcon(':sidebar-unfold-line'))
     
    
