from qtpy import QtWidgets, QtCore, QtGui, Slot

from signage.signage_model import SignageTreeModel

from models.model import ProxyModel

#TODO
class SignageFilterTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport().installEventFilter(self)
        self.setMouseTracking(True)
        
        self.popup = QtWidgets.QDialog(self, QtCore.Qt.WindowType.Popup | QtCore.Qt.WindowType.ToolTip)
        layout = QtWidgets.QVBoxLayout()
        
        self.popupLabel = QtWidgets.QLabel(self.popup)
        self.popupLabel.setWordWrap(True)
        layout.addWidget(self.popupLabel)
        self.popupLabel.setTextFormat(QtCore.Qt.TextFormat.RichText)
        
        self.popup.setLayout(layout)
        self.popup.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self.viewport():
            if event.type() == QtCore.QEvent.Type.MouseMove:
                mouseEvent = event  # QMouseEvent
                index = self.indexAt(mouseEvent.pos())
                if index.isValid():
                    self.showPopup(index)
                else:
                    self.popup.hide()
            elif event.type() == QtCore.QEvent.Type.Leave:
                self.popup.hide()
        elif watched == self.popup:
            if event.type() == QtCore.QEvent.Type.Leave:
                self.popup.hide()
        return super().eventFilter(watched, event)

    def showPopup(self, index: QtCore.QModelIndex):
        if index.column() == 1:
            r = self.visualRect(index)
            self.popup.move(self.viewport().mapToGlobal(r.bottomLeft()))
            self.popup.setFixedSize(200, self.popup.heightForWidth(100))
            self.popupLabel.setText(index.data(QtCore.Qt.ItemDataRole.DisplayRole))
            self.popup.adjustSize()
            self.popup.show()
        else:
            self.popup.hide()


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


class SignageFilter(QtWidgets.QWidget):
    def __init__(self, model: SignageTreeModel, parent=None):
        super(SignageFilter, self).__init__(parent)

        self._model = model.sourceModel()
        self._proxy_model = ProxyModel(self._model)
        self._proxy_model.setPermanentFilter('0', [model.Fields.Type.index])
        self._proxy_model.setDynamicSortFilter(False)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        form = QtWidgets.QFormLayout()
        vbox.addLayout(form)

        self.count_request = QtWidgets.QLabel()
        self.count_request.setText(str(self._proxy_model.rowCount()))
        form.addRow("Total request:", self.count_request)

        self.table = QtWidgets.QTableView()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)  # Make ReadOnly
        self.table.setModel(self._proxy_model)
        tooltipper = QToolTipper(self.table)
        self.table.viewport().installEventFilter(tooltipper)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)

        for field in model.Fields.fields():
            self.table.hideColumn(field.index)

        self.table.showColumn(model.Fields.Refkey.index)
        self.table.showColumn(model.Fields.Title.index)

        vbox.addWidget(self.table)

        self._model.dataChanged.connect(self.updateCounter)

    @Slot()
    def updateCounter(self):
        self.count_request.setText(str(self._proxy_model.rowCount()))

        