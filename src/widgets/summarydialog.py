from qtpy import (QtCore, QtWidgets, QtGui, Signal)


class SummaryDialog(QtWidgets.QDialog):
    """QDialog to summarize"""

    sigReload = Signal()

    def __init__(self, parent=None):
        super(SummaryDialog, self).__init__(parent)
        self.initUI()


    def initUI(self):
        self.setWindowTitle("Summary Dialog")

        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vlayout)

        top_button_box = QtWidgets.QHBoxLayout()
        self.reload_btn = QtWidgets.QPushButton()
        self.reload_btn.setIcon(QtGui.QIcon(":reset-left-fill"))
        top_button_box.addStretch()
        top_button_box.addWidget(self.reload_btn)

        self.reload_btn.clicked.connect(self.sigReload)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.tabs = QtWidgets.QTabWidget()

        self.signagetable = QtWidgets.QTableView()
        self.evidencetable = QtWidgets.QTableView()

        self.tabs.addTab(self.signagetable, "Signage")
        self.tabs.addTab(self.evidencetable, "Evidence")
        
        self.vlayout.addLayout(top_button_box)
        self.vlayout.addWidget(self.tabs)
        self.vlayout.addWidget(self.buttonBox)
        self.adjust_size()

    def computeTableHeight(self, table: QtWidgets.QTableWidget) -> int:
        """Calculate table height."""
        height = 0
        for i in range(table.verticalHeader().count()):
            if not table.verticalHeader().isSectionHidden(i):
                height += table.verticalHeader().sectionSize(i)
        if table.horizontalScrollBar().isHidden():
            height += table.horizontalScrollBar().height()
        if not table.horizontalHeader().isHidden():
            height += table.horizontalHeader().height()

        return height

    def adjust_size(self):
        self.adjustSize()
        self.signagetable.setMinimumHeight(self.computeTableHeight(self.signagetable))
        margins = self.vlayout.contentsMargins()

        width = margins.left() + margins.right() + self.signagetable.horizontalHeader().length() + self.signagetable.verticalHeader().width() + self.signagetable.frameWidth() * 10
        height = self.computeTableHeight(self.signagetable)

        self.resize(width, height)

class Delegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent = None):
        super().__init__(parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super().initStyleOption(option, index)

