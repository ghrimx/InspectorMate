import logging

from pathlib import Path
from qtpy import QtSql

from utilities import config as mconf
from db.dbstructure import (Workspace,
                            SignageType,
                            Document)

logger = logging.getLogger(__name__)


class AppDatabase(QtSql.QSqlDatabase):
    _instance = None
    active_workspace = Workspace()
    cache_signage_type = {}
    cache_doc_type = {}
    cache_doc_status = {}
    cache_signage_status = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()

    @classmethod
    def databaseVersion(cls):
        """
            Get database version
        """

        query = QtSql.QSqlQuery()
        query.exec("""SELECT value FROM metadata WHERE key = 'version' """)

        if not query.exec():
            logger.error(f"databaseVersion > execution failed: {query.lastError().text()}")
        elif query.next():
            mconf.config.db_version = query.value(0)
        else:
            logger.error(f"databaseVersion > No rows found with query : {query.lastQuery()}")

    @classmethod
    def connect(cls, connection_name):
        cls: QtSql.QSqlDatabase = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        cls.setDatabaseName(connection_name)

        if not cls.open():
            logger.error(f"Connection failed: {cls.lastError().text()}")
            raise ValueError(cls.lastError().text())
        else:
            AppDatabase.databaseVersion()
            logger.info(f"Connected to the database v{mconf.config.db_version}: {connection_name}")

    @classmethod
    def setup(cls):
        cls.setActiveWorkspace()
        cls.initCache()

    @classmethod
    def initCache(cls):
        cls.cacheSignageType()
        cls.cacheDocType()
        cls.cacheDocStatus()
        cls.cacheSignageStatus()

    @classmethod
    def setActiveWorkspace(cls):
        """
            Init the workspace dataclass
        """

        query = QtSql.QSqlQuery()
        query.exec("SELECT workspace_id, name, root, attachments_path, notebook_path, onenote_section, state FROM workspace WHERE state = 1")

        if not query.exec():
            logger.error(f"setActiveWorkspace > execution failed: {query.lastError().text()}")
        elif query.next():
            cls.active_workspace.id = query.value(0)
            cls.active_workspace.name = query.value(1)
            cls.active_workspace.rootpath = query.value(2)
            cls.active_workspace.evidence_path = query.value(3)
            cls.active_workspace.notebook_path = query.value(4)
            cls.active_workspace.onenote_section = query.value(5)
            cls.active_workspace.state = query.value(6)
            logger.info(f"setActiveWorkspace > success: workspace={cls.active_workspace}")
        else:
            logger.error(f"setActiveWorkspace > No rows found with query : {query.lastQuery()}")

    @classmethod
    def cacheSignageType(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT type_id, type, color, icon FROM signage_type""")
        if not query.exec():
            logger.error(f"cacheSignageType > execution failed: {query.lastError().text()}")
        else:
            while query.next():
                signage_type = SignageType(query.value(0), query.value(1), query.value(2), query.value(3))
                cls.cache_signage_type[signage_type.type] = signage_type
            logger.info("cacheSignageType > success")

    @classmethod
    def cacheDocType(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT extension, type_id FROM document_type WHERE extension IS NOT NULL""")
        if not query.exec():
            logger.error(f"cacheDocType > execution failed: {query.lastError().text()}")
        else:
            while query.next():
                cls.cache_doc_type[query.value(0)] = query.value(1)
            logger.info("cacheDocType > success")

    @classmethod
    def close(cls):
        cls.database().commit()
        cls.database().close()
        logger.info("Database closed")

    @classmethod
    def docStatuSummary(cls) -> QtSql.QSqlQuery:
        """Summarize the content of the document table"""
        query = QtSql.QSqlQuery()
        query.prepare("""
                        SELECT
                            document_status.status as Status,
                            COUNT(document.status_id) as Count,
                            CONCAT(ROUND((100.0 * COUNT(1) / (SELECT COUNT(1) FROM document WHERE document.workspace_id = :workspace_id)),1), '%') as Percentage
                        FROM
                            document_status
                        LEFT JOIN
                            document
                        ON
                            document_status.status_id = document.status_id
                        WHERE
                            document.workspace_id = :workspace_id
                        GROUP BY
                            document_status.status"""
                      )

        query.bindValue(":workspace_id", cls.active_workspace.id)

        query.exec()

        if not query.exec():
            logger.error(f"docStatuSummary > Query execution failed: {query.lastError().text()}")
        elif query.next():
            return query
        else:
            logger.error(f"docStatuSummary > No rows found with query : {query.lastQuery()} {cls.active_workspace.id}")

    @classmethod
    def queryRefKey(cls, signage_type, prefix: str = "") -> str:
        """
            Query the last refkey from the database

            Args:
            signage_type
            prefix
        """
        query = QtSql.QSqlQuery()
        query.prepare("""
                        SELECT MAX(refKey)
                        FROM
                            signage
                        WHERE
                            signage.workspace_id = :workspace_id
                        AND
                            signage.refKey LIKE :prefix
                        AND
                            signage.type_id = (SELECT type_id FROM signage_type WHERE type = :signage_type)
                        ORDER BY
                            signage.refKey""")

        query.bindValue(":workspace_id", cls.active_workspace.id)
        query.bindValue(":prefix", f'{prefix}%')
        query.bindValue(":signage_type", signage_type)

        query.exec()

        if not query.exec():
            logger.error(f"queryRefKey > Query execution failed: {query.lastError().text()}")
        elif query.next():
            return query.value(0)
        else:
            logger.error(f"queryRefKey > No rows found with query : {query.lastQuery()} {cls.active_workspace.id}")

    @classmethod
    def cacheDocStatus(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT status, status_id FROM document_status""")
        if not query.exec():
            logger.error(f"cacheDocStatus > execution failed: {query.lastError().text()}")
        else:
            while query.next():
                cls.cache_doc_status[query.value(0)] = query.value(1)
            logger.info("cacheDocStatus > success")

    @classmethod
    def queryDocumentByID(cls, doc_id) -> Document:
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT note
                                ,status_id
                                ,refKey
                                ,title
                                ,subtitle
                                ,reference
                                ,type_id
                                ,doc_id
                                ,filename
                                ,filepath
                                ,modification_date
                                ,creation_date
                                ,workspace_id
                                ,dirpath
                                ,display
                                ,fileid FROM document where doc_id = :doc_id""")
        query.bindValue(":doc_id", doc_id)

        if not query.exec():
            logger.error(f"querytDocumentByID > execution failed: {query.lastError().text()}")
        elif query.next():
            doc = Document(query.value(0),
                           query.value(1),
                           query.value(2),
                           query.value(3),
                           query.value(4),
                           query.value(5),
                           query.value(6),
                           query.value(7),
                           query.value(8),
                           Path(query.value(9)),
                           query.value(10),
                           query.value(11),
                           query.value(12),
                           query.value(13),
                           query.value(14),
                           query.value(15))
            return doc
        else:
            logger.error(f"querytDocumentByID > No rows found with query : {query.lastQuery()}")
            return None

    @classmethod
    def queryAllRefKey(cls, signage_type: int) -> QtSql.QSqlQuery:
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT refKey FROM signage where workspace_id = :workspace_id and type_id = :type_id and refkey NOT LIKE '' """)
        query.bindValue(":workspace_id", cls.active_workspace.id)
        query.bindValue(":type_id", signage_type)

        query.exec()

        if not query.exec():
            logger.error(f"queryAllRefKey > Query execution failed: {query.lastError().text()}")
        elif query.next():
            return query
        else:
            logger.error(f"queryAllRefKey > No rows found with query : {query.lastQuery()}")

    @classmethod
    def cacheSignageStatus(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT status, status_id FROM signage_status""")
        if not query.exec():
            logger.error(f"cacheSignageStatus > execution failed: {query.lastError().text()}")
        else:
            while query.next():
                cls.cache_signage_status[query.value(0)] = query.value(1)
            logger.info("cacheSignageStatus > success")

    @classmethod
    def countRequest(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT COUNT(1) FROM signage where workspace_id = :workspace_id and type_id = :type_id""")
        query.bindValue(":workspace_id", cls.active_workspace.id)
        query.bindValue(":type_id", cls.cache_signage_type['Request'].type_id)

        query.exec()

        if not query.exec():
            logger.error(f"countRequest: Query execution failed - ERROR: {query.lastError().text()}")
        elif query.next():
            return query.value(0)
        else:
            logger.error(f"countRequest: No rows found with query - QUERY: {query.lastQuery()}")

    @classmethod
    def reviewProgress(cls):
        review_progress = {}

        query = QtSql.QSqlQuery()
        query.prepare("""SELECT
                            document.refKey,
                            ROUND((COUNT(CASE WHEN status_id > 3 THEN 1 END) * 100 / COUNT(1)),0) AS closed_percentage,
                            COUNT(1),
                            COUNT(CASE WHEN status_id > 3 THEN 1 END)
                        FROM
                            document
                        WHERE document.workspace_id = :workspace_id
                        AND document.refKey NOT LIKE ''
                        GROUP BY
                            document.refKey""")
        query.bindValue(":workspace_id", cls.active_workspace.id)

        query.exec()

        if not query.exec():
            logger.error(f"reviewProgress > Query execution failed: {query.lastError().text()}")
        else:
            while query.next():
                review_progress[query.value(0)] = {"progress": int(query.value(1)), "count": query.value(2), "closed": query.value(3)}
            return review_progress
