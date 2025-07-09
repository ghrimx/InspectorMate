import logging
from pathlib import Path, WindowsPath

from qtpy import (QtWidgets, QtCore, Qt, QtGui, QtSql)

from database.database import AppDatabase, Cache, Document

from models.model import (BaseRelationalTableModel, DatabaseField)
from utilities import (utils, config as mconf)

from qt_theme_manager import theme_icon_manager, Theme

logger = logging.getLogger(__name__)



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
    
    #  Reimplemented method to remove the decoration if not child
    def hasChildren(self, index):
        file_info = self.fileInfo(index)
        _dir = QtCore.QDir(file_info.absoluteFilePath())
        return bool(_dir.entryList(self.filter()))

    def create_models(self):
        self.folderpath = AppDatabase.activeWorkspace().evidence_path
        self.parent_folder = Path(self.folderpath)
        self.folderindex = self.setRootPath(str(self.folderpath))
        self.setFilter(QtCore.QDir.Filter.AllDirs | QtCore.QDir.Filter.NoDotAndDotDot)

        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self)
        self.proxy_index = self.proxy_model.mapFromSource(self.index(str(self.parent_folder)))
        # self.setIconProvider(EmptyIconProvider())  # Remove decoration

    def refresh(self):
        self.folderpath = AppDatabase.activeWorkspace().evidence_path
        self.parent_folder = Path(self.folderpath)
        self.folderindex = self.setRootPath(str(self.folderpath))
        self.proxy_model.setSourceModel(self)
        self.proxy_index = self.proxy_model.mapFromSource(self.index(str(self.parent_folder)))


