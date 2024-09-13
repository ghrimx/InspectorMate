import base64
import logging

from qtpy import (Qt, QtCore, QtGui, QtWidgets)

from models.model import ProxyModel
from db.database import AppDatabase
from db.dbstructure import SignageType

from delegates.delegate import ReadOnlyDelegate

logger = logging.getLogger(__name__)


class TitleDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, model: ProxyModel, parent=None):
        super().__init__(parent=parent)
        self._proxy_model = model

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super().initStyleOption(option, index)

        title = index.data(Qt.ItemDataRole.DisplayRole)
        type_model_val: str = self._proxy_model.index(index.row(), self._proxy_model.sourceModel().Fields.Type.index).data(Qt.ItemDataRole.DisplayRole)
        signage_type: SignageType = AppDatabase.cache_signage_type.get(type_model_val)

        pix = QtGui.QPixmap()

        if signage_type is not None:
            img64str = signage_type.icon.strip()
            try:
                icon_bytearray = base64.b64decode(img64str)
            except UnicodeError:
                logger.error('Cannot decode string to bytes')
            except Exception as e:
                logger.error(e)
            else:
                pix.loadFromData(icon_bytearray)

        signage_type_icon = QtGui.QIcon(pix)

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = signage_type_icon
        option.text = title


class ProgressBarDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, model: ProxyModel, parent=None):
        super().__init__(parent)
        self._model = model

    def paint(self, painter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):

        evidence_eol = int(index.data(Qt.ItemDataRole.DisplayRole))

        evidence = self._model.data(self._model.index(index.row(), self._model.sourceModel().Fields.Evidence.index), Qt.ItemDataRole.DisplayRole)

        if evidence > 0:
            progress = int((evidence_eol / evidence) * 100)
        else:
            progress = 0

        progressBarOption = QtWidgets.QStyleOptionProgressBar()
        progressBarOption.rect = option.rect
        progressBarOption.minimum = 0
        progressBarOption.maximum = 100
        progressBarOption.progress = progress
        progressBarOption.text = f"{progress}%"
        progressBarOption.textVisible = True
        progressBarOption.state |= QtWidgets.QStyle.StateFlag.State_Horizontal

        if QtWidgets.QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, painter.brush())

        QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.ControlElement.CE_ProgressBar, progressBarOption, painter)


class EvidenceColumnDelegate(ReadOnlyDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        value = index.data(Qt.ItemDataRole.DisplayRole)

        if int(value) > 0:
            option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
            option.icon = QtGui.QIcon(':active-icon')
            option.text = ""
            option.displayAlignment = Qt.AlignmentFlag.AlignHCenter
            option.decorationAlignment = Qt.AlignmentFlag.AlignHCenter
        else:
            option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
            option.icon = QtGui.QIcon(':inactive-icon')
            option.text = ""
            option.displayAlignment = Qt.AlignmentFlag.AlignHCenter
            option.decorationAlignment = Qt.AlignmentFlag.AlignHCenter
