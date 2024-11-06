from datetime import datetime
from qtpy import QtCore

from db.database import AppDatabase
from models.objectclass import (Workspace, DatabaseField)
from models.model import BaseRelationalTableModel


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

    def insert(self, workspace: Workspace) -> bool:
        r = self.record()
        r.setValue('name', workspace.name)
        r.setValue('reference', workspace.reference)
        r.setValue('root', workspace.rootpath)
        r.setValue('state', workspace.state)
        r.setValue('attachments_path', workspace.evidence_path)
        r.setValue('notebook_path', workspace.notebook_path)
        r.setValue('onenote_section', workspace.onenote_section)
        r.setValue('creation_date', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        r.setValue('modification_date', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        res = self.insertRecord(-1, r)
        if res:
            self.refresh()

    def refresh(self):
        AppDatabase.setActiveWorkspace()
        self.select()
