import logging
from qtpy import Qt, QtCore, QtSql, QSqlRelationalTableModel
from database.database import AppDatabase
from common import Connector, DatabaseField


logger = logging.getLogger(__name__)


class ConnectorModel(QSqlRelationalTableModel):
    _connectors = {}

    class Fields:
        ID: DatabaseField
        TYPE: DatabaseField
        VALUE: DatabaseField
        LASTMODIFIED: DatabaseField
        WorkspaceID: DatabaseField

        @classmethod
        def fields(self) -> list["DatabaseField"]:
            """Return all defined DatabaseField instances."""
            return [
                value for name, value in self.__dict__.items()
                if isinstance(value, DatabaseField)
            ]

    def __init__(self, parent = None):
        super(ConnectorModel, self).__init__(parent)

        self.setTable('connectors')
        self.setEditStrategy(QtSql.QSqlTableModel.EditStrategy.OnFieldChange)
        self.initFields()
        self.refresh()

        self.setHeaderData(self.fieldIndex('type'),
                           Qt.Orientation.Horizontal,
                           "Type")
        self.setHeaderData(self.fieldIndex('value'),
                           Qt.Orientation.Horizontal,
                           "Value")

    def refresh(self):
        self.select()
        self.setFilter(f"workspace_id={AppDatabase.activeWorkspace().id}")
        self.initCache()

    def initFields(self):
        ConnectorModel.Fields.ID = DatabaseField("id", self.fieldIndex('id'), False)
        ConnectorModel.Fields.TYPE = DatabaseField("type", self.fieldIndex('type'), True)
        ConnectorModel.Fields.VALUE = DatabaseField("value", self.fieldIndex('value'), True)
        ConnectorModel.Fields.LASTMODIFIED = DatabaseField("last_modified", self.fieldIndex('last_modified'), False)
        ConnectorModel.Fields.WorkspaceID = DatabaseField("workspace_id", self.fieldIndex('workspace_id'), False)

    @classmethod
    def connectors(cls) -> dict[str,dict[Connector]]:
        """Return dictionary of connector organized by types
        
        e.g. {"docx": {uid1:connector1, uid2:connector2}}
        """
        return cls._connectors
    
    def initCache(self):
        self._connectors.clear()
        for row in range(self.rowCount()):
            uid = self.index(row, self.Fields.ID.index).data(Qt.ItemDataRole.DisplayRole)
            value = self.index(row, self.Fields.VALUE.index).data(Qt.ItemDataRole.DisplayRole)
            connector_type = self.index(row, self.Fields.TYPE.index).data(Qt.ItemDataRole.DisplayRole)
            last_modified = self.index(row, self.Fields.LASTMODIFIED.index).data(Qt.ItemDataRole.DisplayRole)
            connnector = Connector(uid, connector_type, value, last_modified)
            self._connectors.setdefault(connector_type, {}).update({uid:connnector})

    def addConnector(self, connector: Connector):
        if not connector:
            return
                
        record = self.record()
        record.setValue('value', connector.value)
        record.setValue('type', connector.type)
        record.setValue('workspace_id', AppDatabase.activeWorkspace().id)

        if not self.insertRecord(-1, record):
            err = f"Cannot insert new connector - Error:{self.lastError().text()}"
            logger.error(err)
            return False
       
        self.refresh()
        return True
    
    def removeConnector(self, index: QtCore.QModelIndex):
        self.beginRemoveRows(QtCore.QModelIndex(), index.row(), index.row())
        self.removeRow(index.row(), QtCore.QModelIndex())
        self.endRemoveRows()

        self.refresh()

