import logging
from enum import Enum
from qtpy import Qt, QtCore
from database.database import AppDatabase
from models.objectclass import Connector, DatabaseField
from models.model import BaseRelationalTableModel

logger = logging.getLogger(__name__)


class ConnectorType(Enum):
    ONENOTE = 'onenote'
    DOCX = 'docx'


CONNECTORS = [ConnectorType.ONENOTE, ConnectorType.DOCX]


class ConnectorModel(BaseRelationalTableModel):
    cache_connectors = {}

    class Fields:
        ID = DatabaseField
        TYPE = DatabaseField
        VALUE = DatabaseField
        LASTMODIFIED = DatabaseField

    def __init__(self) -> None:
        super().__init__()

        self.setTable('connectors')
        self.initFields()
        self.refresh()

        self.setHeaderData(self.fieldIndex('type'),
                           Qt.Orientation.Horizontal,
                           "Type")
        self.setHeaderData(self.fieldIndex('value'),
                           Qt.Orientation.Horizontal,
                           "Value")
        self.initCache()

    def initFields(self):
        ConnectorModel.Fields.ID = DatabaseField("id", self.fieldIndex('id'), False)
        ConnectorModel.Fields.TYPE = DatabaseField("type", self.fieldIndex('type'), True)
        ConnectorModel.Fields.VALUE = DatabaseField("value", self.fieldIndex('value'), True)
        ConnectorModel.Fields.LASTMODIFIED = DatabaseField("last_modified", self.fieldIndex('last_modified'), False)

    def initCache(cls):
        cls.cache_connectors.clear()
        for row in range(cls.rowCount()):
            uid = cls.index(row, cls.Fields.ID.index).data(Qt.ItemDataRole.DisplayRole)
            value = cls.index(row, cls.Fields.VALUE.index).data(Qt.ItemDataRole.DisplayRole)
            connector_type = cls.index(row, cls.Fields.TYPE.index).data(Qt.ItemDataRole.DisplayRole)
            last_modified = cls.index(row, cls.Fields.LASTMODIFIED.index).data(Qt.ItemDataRole.DisplayRole)
            connnector = Connector(uid, connector_type, value, last_modified)
            cls.cache_connectors.setdefault(connector_type, {}).update({uid:connnector})

    def reset(self):
        self.refresh()
        self.initCache()

    @classmethod
    def cache(cls):
        return cls.cache_connectors
    
    def addConnector(self, connector: Connector):
        if not connector:
            return
                
        record = self.record()
        record.setValue('value', connector.value)
        record.setValue('type', connector.type)
        record.setValue('workspace_id', AppDatabase.activeWorkspace().id)
        inserted = self.insertRecord(-1, record)

        if not inserted:
            err = f"Cannot insert new connector - Error:{self.lastError().text()}"
            logger.info(err)
            return False, err
       
        if not self.refresh():
            err = f"Cannot refresh connector model - Error:{self.lastError().text()}"
            logger.info(err)
            return False, err

        self.initCache()

        return True, "Connector inserted successfully !"
    
    def removeConnector(self, index: QtCore.QModelIndex):
        uid = self.index(index.row(), self.Fields.ID.index).data(Qt.ItemDataRole.DisplayRole)
        connector_type = self.index(index.row(), self.Fields.TYPE.index).data(Qt.ItemDataRole.DisplayRole)
        self.cache_connectors.get(connector_type).pop(uid)

        self.beginRemoveRows(QtCore.QModelIndex(), index.row(), index.row())
        self.removeRow(index.row(), QtCore.QModelIndex())
        self.endRemoveRows()
        self.refresh()

    def updateConnector(self, connector: Connector):
        for row in range(self.rowCount()):
            record = self.record(row)
            if record.value("id") == connector.uid:
                record.setValue("last_modified", connector.last_modified)
                self.setRecord(row, record)       
                break
        
        self.submitAll()
