import html2text

from qtpy import (Qt, QtCore, QtGui, QtWidgets)


class ReadOnlyDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, *args):
        """ Make editor read-only """
        return


class CenterDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        option.decorationAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)


class NoteColumnDelegate(ReadOnlyDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        value = index.data(Qt.ItemDataRole.DisplayRole)
        if value is not None:
            raw_text: str = html2text.html2text(value)
            if not (raw_text.strip()) == "":
                option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
                option.icon = QtGui.QIcon(':quill-pen-fill')
                option.text = ""
                option.decorationSize = QtCore.QSize(self.parent().columnWidth(index.column()), self.parent().header().geometry().height())
                option.displayAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
                option.decorationAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
            else:
                option.text = ""
