import logging
from pathlib import Path

from qtpy import Signal, QtCore, Qt, QtSql, QSqlRelationalTableModel

from database.database import AppDatabase
from common import DatabaseField
from utilities import utils, config as mconf


logger = logging.getLogger(__name__)


class WorkerSignals(QtCore.QObject):
    result = Signal(object)
    error = Signal(Exception)
    finished = Signal()
    status = Signal(str)

class InsertDocumentsWorker(QtCore.QRunnable):
    def __init__(self,
                 model: "EvidenceModel",
                 evidence_path: Path,
                 cache_files: set[Path],
                 pattern: str,
                 fields):
        super().__init__()
        self.model = model
        self.evidence_path = evidence_path
        self.cache_files = cache_files
        self.pattern = pattern
        self.fields: EvidenceModel.Fields = fields
        self._abort = False
        self.signals = WorkerSignals()

    def abort(self):
        self._abort = True

    def run(self):
        try:
            files = utils.walkFolder(self.evidence_path)
            files.difference_update(self.cache_files)

            for file in files:
                if self._abort:
                    break

                refkey = utils.findRefKeyFromPath(file.as_posix(), 
                                                  self.pattern,
                                                  AppDatabase.activeWorkspace().evidence_path)
                fileid = utils.queryFileID(file.as_posix())

                r: QtSql.QSqlRecord = self.model.record()
                r.setValue(self.fields.Refkey.index, refkey)
                r.setValue(self.fields.Title.index, file.stem)
                r.setValue(self.fields.Subtitle.index, "")
                r.setValue(self.fields.Reference.index, "")
                r.setValue(self.fields.Note.index, "")
                r.setValue(self.fields.Filepath.index, file.as_posix())
                r.setValue(self.fields.CreationDatetime.index, str(file.stat().st_birthtime))
                r.setValue(self.fields.ModificationDatetime.index, str(file.stat().st_mtime))
                r.setValue(self.fields.FileID.index, fileid)
                r.setValue(self.fields.Workspace.index, AppDatabase.activeWorkspace().id)
                self.signals.result.emit(r)
        except Exception as e:
            logger.exception("Worker failed")
            self.signals.error.emit(e)
        finally:
            self.signals.finished.emit()


#################################################################
#                        EvidenceModel
#################################################################

