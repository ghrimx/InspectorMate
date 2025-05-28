from qtpy import (QtWidgets, QtCore, QtGui, Qt)

from workspace.workspacemodel import WorkspaceModel
from widgets.tableview import TableView
from delegates.delegate import ReadOnlyDelegate


class WorkspaceTable(TableView):
    def __init__(self, model: WorkspaceModel):
        super().__init__()
        self.setModel(model)
        self.horizontalHeader().setStretchLastSection(True)

        self.state_delegate = StateDelegate()
        self.setItemDelegateForColumn(model.Fields.State.index, self.state_delegate)


class StateDelegate(ReadOnlyDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        value = index.data(Qt.ItemDataRole.DisplayRole)
        if value == 1:
            ico = ':status-on'
        else:
            ico = ':status-off'

        if value != "":
            option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
            option.icon = QtGui.QIcon(ico)
            option.decorationAlignment = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignCenter
            option.displayAlignment = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignCenter
            option.text = ""
            option.decorationSize = option.rect.size()
