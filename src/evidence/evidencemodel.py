import logging
from pathlib import Path
from os import DirEntry

from qtpy import (QtWidgets, QtCore, Qt, QtGui, QtSql)

from db.database import AppDatabase
from db.dbstructure import Document

from models.model import (BaseRelationalTableModel, DatabaseField)

from utilities import (utils, config as mconf)

logger = logging.getLogger(__name__)


class DocStatusSummary(QtSql.QSqlQueryModel):
    """Model for document Status summary table"""
    def __init__(self):
        super().__init__()

    def data(self, index: QtCore.QModelIndex, role=Qt.ItemDataRole):
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() > 0:
            return Qt.AlignmentFlag.AlignCenter
        return super().data(index, role)

    def refresh(self):
        self.setQuery(AppDatabase.docStatuSummary())


class EmptyIconProvider(QtWidgets.QFileIconProvider):
    """Disable the icon provider used to decorate the QFileSystemModel"""
    def icon(self, _):
        return QtGui.QIcon()


class DocExplorerModel(QtGui.QFileSystemModel):
    """Model for the navigation pane (FileSystemModel) to filter the document based on their location in the directory tree"""
    def __init__(self) -> None:
        super().__init__()
        self.create_models()

    def get_path(self, selected_index):
        folderpath = self.filePath(self.proxy_model.mapToSource(selected_index))
        return Path(folderpath)

    def create_models(self):
        self.folderpath = AppDatabase.active_workspace.evidence_path
        self.parent_folder = Path(self.folderpath)
        self.folderindex = self.setRootPath(str(self.folderpath))
        self.setFilter(QtCore.QDir.Filter.AllDirs | QtCore.QDir.Filter.NoDotAndDotDot)

        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self)
        self.proxy_index = self.proxy_model.mapFromSource(self.index(str(self.parent_folder)))
        self.setIconProvider(EmptyIconProvider())  # Remove decoration

    def refresh(self):
        self.folderpath = AppDatabase.active_workspace.evidence_path
        self.parent_folder = Path(self.folderpath)
        self.folderindex = self.setRootPath(str(self.folderpath))
        self.proxy_model.setSourceModel(self)
        self.proxy_index = self.proxy_model.mapFromSource(self.index(str(self.parent_folder)))