class EvidenceModel(QSqlRelationalTableModel):
    """Evidence model build from the document table of database"""

    sigUpdateReviewProgress = Signal()

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
        def fields(self) -> list["DatabaseField"]:
            """Return all defined DatabaseField instances."""
            return [
                value for name, value in self.__dict__.items()
                if isinstance(value, DatabaseField)
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

        if not self.select():
            logger.error(f"Fail to select data from database - Error: {self.lastError().text()}")

        self._renameHeaders()
        self.init_cache_files()

    def refresh(self):
        self.submitAll()
        self.select()
        self.setFilter(f"workspace_id={AppDatabase.activeWorkspace().id}")
        return super().refresh()

    def init_cache_files(self):
        self.cache_files.clear()
        for row in range(self.rowCount()):
            filepath = self.index(row, self.Fields.Filepath.index).data(Qt.ItemDataRole.DisplayRole)
            self.cache_files.add(Path(filepath))
        
        logger.info(f"Success! - Cache's size={len(self.cache_files)}")

    def init_fields(self):
        self.Fields.Refkey = DatabaseField('Refkey', self.fieldIndex('refkey'), True)
        self.Fields.Title = DatabaseField('Title', self.fieldIndex('title'), True)
        self.Fields.Subtitle = DatabaseField('Subtitle', self.fieldIndex("subtitle"), False)
        self.Fields.Reference = DatabaseField('Reference', self.fieldIndex("reference"), True)
        self.Fields.Status = DatabaseField('Status', self.fieldIndex('status'), True)
        self.Fields.Type = DatabaseField('Type', self.fieldIndex('type'), False)
        self.Fields.Note = DatabaseField('Note', self.fieldIndex('note'), True)
        self.Fields.Filepath = DatabaseField('Filepath', self.fieldIndex("filepath"), False)
        self.Fields.CreationDatetime = DatabaseField('creation_datetime', self.fieldIndex('creation_datetime'), False)
        self.Fields.ModificationDatetime = DatabaseField('modification_datetime', self.fieldIndex('modification_datetime'), False)
        self.Fields.FileID = DatabaseField('fileid', self.fieldIndex('fileid'), False)
        self.Fields.ID = DatabaseField('id', self.fieldIndex('id'), False)
        self.Fields.SignageID = DatabaseField('signage_id', self.fieldIndex('signage_id'), False)
        self.Fields.Workspace = DatabaseField('workspace_id', self.fieldIndex('workspace_id'), False)
        
    def _renameHeaders(self):
        for field in self.Fields.fields():
            self.setHeaderData(field.index, QtCore.Qt.Orientation.Horizontal, field.name)

    def _onDocumentsReady(self, record: QtSql.QSqlRecord):
        """Apply insertions to model in the GUI thread."""
        if not record:
            return

        inserted = self.insertRecord(-1, record)
        if inserted:
            self.inserted_count += 1 
            self.cache_files.add(Path(record.value(self.Fields.Filepath.index)))
        else:
            logger.error(self.lastError().text())

    def insertDocumentAsync(self,
                            on_finished: callable = None):
        evidence_path = AppDatabase.activeWorkspace().evidence_path
        cache_files = self.cache_files
        pattern = mconf.default_regex if mconf.settings.value("regex") is None else mconf.settings.value("regex")

        pool = QtCore.QThreadPool().globalInstance()
        worker = InsertDocumentsWorker(model=self,
                                       evidence_path=evidence_path,
                                       cache_files=cache_files,
                                       pattern=pattern,
                                       fields=self.Fields
                                       )

        worker.signals.result.connect(self._onDocumentsReady)
        if on_finished:
            worker.signals.finished.connect(lambda: on_finished(f"[Evidence(s) inserted: {self.inserted_count}]"))
            worker.signals.finished.connect(self.refresh)
            worker.signals.finished.connect(self.sigUpdateReviewProgress)
            worker.signals.finished.connect(AppDatabase.update_document_signage_id)
        self.inserted_count = 0
        pool.start(worker)
    
    def updateStatus(self, rows: list[int], status_id: int):
        self.database().transaction()
        try:
            for row in rows:
                idx = self.index(row, self.Fields.Status.index)
                self.setData(idx, status_id, role=QtCore.Qt.ItemDataRole.EditRole)

            # Commit all changes
            if not self.submitAll():
                logger.error("Failed to update status:", self.lastError().text())
                self.database().rollback()
                return False
            else:
                self.database().commit()
        except Exception as e:
            logger.error("Error updating status:", e)
            self.database().rollback()
            return False
        self.sigUpdateReviewProgress.emit()
        return True

    def deleteRows(self, rows: list[int]) -> bool:
        """Delete a row from the model and refresh the model"""
        if not rows:
            return False

        removed_cnt = 0

        rows = sorted({r for r in rows}, reverse=True)
        for row in rows:
            filepath = self.index(row, self.Fields.Filepath.index).data(Qt.ItemDataRole.DisplayRole)
            if filepath:
                self.cache_files.discard(Path(filepath))

            if self.removeRow(row, QtCore.QModelIndex()):
                removed_cnt += 1
            else:
                logger.error(f"Unable to remove: {filepath}")

        self.refresh()
        self.sigUpdateReviewProgress.emit()
        return f'[Evidence(s) removed: {removed_cnt} of {len(rows)}]'

    def autoRefKey(self, rows: list[int]):
        """
            - Get filepath from the fileid
            - Get the Refkey from the filepath
            - Update the filepath and the refkey 
        """
        regex = mconf.default_regex if mconf.settings.value("regex") is None else mconf.settings.value("regex")
        self.refresh()
        for row in rows:
            update_filepath = False
            filepath = self.data(self.index(row, self.Fields.Filepath.index), Qt.ItemDataRole.DisplayRole)

            if not Path(filepath).is_file():
                fileid = self.data(self.index(row, self.Fields.FileID.index), Qt.ItemDataRole.DisplayRole)
                new_filepath = Path(utils.queryFileNameByID(fileid)).as_posix()
                if not Path(new_filepath).is_file():
                    logger.error(f"File '{filepath}' not found. Cannot detect refkey.")
                    continue
                else:
                    update_filepath = True
                    filepath = new_filepath

            refkey = utils.findRefKeyFromPath(filepath, regex, AppDatabase.activeWorkspace().evidence_path)
            
            logger.debug(f'refkey:{refkey}')

            if refkey != "":
                record = self.record(row)
                record.setValue(self.Fields.Refkey.index, refkey)
                if update_filepath:
                    record.setValue(self.Fields.Filepath.index, filepath)
                if not self.setRecord(row, record):
                    logger.error(f'{self.lastError().text()}')

        self.refresh()
        self.init_cache_files()
        AppDatabase.update_document_signage_id()
        self.sigUpdateReviewProgress.emit()

    def updateRefKey(self, rows: list[int], refkey: str):
        if refkey != "":
            for row in rows:
                record = self.record(row)
                record.setValue(self.Fields.Refkey.index, refkey)
                if not self.setRecord(row, record):
                    logger.error(f"{self.lastError().text()}")
            self.refresh()
            AppDatabase.update_document_signage_id()
            self.sigUpdateReviewProgress.emit()

    def updateFilePath(self, index: QtCore.QModelIndex, filepath: str):
        fpath = Path(filepath)

        if fpath.exists():
            record = self.record(index.row())
            record.setValue(self.Fields.Filepath.index, fpath.as_posix())
            self.refresh()
    
    def summary(self) -> list:
        vheaders = []
        status_model = self.relationModel(self.Fields.Status.index)
        for row in range(status_model.rowCount()):
            record = status_model.record(row)
            vheaders.append(record.value("name"))
        vheaders.append("Total")
        hheaders = ["Count"]

        data = [[0] for _ in range(len(vheaders))] 

        # Populate data table
        for row in range(self.rowCount()):
            sname = self.index(row, self.Fields.Status.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
            s = vheaders.index(sname)

            if s is not None:
                data[int(s)][0] += 1    # row data
                data[-1][0] += 1        # Total row

        return data, vheaders, hheaders
