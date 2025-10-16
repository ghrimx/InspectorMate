from html2text import html2text
from qtpy import Qt, QtCore, QtWidgets, QtGui
from qt_theme_manager import theme_icon_manager


class NoteColumnDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None, important=False):
        super().__init__(parent=parent)
        self.important = important

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        value = index.data(Qt.ItemDataRole.DisplayRole)
        if not value:
            return

        try:
            raw_text = html2text(str(value)).strip()
        except Exception:
            raw_text = ""

        if raw_text != "":
            # Set icon safely
            option.icon = theme_icon_manager.get_color_icon(':quill-pen-fill', "#ff0000") if self.important else theme_icon_manager.get_icon(':quill-pen-fill')

            # Center and size icon
            option.text = "Note"
            option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
            option.displayAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter
            option.decorationAlignment = QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignVCenter

            view = option.widget
            if view:
                option.decorationSize = QtCore.QSize(
                    view.columnWidth(index.column()),
                    view.header().height()
                )
        else:
            option.text = ""


class ReadOnlyDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, *args):
        """ Make editor read-only """
        return


class CenterDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        option.decorationAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)


class CompositeDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, delegates, parent=None):
        super().__init__(parent)
        self.delegates = delegates

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        for delegate in self.delegates:
            delegate.initStyleOption(option, index)