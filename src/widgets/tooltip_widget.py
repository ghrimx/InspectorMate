from qtpy import QtWidgets, QtCore, QtGui, Slot

class QToolTipper(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)

    def eventFilter(self, obj, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.Type.ToolTip:
            view = obj.parent()
            if not isinstance(view, QtWidgets.QAbstractItemView):
                return False
            
            helpevent: QtGui.QHelpEvent = QtGui.QHelpEvent(event.type(), event.pos(), event.globalPos())
            index = view.indexAt(helpevent.pos())
            if not index.isValid():
                return False
            
            item_text = view.model().data(index, QtCore.Qt.ItemDataRole.DisplayRole)

            # Wrap the text
            formattedTooltip = f"<div style='max-width: 300px; white-space: normal;'>{item_text}</div>"
            
            fm = view.fontMetrics()
            item_text_width = fm.horizontalAdvance(item_text)
            rect = view.visualRect(index)
            rect_width = rect.width()

            if item_text_width > rect_width:
                QtWidgets.QToolTip.showText(helpevent.globalPos(),
                                            formattedTooltip,
                                            view,
                                            rect)
            else:
                QtWidgets.QToolTip.hideText()
            return True
        return False