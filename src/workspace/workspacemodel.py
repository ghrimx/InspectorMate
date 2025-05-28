import logging

from datetime import datetime
from qtpy import QtCore, QtSql

from database.database import AppDatabase
from models.objectclass import (Workspace, DatabaseField)
from models.model import BaseRelationalTableModel

logger = logging.getLogger(__name__)


class WorkspaceModel(BaseRelationalTableModel):

    class Fields:
        ID = DatabaseField
        Name = DatabaseField
        State = DatabaseField
        Rootpath = DatabaseField
        EvidencePath = DatabaseField
        NotebookPath = DatabaseField
        OneNoteSection = DatabaseField
        CreationDate = DatabaseField
        ModificationDate = DatabaseField
        Reference = DatabaseField    

    def __init__(self) -> None:
        super().__init__()

        self.setTable('workspace')
        self.init_index()
        self.select()

        self.setHeaderData(self.fieldIndex('workspace_id'),
                           QtCore.Qt.Orientation.Horizontal,
                           "ID")
        self.setHeaderData(self.fieldIndex('name'),
                           QtCore.Qt.Orientation.Horizontal,
                           "Name")
        self.setHeaderData(self.fieldIndex('state'),
                           QtCore.Qt.Orientation.Horizontal,
                           "State")
        self.setHeaderData(self.fieldIndex('root'),
                           QtCore.Qt.Orientation.Horizontal,
                           "Path")
        self.setHeaderData(self.fieldIndex('creation_date'),
                           QtCore.Qt.Orientation.Horizontal,
                           "Creation Date")
        self.setHeaderData(self.fieldIndex('modification_date'),
                           QtCore.Qt.Orientation.Horizontal,
                           "Modification Date")

    def init_index(self):
        WorkspaceModel.Fields.ID = DatabaseField("workspace_id", self.fieldIndex('workspace_id'), False)
        WorkspaceModel.Fields.Name = DatabaseField("name", self.fieldIndex('name'), True)
        WorkspaceModel.Fields.State = DatabaseField("state", self.fieldIndex('state'), True)
        WorkspaceModel.Fields.Rootpath = DatabaseField("root", self.fieldIndex('root'), False)
        WorkspaceModel.Fields.EvidencePath = DatabaseField("attachments_path", self.fieldIndex('attachments_path'), False)
        WorkspaceModel.Fields.NotebookPath = DatabaseField("notebook_path", self.fieldIndex('notebook_path'), False)
        WorkspaceModel.Fields.OneNoteSection = DatabaseField("onenote_section", self.fieldIndex('onenote_section'), False)
        WorkspaceModel.Fields.CreationDate = DatabaseField("creation_date", self.fieldIndex('creation_date'), False)
        WorkspaceModel.Fields.ModificationDate = DatabaseField("modification_date", self.fieldIndex('modification_date'), False)
        WorkspaceModel.Fields.Reference = DatabaseField("reference", self.fieldIndex('reference'), True)

    def insertWorkspace(self, workspace: Workspace) -> tuple[bool,str]:
        record = self.record()
        record.setValue('name', workspace.name)
        record.setValue('reference', workspace.reference)
        record.setValue('root', workspace.rootpath)
        record.setValue('state', workspace.state)
        record.setValue('attachments_path', workspace.evidence_path)
        record.setValue('notebook_path', workspace.notebook_path)
        record.setValue('onenote_section', workspace.onenote_section)
        record.setValue('creation_date', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        record.setValue('modification_date', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        inserted = self.insertRecord(-1, record)
        self.endInsertRows()

        if not inserted:
            err = f"insertWorkspace > Cannot insert new workspace - Error:{self.lastError().text()}"
            logger.info(err)
            return False, err
       
        if not self.refresh():
            err = f"insertWorkspace > Cannot refresh workspace model - Error:{self.lastError().text()}"
            logger.info(err)
            return False, err

        return True, "Workspace inserted successfully !"

    def refresh(self):
        AppDatabase.setActiveWorkspace()
        ok = self.select()
        return ok

    def activeWorkspace(self):
        return AppDatabase.activeWorkspace()




