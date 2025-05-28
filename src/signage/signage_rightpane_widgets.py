# Standard library imports.

# Related third party imports.
from qtpy import QtWidgets, QtCore, QtSql, Slot, Signal

# Local application/library specific imports.
from signage.signage_model import SignageTreeModel

from widgets.fitcontenteditor import FitContentTextEdit
from widgets.textinput import LineInput
from widgets.noteeditor import NoteEditor


class SignageInfoWidget(QtWidgets.QWidget):

    class Signals(QtCore.QObject):
        delete = Signal()
        resetFilters = Signal()
        updateStatus = Signal(int)
        updateOwner = Signal(str)
        updateType = Signal(int)
        updateTitle = Signal(str)
        updateRefkey = Signal(str)
        updatePrivateNote = Signal(str)
        updatePublicNote = Signal(str)

    def __init__(self, signage_status: dict, signage_type: dict, parent = None):
        super(SignageInfoWidget, self).__init__(parent)
        self._signage_status = signage_status
        self._signage_type = signage_type
        self.signals = self.Signals(self)
        self.initUI()

    def initUI(self):

        formlayout = QtWidgets.QFormLayout(self)
        self.setLayout(formlayout)

        # Title
        self.title_textedit = FitContentTextEdit(False)
        self.title_textedit.setAcceptRichText(False)
        self.title_textedit.sigTextEdited.connect(self.signals.updateTitle)

        # Status
        self.status_combobox = QtWidgets.QComboBox()
        for key, item in self._signage_status.items():
            self.status_combobox.insertItem(key, item.name, item)
        self.status_combobox.activated.connect(self.mapSignals)

        # Refkey
        self.refkey_field = LineInput()
        self.refkey_field.sigTextEdited.connect(self.signals.updateRefkey)

        # Type
        self.type_combobox = QtWidgets.QComboBox()
        for key, item in self._signage_type.items():
            self.type_combobox.insertItem(key, item.name, item)
        self.type_combobox.activated.connect(self.mapSignals)
        
        # Owner
        self.owner_lineinput= LineInput()
        self.owner_lineinput.sigTextEdited.connect(self.signals.updateOwner)

        # Source
        self.source_label = FitContentTextEdit(True)
        self.source_label.setStyleSheet("color: grey;")

        # Evidence
        self.evidence_label = QtWidgets.QLineEdit()
        self.evidence_label.setReadOnly(True)
        self.evidence_label.setStyleSheet("color: grey;")

        # Signage id
        self.id_label = QtWidgets.QLineEdit()
        self.id_label.setReadOnly(True)
        self.id_label.setStyleSheet("color: grey;")

        # Signage Parent id
        self.parentid_label = QtWidgets.QLineEdit()
        self.parentid_label.setReadOnly(True)
        self.parentid_label.setStyleSheet("color: grey;")

        # Creation date
        self.creation_date = QtWidgets.QLineEdit()
        self.creation_date.setReadOnly(True)
        self.creation_date.setStyleSheet("color: grey;")

        # Private & Public Note
        self.note = NoteEditor(parent=self)
        self.note.editor.sigTextEdited.connect(self.signals.updatePrivateNote)
        self.public_note = NoteEditor(parent=self)
        self.public_note.editor.sigTextEdited.connect(self.signals.updatePublicNote)
        self.public_note.editor.setStyleSheet("border: 2px solid red;")

        formlayout.addRow('Title', self.title_textedit)
        formlayout.addRow('Refkey', self.refkey_field)
        formlayout.addRow('Status', self.status_combobox)
        formlayout.addRow('Type', self.type_combobox)
        formlayout.addRow('Owner', self.owner_lineinput)
        formlayout.addRow('Source', self.source_label)
        formlayout.addRow('Evidence', self.evidence_label)
        formlayout.addRow('id', self.id_label)
        formlayout.addRow('Creation date', self.creation_date)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, 
                                       QtWidgets.QSizePolicy.Policy.Expanding)
        formlayout.addItem(spacer)

    def setupMapper(self, model: SignageTreeModel):
        # Combobox model
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(model)
        self.mapper.setItemDelegate(QtSql.QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.status_combobox, model.Fields.Status.index, b"currentIndex")
        self.mapper.addMapping(self.title_textedit, model.Fields.Title.index, b"plainText")
        self.mapper.addMapping(self.refkey_field, model.Fields.Refkey.index)
        self.mapper.addMapping(self.type_combobox, model.Fields.Type.index, b"currentIndex")
        self.mapper.addMapping(self.owner_lineinput, model.Fields.Owner.index)
        self.mapper.addMapping(self.source_label, model.Fields.Source.index, b"plainText")
        self.mapper.addMapping(self.evidence_label, model.Fields.Evidence.index)
        self.mapper.addMapping(self.id_label, model.Fields.ID.index)
        self.mapper.addMapping(self.parentid_label, model.Fields.ParentID.index)
        self.mapper.addMapping(self.creation_date, model.Fields.CreationDatetime.index)
        self.mapper.addMapping(self.note.editor, model.Fields.Note.index)
        self.mapper.addMapping(self.public_note.editor, model.Fields.PublicNote.index)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.AutoSubmit)

    @Slot(QtCore.QModelIndex, QtCore.QModelIndex)
    def updatePanelFields(self, currentIndex: QtCore.QModelIndex, previousIndex: QtCore.QModelIndex):
        """Update the mapper index upon Signage table row changed"""
        self.mapper.setRootIndex(currentIndex.parent())
        self.mapper.setCurrentModelIndex(currentIndex)

    @Slot()
    def mapSignals(self):
        """Prepare data prior emitting signal"""
        sender = self.sender()

        match sender:
            case self.status_combobox:
                signage_status = self.status_combobox.currentData()
                self.signals.updateStatus.emit(signage_status.uid)
            case self.type_combobox:
                signage_type = self.type_combobox.currentData()
                self.signals.updateType.emit(signage_type.uid)
            case _:
                return

        




