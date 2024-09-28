from qtpy import (Qt, QtCore, QtWidgets, QtGui)


class ToolBar(QtWidgets.QToolBar):
    """
    Initialize the toolbar.

    Args:
        parent: The parent widget.
        orientation: The toolbar's orientation.
        style: The toolbar's tool button style.
        icon_size: The toolbar's icon size.
    """

    def __init__(self,
                 parent,
                 orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 style: Qt.ToolButtonStyle = Qt.ToolButtonStyle.ToolButtonIconOnly,
                 icon_size: tuple[int, int] = (32, 32)) -> None:
        super().__init__(parent)
        self.actions_call = {}
        self.setOrientation(orientation)
        self.setToolButtonStyle(style)
        self.setIconSize(QtCore.QSize(icon_size[0], icon_size[1]))

    def add_action(self, icon: str, text: str = None, tooltip: str = None, trigger_action = None) -> None:
        """
        Add an action to the toolbar.

        Args:
            text: The button's text.
            icon: The button's icon.
            trigger_action: The action to be executed when the button is clicked.
        """
        action = QtGui.QAction(QtGui.QIcon(icon), text, self)
        action.setToolTip(tooltip)
        action.triggered.connect(trigger_action)
        self.actions_call[text] = action
        self.addAction(action)
    
    def add_button(self, icon: str, text: str|None, tooltip: str|None = None, checkable: bool = False, trigger_action = None) -> QtGui.QAction:
        """
        Add a button to the toolbar.

        Args:
            text: The button's text.
            icon: The button's icon.
            tooltip: The button's tooltip.
            trigger_action: The action to be executed when the button is clicked.
        """
        button = QtWidgets.QToolButton()
        button.setIcon(QtGui.QIcon(icon))
        button.setToolTip(tooltip)
        button.setCheckable(checkable)
        button.clicked.connect(trigger_action)
        self.actions_call[text] = button
        action = self.addWidget(button)
        return action

    def add_spacer(self) -> QtGui.QAction:
        """
        Add a spacer to the toolbar.
        """
        spacer = QtWidgets.QWidget(self)
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        action = self.addWidget(spacer)
        return action
