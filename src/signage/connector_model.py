import logging
from enum import Enum
from qtpy import Qt
from database.database import AppDatabase, Cache
from models.objectclass import Connector, DatabaseField
from models.model import BaseRelationalTableModel

logger = logging.getLogger(__name__)


class ConnectorType(Enum):
    ONENOTE = 'onenote'
    DOCX = 'docx'


CONNECTORS = [ConnectorType.ONENOTE, ConnectorType.DOCX]


class ConnectorModel(BaseRelationalTableModel):

    class Fields:
        ID = DatabaseField
        TYPE = DatabaseField
        VALUE = DatabaseField

    def __init__(self) -> None:
        super().__init__()
        self._connector_types = []
        self.cache_connectors = Cache()

        self.setTable('connectors')
        self.initFields()
        self.refresh()

        self.setHeaderData(self.fieldIndex('type'),
                           Qt.Orientation.Horizontal,
                           "Type")
        self.setHeaderData(self.fieldIndex('value'),
                           Qt.Orientation.Horizontal,
                           "Value")

    def initFields(self):
        ConnectorModel.Fields.ID = DatabaseField("id", self.fieldIndex('id'), False)
        ConnectorModel.Fields.TYPE = DatabaseField("type", self.fieldIndex('type'), True)
        ConnectorModel.Fields.VALUE = DatabaseField("value", self.fieldIndex('value'), True)

    def initCache(self):
        self.cache_connectors.clear()
        for row in range(self.rowCount()):
            value = self.index(row, self.Fields.VALUE.index).data(Qt.ItemDataRole.DisplayRole)
            type = self.index(row, self.Fields.TYPE.index).data(Qt.ItemDataRole.DisplayRole)
            self.cache_connectors[type] = value

        print()
    
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

        return True, "Connector inserted successfully !"