class DocTableModel(BaseRelationalTableModel):
    """Document model build from the document table of database"""

    class Fields:
        ID = DatabaseField
        RefKey = DatabaseField
        Status = DatabaseField
        Type = DatabaseField
        Title = DatabaseField
        Subtitle = DatabaseField
        Reference = DatabaseField
        Note = DatabaseField
        Filename = DatabaseField
        Filepath = DatabaseField
        Folderpath = DatabaseField
        Workspace = DatabaseField
        ModificationDate = DatabaseField
        CreationDate = DatabaseField
        Display = DatabaseField
        FileID = DatabaseField

    def __init__(self):
        super().__init__()
        self.status_color_cache = {}

        self.setTable("document")
        self.init_fields()

        self.setRelation(self.Fields.Status.index,
                         QtSql.QSqlRelation("document_status", "status_id", "Status"))
        self.setRelation(self.Fields.Type.index,
                         QtSql.QSqlRelation("document_type", "type_id", "icon"))

        self.setFilter(f"workspace_id={AppDatabase.active_workspace.id}")

        self.setHeaderData(self.fieldIndex("status_id"),
                           Qt.Orientation.Horizontal,
                           "Status")
        self.setHeaderData(self.fieldIndex("title"),
                           Qt.Orientation.Horizontal,
                           "Title")
        self.setHeaderData(self.fieldIndex("subtitle"),
                           Qt.Orientation.Horizontal,
                           "SubTitle")
        self.setHeaderData(self.fieldIndex("reference"),
                           Qt.Orientation.Horizontal,
                           "Reference")
        self.setHeaderData(self.fieldIndex("note"),
                           Qt.Orientation.Horizontal,
                           "Note")
        self.select()

    def init_fields(self):
        self.Fields.ID = DatabaseField('doc_id', self.fieldIndex('doc_id'), False)
        self.Fields.RefKey = DatabaseField('refKey', self.fieldIndex('refKey'), True)
        self.Fields.Title = DatabaseField('title', self.fieldIndex('title'), True)
        self.Fields.Status = DatabaseField('status_id', self.fieldIndex('status_id'), True)
        self.Fields.Type = DatabaseField('type_id', self.fieldIndex('type_id'), False)
        self.Fields.Subtitle = DatabaseField('subtitle', self.fieldIndex("subtitle"), False)
        self.Fields.Reference = DatabaseField('reference', self.fieldIndex("reference"), True)
        self.Fields.Filename = DatabaseField('filename', self.fieldIndex("filename"), False)
        self.Fields.Filepath = DatabaseField('filepath', self.fieldIndex("filepath"), False)
        self.Fields.Folderpath = DatabaseField('dirpath', self.fieldIndex("dirpath"), False)
        self.Fields.Note = DatabaseField('note', self.fieldIndex('note'), True)
        self.Fields.Workspace = DatabaseField('workspace_id', self.fieldIndex('workspace_id'), False)
        self.Fields.ModificationDate = DatabaseField('modification_date', self.fieldIndex('modification_date'), False)
        self.Fields.CreationDate = DatabaseField('creation_date', self.fieldIndex('creation_date'), False)
        self.Fields.Display = DatabaseField('display', self.fieldIndex('display'), False)
        self.Fields.FileID = DatabaseField('fileid', self.fieldIndex('fileid'), False)

    def insertDocument(self):
        files = []
        files = utils.folder_scanner(AppDatabase.active_workspace.evidence_path)

        pattern = mconf.default_regex if mconf.settings.value("regex") is None else mconf.settings.value("regex")

        self.layoutAboutToBeChanged.emit()

        if files:
            file: DirEntry
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount() + len(files))

            for file in files:

                refkey = self.findRefKeyFromPath(file.path, pattern)

                fileid = utils.queryFileID(file.path)

                r = self.record()
                r.setValue(self.Fields.Display.index, 1)
                r.setValue(self.Fields.RefKey.index, refkey)
                r.setValue(self.Fields.Filename.index, file.name)
                r.setValue(self.Fields.Filepath.index, Path(file.path).as_posix())
                r.setValue(self.Fields.Title.index, Path(file.name).stem)
                r.setValue(self.Fields.ModificationDate.index, str(file.stat().st_mtime))
                r.setValue(self.Fields.CreationDate.index, str(file.stat().st_birthtime))
                r.setValue(self.Fields.Folderpath.index, Path(file.path).parent.as_posix())
                r.setValue(self.Fields.Type.index, AppDatabase.cache_doc_type.get(Path(file.path).suffix.lower()) if AppDatabase.cache_doc_type.get(Path(file.path).suffix.lower()) else 1)
                r.setValue(self.Fields.Workspace.index, AppDatabase.active_workspace.id)
                r.setValue(self.Fields.FileID.index, fileid)
                self.insertRecord(-1, r)

            self.endInsertRows()
            self.select()

            self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
            self.layoutChanged.emit()

    def document(self, selected_index: QtCore.QModelIndex) -> Document:
        """
        Get the infos of the selected evidence

            Return:
                evidence: dataclass object
        """
        selected_row = selected_index.row()
        id_idx = self.index(selected_row, self.Fields.ID.index)
        doc_id = self.data(id_idx, Qt.ItemDataRole.DisplayRole)

        doc = AppDatabase.queryDocumentByID(doc_id)
        return doc

    def updateStatus(self, rows: list[int], status: int):
        for row in rows:
            res = self.setData(self.index(row, self.Fields.Status.index), status, Qt.ItemDataRole.EditRole)

            if res:
                self.submit()

        self.refresh()

    def data(self, index: QtCore.QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.ForegroundRole:
            status_idx = self.index(index.row(), self.Fields.Status.index)  # Column with status text
            status = self.data(status_idx, Qt.ItemDataRole.DisplayRole)

            if status:
                if status not in self.status_color_cache:
                    self.status_color_cache[status] = self.fetch_status_color(status)

                color_hex = self.status_color_cache[status]
                if color_hex:
                    return QtGui.QColor(color_hex)

        return super().data(index, role)

    def fetch_status_color(self, status):
        query = QtSql.QSqlQuery()
        query.prepare("SELECT color FROM document_status WHERE status = ?")
        query.addBindValue(status)
        if query.exec() and query.next():
            return query.value(0)
        return None

    def deleteRows(self, indexes: list[QtCore.QModelIndex]) -> bool:
        """Delete a row from the model and refresh the model"""
        for index in indexes:
            self.removeRow(index.row())

        self.refresh()

    def findRefKeyFromPath(self, filepath: str, pattern: str = "") -> str:
        # set of path segments
        folder_segments = set(Path(AppDatabase.active_workspace.evidence_path).parents)
        folder_segments.add(Path(AppDatabase.active_workspace.evidence_path))
        file_segments = set(Path(filepath).parents)
        file_segments.add(Path(filepath))

        refkey = ""
        if pattern != "":
            # find refKey only in segments up to the monitored folder
            for item in [x for x in file_segments if x not in folder_segments]:
                refkey = utils.find_match(item.name, pattern)
                if refkey != "":
                    break
        
        return refkey

    def autoRefKey(self, rows: list[int]):
        regex = mconf.default_regex if mconf.settings.value("regex") is None else mconf.settings.value("regex")

        for row in rows:
            filepath = self.data(self.index(row, self.Fields.Filepath.index), Qt.ItemDataRole.DisplayRole)
            fpath = Path(filepath)

            refkey = self.findRefKeyFromPath(fpath, regex)

            if refkey != "":
                record = self.record(row)
                record.setValue(self.Fields.RefKey.index, refkey)
                self.setRecord(row, record)

        res = self.submitAll()

        if res:
            self.refresh()

    def updateRefKey(self, rows: list[int], refkey: str):
        if refkey != "":
            for row in rows:
                record = self.record(row)
                record.setValue(self.Fields.RefKey.index, refkey)
                self.setRecord(row, record)

            res = self.submitAll()

            if res:
                self.refresh()
        else:
            return

    def updateFilePath(self, row: int, filepath: str):
        fpath = Path(filepath)

        if fpath.exists():
            record = self.record(row)
            record.setValue(self.Fields.Folderpath.index, fpath.parent.as_posix())
            record.setValue(self.Fields.Filename.index, fpath.name)
            record.setValue(self.Fields.Filepath.index, fpath.as_posix())
            self.setRecord(row, record)

            res = self.submitAll()

            if res:
                self.refresh()

    def reviewProgress(self):

        self.review_progress = {}

        for row in range(self.rowCount()):
            record = self.record(row)
            refkey = record.value(self.Fields.RefKey.index)
            status = record.value(self.Fields.Status.index)

            if refkey in self.review_progress:
                self.review_progress[refkey]["total"] += 1
            else:
                self.review_progress.update({refkey: {"progress": 0, "closed": 0, "total": 1}})
            if status == "Closed" or status == "Rejected":
                self.review_progress[refkey]["closed"] += 1

            self.review_progress[refkey]["progress"] = round(self.review_progress[refkey]["closed"] / self.review_progress[refkey]["total"], 2) * 100

        return self.review_progress
