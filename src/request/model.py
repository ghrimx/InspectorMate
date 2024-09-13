import logging
import pandas as pd
from xml.etree import ElementTree as ET
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from qtpy import (Qt, QtCore, QtGui, Slot, QtSql)

from models.model import (BaseRelationalTableModel, DatabaseField)

from db.dbstructure import (Signage, SignageType)
from db.database import AppDatabase

from onenote.onenote_api import (OneNote, Hierarchy, Tag)
from utilities import (utils, config as mconf)

logger = logging.getLogger(__name__)

class RequestModel(BaseRelationalTableModel):
    class Fields:
        ID: DatabaseField
        Status: DatabaseField
        Title: DatabaseField
        RefKey: DatabaseField
        Note: DatabaseField
        Workspace: DatabaseField
        CreationDatetime: DatabaseField
        ModificationDatetime: DatabaseField
        Link: DatabaseField
        Owner: DatabaseField
        Evidence: DatabaseField 
        EvidenceEOL: DatabaseField

    def __init__(self):
        super().__init__()

        self.setTable("request")
        self.setRelation(self.Fields.Status.index,
                         QtSql.QSqlRelation("request_status","id","name"))
        self.iniFields()
        self.select()

    def iniFields(self):
        self.Fields.ID = DatabaseField('id', self.fieldIndex('id'), False)
        self.Fields.Status = DatabaseField('status', self.fieldIndex('status'), True)
        self.Fields.RefKey = DatabaseField('refkey', self.fieldIndex('refkey'), True)
        self.Fields.Title = DatabaseField('title', self.fieldIndex('title'), True)
        self.Fields.Note = DatabaseField('note', self.fieldIndex('note'), True)
        self.Fields.Owner = DatabaseField('owner', self.fieldIndex('owner'), True)
        self.Fields.Workspace = DatabaseField('workspace_id', self.fieldIndex('workspace_id'), False)
        self.Fields.CreationDatetime = DatabaseField('creation_datetime', self.fieldIndex('creation_datetime'), False)
        self.Fields.ModificationDatetime = DatabaseField('modification_datetime', self.fieldIndex('modification_datetime'), False)
        self.Fields.Link = DatabaseField('link', self.fieldIndex('link'), False)
        self.Fields.Evidence = DatabaseField('evidence', self.fieldIndex('evidence'), True)
        self.Fields.EvidenceEOL = DatabaseField('evidence_eol', self.fieldIndex('evidence_eol'), True)