class EvidenceModel(BaseRelationalTableModel):
    """Evidence model build from the document table of database"""  

    class Fields:
        Refkey = DatabaseField
        Title = DatabaseField
        Subtitle = DatabaseField
        Reference = DatabaseField
        Status = DatabaseField
        Type = DatabaseField
        Note = DatabaseField
        Filepath = DatabaseField
        CreationDatetime = DatabaseField
        ModificationDatetime = DatabaseField
        FileID = DatabaseField
        ID = DatabaseField
        SignageID = DatabaseField
        Workspace = DatabaseField
        
        @classmethod
        def fields(cls) -> list[DatabaseField]:
            """Return the list of fields.
                
            The order of item in the list matters and should match the fields order from the database.
            """
            return [
                    cls.Refkey,
                    cls.Title,
                    cls.Subtitle,
                    cls.Reference,
                    cls.Status,
                    cls.Type,
                    cls.Note,
                    cls.Filepath,
                    cls.CreationDatetime,
                    cls.ModificationDatetime,
                    cls.FileID,
                    cls.ID,
                    cls.SignageID,
                    cls.Workspace
                    ]
        
    def __init__(self):
        super(EvidenceModel, self).__init__()
        self.setEditStrategy(QtSql.QSqlTableModel.EditStrategy.OnFieldChange)
        self.cache_files: set = set()
        self.status_color_cache = {}

        self.setTable("document")
        self.init_fields()

        self.setRelation(self.Fields.Status.index,
                         QtSql.QSqlRelation("document_status", "uid", "name"))
        self.setRelation(self.Fields.Type.index,
                         QtSql.QSqlRelation("document_type", "type_id", "icon"))

        self.setFilter(f"workspace_id={AppDatabase.activeWorkspace().id}")

        self.setHeaderData(self.fieldIndex("status"),
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
        if not self.select():
            logger.error(f"Fail to select data from database - Error: {self.lastError().text()}")
        self.init_cache_files()

    def init_cache_files(self):
        for row in range(self.rowCount()):
            filepath = self.index(row, self.Fields.Filepath.index).data(Qt.ItemDataRole.DisplayRole)
            self.cache_files.add(WindowsPath(filepath))
        
        logger.info(f"Success! - Cache's size={len(self.cache_files)}")

    def init_fields(self):
        self.Fields.Refkey = DatabaseField('refkey', self.fieldIndex('refkey'), True)
        self.Fields.Title = DatabaseField('title', self.fieldIndex('title'), True)
        self.Fields.Subtitle = DatabaseField('subtitle', self.fieldIndex("subtitle"), False)
        self.Fields.Reference = DatabaseField('reference', self.fieldIndex("reference"), True)
        self.Fields.Status = DatabaseField('status', self.fieldIndex('status'), True)
        self.Fields.Type = DatabaseField('type', self.fieldIndex('type'), False)
        self.Fields.Note = DatabaseField('note', self.fieldIndex('note'), True)
        self.Fields.Filepath = DatabaseField('filepath', self.fieldIndex("filepath"), False)
        self.Fields.CreationDatetime = DatabaseField('creation_datetime', self.fieldIndex('creation_datetime'), False)
        self.Fields.ModificationDatetime = DatabaseField('modification_datetime', self.fieldIndex('modification_datetime'), False)
        self.Fields.FileID = DatabaseField('fileid', self.fieldIndex('fileid'), False)
        self.Fields.ID = DatabaseField('id', self.fieldIndex('id'), False)
        self.Fields.SignageID = DatabaseField('signage_id', self.fieldIndex('signage_id'), False)
        self.Fields.Workspace = DatabaseField('workspace_id', self.fieldIndex('workspace_id'), False)

    @classmethod
    def visibleFields(cls) -> list[int]:
        visible_fields = []
        for field in cls.Fields.fields():
            if field.visible:
                visible_fields.append(field.index)
        return visible_fields

    def insertDocument(self):
        files: set[Path] = set()
        files = utils.walkFolder(self.activeWorkspace().evidence_path)
        pattern = mconf.default_regex if mconf.settings.value("regex") is None else mconf.settings.value("regex")

        files.difference_update(self.cache_files)

        if files:
    
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount() + len(files))

            for file in files:

                refkey = self.findRefKeyFromPath(file.as_posix(), pattern)

                fileid = utils.queryFileID(file.as_posix())

                r: QtSql.QSqlRecord = self.record()
                r.setValue(self.Fields.Refkey.index, refkey)
                r.setValue(self.Fields.Title.index, file.stem)
                r.setValue(self.Fields.Subtitle.index, "")
                r.setValue(self.Fields.Reference.index, "")
                r.setValue(self.Fields.Type.index, AppDatabase.cache_doc_type.get(file.suffix.lower()) if AppDatabase.cache_doc_type.get(file.suffix.lower()) else 1)
                r.setValue(self.Fields.Note.index, "")
                r.setValue(self.Fields.Filepath.index, file.as_posix())
                r.setValue(self.Fields.CreationDatetime.index, str(file.stat().st_birthtime))
                r.setValue(self.Fields.ModificationDatetime.index, str(file.stat().st_mtime))
                r.setValue(self.Fields.FileID.index, fileid)
                r.setValue(self.Fields.Workspace.index, AppDatabase.activeWorkspace().id)
                inserted = self.insertRecord(-1, r)

                if inserted:
                    self.cache_files.add(file)
                else:
                    logger.error(f"Cannot insert: {file.as_posix()} - Error: {self.lastError().text()}")

            self.endInsertRows()

            self.beginResetModel()
            self.select()
            self.endResetModel()

    def document(self, index: QtCore.QModelIndex) -> Document:
        """Return Document dataclass from the database"""
        id = index.sibling(index.row(), self.Fields.ID.index).data(Qt.ItemDataRole.DisplayRole)
        document = AppDatabase.queryDocumentByID(id)
        return document

    def updateStatus(self, rows: list[int], status: int) -> bool:
        for row in rows:
            r = self.setData(self.index(row, self.Fields.Status.index), status, Qt.ItemDataRole.EditRole)

            if r:
                self.submit()

        self.refresh()

        return r

    def data(self, index: QtCore.QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.ForegroundRole:
            status_idx = index.sibling(index.row(), self.Fields.Status.index)  # Column with status text
            status = self.data(status_idx, Qt.ItemDataRole.DisplayRole)

            status_item = self.cacheEvidenceStatus().get(status)
            if status_item is not None :
                
                color_hex = status_item.color

                if color_hex == "#000000" and theme_icon_manager.get_theme() == Theme.DARK:
                    color_hex = theme_icon_manager.get_theme_color().name(QtGui.QColor.NameFormat.HexRgb)

                if color_hex:
                    return QtGui.QColor(color_hex)

        return super().data(index, role)

    def deleteRows(self, indexes: list[QtCore.QModelIndex]) -> bool:
        """Delete a row from the model and refresh the model"""
        for index in indexes:
            self.removeRow(index.row())

        self.refresh()

    def findRefKeyFromPath(self, filepath: str, pattern: str = "") -> str:
        # Remove evidence folder path from file segments
        segments = filepath.replace(AppDatabase.activeWorkspace().evidence_path, "")

        refkey = ""
        if pattern != "":
            # find refKey only in segments up to the evidence folder
            for item in segments.split('/'):
                refkey = utils.find_match(item, pattern)
                if refkey != "":
                    break
        
        return refkey

    def autoRefKey(self, rows: list[int]):
        regex = mconf.default_regex if mconf.settings.value("regex") is None else mconf.settings.value("regex")

        for row in rows:
            filepath = self.data(self.index(row, self.Fields.Filepath.index), Qt.ItemDataRole.DisplayRole)

            refkey = self.findRefKeyFromPath(filepath, regex)

            if refkey != "":
                record = self.record(row)
                record.setValue(self.Fields.Refkey.index, refkey)
                self.setRecord(row, record)

        res = self.submitAll()

        if res:
            self.refresh()

    def updateRefKey(self, rows: list[int], refkey: str):
        if refkey != "":
            self.beginResetModel()
            for row in rows:
                record = self.record(row)
                record.setValue(self.Fields.Refkey.index, refkey)
                self.setRecord(row, record)

            if self.submitAll():
                self.refresh()
            self.endResetModel()

    def updateFilePath(self, index: QtCore.QModelIndex, filepath: str):
        fpath = Path(filepath)

        if fpath.exists():
            record = self.record(index.row())
            self.beginResetModel()
            record.setValue(self.Fields.Filepath.index, fpath.as_posix())
            self.setRecord(index.row(), record)
            self.endResetModel()

            if self.submitAll():
                self.refresh()

    def reviewProgress(self):

        self.review_progress = {}

        for row in range(self.rowCount()):
            record = self.record(row)
            refkey = record.value(self.Fields.Refkey.index)
            status = record.value(self.Fields.Status.index)

            if refkey in self.review_progress:
                self.review_progress[refkey]["total"] += 1
            else:
                self.review_progress.update({refkey: {"progress": 0, "closed": 0, "total": 1}})
            if status == "Closed" or status == "Rejected":
                self.review_progress[refkey]["closed"] += 1

            self.review_progress[refkey]["progress"] = round(self.review_progress[refkey]["closed"] / self.review_progress[refkey]["total"], 2) * 100

        return self.review_progress
    
    def cacheEvidenceStatus(self) -> Cache:
        return AppDatabase.cache_document_status

    def activeWorkspace(self):
        return AppDatabase.activeWorkspace()
    
    def summary(self) -> list:

        vheaders = list(self.cacheEvidenceStatus().strkeys())
        vheaders.append("Total")
        hheaders = ["Count"]

        # Init data table
        data = [[0] * len(hheaders) for i in range(len(vheaders))] 

        # Populate data table
        for row in range(self.rowCount()):
            sname = self.index(row, self.Fields.Status.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
            s = self.cacheEvidenceStatus().get(sname).uid

            if s is not None:
                data[int(s)][0] += 1    # row data
                data[-1][0] += 1        # Total row

        return data, vheaders, hheaders