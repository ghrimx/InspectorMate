from qtpy import QtWidgets, QtCore, Signal
from PyQt6.QtSql import QSqlRelationalDelegate

from evidence.evidencemodel import EvidenceModel

from database.dbstructure import Document

from widgets.fitcontenteditor import FitContentTextEdit
from widgets.richtexteditor import RichTextEditor


class DocInfoWidget(QtWidgets.QWidget):
    sigStatusUpdated = Signal()
    sigRefkeyUpdated = Signal()

    def __init__(self, model: EvidenceModel, parent=None):
        super(DocInfoWidget, self).__init__(parent=parent)
        self._model = model

        formlayout = QtWidgets.QFormLayout(self)
        self.setLayout(formlayout)

        self.status = QtWidgets.QComboBox()
        self.status_model = self._model.relationModel(self._model.Fields.Status.index)
        self.status.setModel(self.status_model)
        self.status.setModelColumn(1)
        self.status.activated.connect(self.sigStatusUpdated)

        self.title = FitContentTextEdit(False)
        self.refkey = QtWidgets.QLineEdit()
        self.refkey.editingFinished.connect(self.sigRefkeyUpdated)
        self.subtitle = QtWidgets.QLineEdit()
        self.reference = QtWidgets.QLineEdit()
        self.filename = FitContentTextEdit(True)
        self.filename.setStyleSheet("color: grey;")
        self.note = RichTextEditor.fromMapper(bar=False, parent=self)
        self.signage_id = QtWidgets.QLineEdit()
        self.signage_id.setReadOnly(True)
        self.signage_id.setStyleSheet("color: grey;")

        formlayout.addRow("Status", self.status)
        formlayout.addRow("Refkey", self.refkey)
        formlayout.addRow("Title", self.title)
        formlayout.addRow("SubTitle", self.subtitle)
        formlayout.addRow("Reference", self.reference)
        formlayout.addRow("Filename", self.filename)
        formlayout.addRow("Signage id", self.signage_id)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)

        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(model)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.status, model.Fields.Status.index)
        self.mapper.addMapping(self.refkey, model.Fields.Refkey.index)
        self.mapper.addMapping(self.title, model.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.subtitle, model.Fields.Subtitle.index)
        self.mapper.addMapping(self.reference, model.Fields.Reference.index)
        self.mapper.addMapping(self.filename, model.Fields.Filepath.index, b"plainText")
        self.mapper.addMapping(self.note.editor, model.Fields.Note.index)
        self.mapper.addMapping(self.signage_id, model.Fields.SignageID.index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)      

    def update_mapped_widgets(self): #TODO
        if self._model.rowCount():
            self.mapper.toFirst()
        else:
            self.mapper.setCurrentIndex(-1)
            for section in range(self._model.columnCount()):
                widget: QtWidgets.QWidget = self.mapper.mappedWidgetAt(section)
                if not widget:
                    pass
                elif isinstance(widget, QtWidgets.QComboBox):
                    widget.setCurrentIndex(-1)
                else:
                    widget.clear()


