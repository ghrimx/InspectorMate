from my_pyqt_widgets import ToolBar
from qt_theme_manager import theme_icon_manager

from qtpy import Qt, QtWidgets


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

        self.vbox = QtWidgets.QVBoxLayout(parent)
        self.vbox.addWidget(self.toolbar)
        self.vbox.addWidget(self.splitter)
        self.setLayout(self.vbox)

    def createToolbar(self, parent=None):
        self.toolbar = ToolBar(self)

        # Fold Left Pane
        self.fold_left_pane = self.toolbar.add_action(
            "fold_left_pane",
            "Fold left pane",
            self.onFoldLeftSidebarTriggered,
            theme_icon_manager.get_icon(":sidebar-fold-line"),
        )

        # Search LineEdit
        self.search_tool = QtWidgets.QLineEdit(parent)
        self.search_tool.setPlaceholderText("Search...")
        self.search_tool.setFixedWidth(180)
        self.action_search = self.toolbar.add_widget("search_tool", self.search_tool)

        # Separator
        self.action_separator = self.toolbar.add_separator("first_separator")

        # Spacer
        self.toolbar.add_spacer("spacer")

        # Fold Right Pane
        self.fold_right_pane = self.toolbar.add_action(
            "fold_right_pane",
            "Fold right pane",
            self.onFoldRightSidebarTriggered,
            theme_icon_manager.get_icon(":sidebar-unfold-line"),
        )

    def onFoldLeftSidebarTriggered(self):
        self.left_pane_folded = not self.left_pane_folded

        if self.left_pane_folded:
            self.left_pane.hide()
            self.fold_left_pane.setIcon(
                theme_icon_manager.get_icon(":sidebar-unfold-line")
            )
        else:
            self.left_pane.show()
            self.fold_left_pane.setIcon(
                theme_icon_manager.get_icon(":sidebar-fold-line")
            )

    def onFoldRightSidebarTriggered(self):
        self.right_pane_folded = not self.right_pane_folded

        if self.right_pane_folded:
            self.right_pane.hide()
            self.fold_right_pane.setIcon(
                theme_icon_manager.get_icon(":sidebar-fold-line")
            )
        else:
            self.right_pane.show()
            self.fold_right_pane.setIcon(
                theme_icon_manager.get_icon(":sidebar-unfold-line")
            )
