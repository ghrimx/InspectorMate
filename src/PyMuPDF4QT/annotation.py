import logging
from qtpy import QtCore, QtSql, QtWidgets, QtGui

from models.model import BaseRelationalTableModel, DatabaseField

logger = logging.getLogger(__name__)


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
        option.icon = QtGui.QIcon(":text-block")
        option.text = content

