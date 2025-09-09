import logging
from dataclasses import dataclass
from qtpy import QtCore, QtSql, QtWidgets, QtCore, Signal, Slot

from models.model import BaseRelationalTableModel, DatabaseField, ProxyModel
from qt_theme_manager import theme_icon_manager

from widgets.fitcontenteditor import FitContentTextEdit

logger = logging.getLogger(__name__)

@dataclass
class Annotation:
    text: str = ""
    uid: str = ""
    comment: str = ""
    pagelabel: str = ""
    pno: int = -1

class AnnotationModel(BaseRelationalTableModel):

    class Fields:
        Uid: DatabaseField
        DocumentID = DatabaseField
        Text = DatabaseField
        Comment = DatabaseField
        Color = DatabaseField
        Position = DatabaseField
        PageLabel = DatabaseField
        PageNumber = DatabaseField

    def __init__(self):
        super(AnnotationModel, self).__init__()
        self.setEditStrategy(QtSql.QSqlTableModel.EditStrategy.OnFieldChange)
        self.setTable("annotations")
        self.initFields()
        self._cache_annotations = []

        if not self.select():
            logger.error(f"Fail to select data from database - Error: {self.lastError().text()}")

    def initFields(self):
        self.Fields.Uid = DatabaseField('uid', self.fieldIndex('uid'), False)
        self.Fields.DocumentID = DatabaseField('document_id', self.fieldIndex('document_id'), False)
        self.Fields.Text = DatabaseField('text', self.fieldIndex('text'), True)
        self.Fields.Comment = DatabaseField('comment', self.fieldIndex('comment'), True)
        self.Fields.Color = DatabaseField('color', self.fieldIndex('color'), False)
        self.Fields.Position = DatabaseField('position', self.fieldIndex('position'), False)
        self.Fields.PageLabel = DatabaseField('page_label', self.fieldIndex('page_label'), True)
        self.Fields.PageNumber = DatabaseField('page_number', self.fieldIndex('page_number'), True)

    def cache(self) -> list:
        return self._cache_annotations
    
    def initCache(self, doc_id: str):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT text,
                                position
                            FROM annotations
                            WHERE document_id = :doc_id;
                            """)
        query.bindValue(":doc_id", doc_id)
        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
            return False
        else:
            while query.next():
                self._cache_annotations.append({"text":query.value(0), "position":query.value(1)})
            return True

    def remove(self):
        ...


class AnnotationDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        pno = index.sibling(index.row(), AnnotationModel.Fields.PageNumber.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        text: str = index.sibling(index.row(), AnnotationModel.Fields.Text.index).data(QtCore.Qt.ItemDataRole.DisplayRole)

        if text.strip() != "":
            content = f"{text.strip()}, page {pno+1}"   
        else:
            content = f"page {pno+1}" 

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        option.icon = theme_icon_manager.get_icon(":text-block")
        option.text = content

class AnnotationWidget(QtWidgets.QWidget):
    sigAnnotationChanged = Signal(Annotation)
    
    def __init__(self, annot: Annotation, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Annotation Viewer")
        self._annotation = annot
        formlayout = QtWidgets.QFormLayout()
        self.setLayout(formlayout)

        self.comment = FitContentTextEdit()
        self.comment.setPlainText(self._annotation.comment)

        self.text = FitContentTextEdit(True)
        self.text.setPlainText(self._annotation.text)
        self.text.setStyleSheet("QTextEdit { background: #f2f2f2; }")
        
        formlayout.addRow("page", QtWidgets.QLabel(str(self._annotation.pno)))
        formlayout.addRow("text", self.text)
        formlayout.addRow("comment", self.comment)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        formlayout.addWidget(self.buttonBox)

        # Connection
        self.comment.textChanged.connect(self.onCommentChanged)

    def onCommentChanged(self):
        text = self.comment.toPlainText()
        self._annotation.comment = text

    def accept(self):
        self.sigAnnotationChanged.emit(self._annotation)
        self.close()

    def reject(self):
        self.close()
        

class AnnotationPane(QtWidgets.QWidget):
    clicked = Signal(QtCore.QModelIndex)

    def __init__(self, model: AnnotationModel, parent = None):
        super().__init__(parent)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        button_box = QtWidgets.QHBoxLayout()
        self.search_field = QtWidgets.QLineEdit()
        self.remove_btn = QtWidgets.QPushButton()
        self.remove_btn.setIcon(theme_icon_manager.get_icon(':delete-bin2'))
        button_box.addWidget(self.search_field)
        button_box.addWidget(self.remove_btn)

        vbox.addLayout(button_box)

        self.view = QtWidgets.QListView()
        self.proxy = ProxyModel(model)
        self.view.setModel(self.proxy)
        self.view.setModelColumn(model.Fields.Text.index)
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.view.setAlternatingRowColors(True)
        self.view.setStyleSheet("alternate-background-color: aliceblue;")

        annotation_delegate = AnnotationDelegate()
        self.view.setItemDelegate(annotation_delegate)

        vbox.addWidget(self.view)

        # Connection
        self.view.clicked.connect(self.clicked)
        self.search_field.textChanged.connect(self.searchFor)
        self.view.doubleClicked.connect(self.onAnnotationOpen)

    def searchFor(self):
        pattern = self.search_field.text()
        model: AnnotationModel = self.proxy.sourceModel()
        self.proxy.setUserFilter(pattern,
                                 [model.Fields.Text.index])
        self.proxy.invalidateFilter()

    @Slot(QtCore.QModelIndex)
    def onAnnotationOpen(self, index: QtCore.QModelIndex):
        pno = index.sibling(index.row(), AnnotationModel.Fields.PageNumber.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        text = index.sibling(index.row(), AnnotationModel.Fields.Text.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        comment = index.sibling(index.row(), AnnotationModel.Fields.Comment.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        annot = Annotation(text=text, pno=pno+1, comment=comment)
        self.annot_popup = AnnotationWidget(annot)
        self.annot_popup.show()
