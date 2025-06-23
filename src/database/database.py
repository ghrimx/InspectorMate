import logging

from pathlib import Path
from qtpy import QtSql

from utilities import config as mconf
from database.dbstructure import (Workspace,
                                  SignageType,
                                  Signage,
                                  Document,
                                  SignageStatus,
                                  DocumentType,
                                  DocumentStatus)

logger = logging.getLogger(__name__)


class Cache:
    """Cache class with 2 ways of retreiving value."""
    def __init__(self):
        self._key_dict = {} # str : key
        self._d2 = {} # int : value
    
    def add(self, kint: int, kstr: str, value):
        self._key_dict[kstr] = kint
        self._d2[kint] = value

    def get(self, key: str | int):
        if isinstance(key, str):
            kint = self._key_dict.get(key)
            return self._d2.get(kint)
        if isinstance(key, int):
            return self._d2.get(key)
        
    def keys(self):
        return self._d2.keys()
        
    def strkeys(self):
        return self._key_dict.keys()
    
    def intkeys(self):
        return self._key_dict.values()

    def items(self):
        """Return key:int, item:value"""
        return self._d2.items()
    
    def values(self):
        return self._d2.values()
    
    def len(self) -> int:
        return len(self._d2)

    @property
    def d2(self):
        return self._d2

    @d2.setter
    def d2(self, d: dict):
        self._d2 = d


class AppDatabase(QtSql.QSqlDatabase):
    _instance = None # Singleton
    _active_workspace = Workspace()
    cache_signage_status = Cache()
    cache_signage_type = Cache()
    cache_doc_type = {}
    cache_document_type = Cache()
    cache_document_status = Cache()

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
        query.exec("""SELECT name FROM version ORDER BY id DESC LIMIT 1;""")

        if not query.exec():
            logger.error(f"Fail to retreive database version: {query.lastError().text()}")
        elif query.next():
            mconf.config.db_version = query.value(0)
        else:
            logger.error(f"No rows found with query : {query.lastQuery()}")

    @classmethod
    def connect(cls, connection_name):
        cls: QtSql.QSqlDatabase = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        cls.setDatabaseName(connection_name)
        hasLastInsertID = cls.driver().hasFeature(QtSql.QSqlDriver.DriverFeature.LastInsertId)
        cls.setConnectOptions("QSQLITE_ENABLE_REGEXP") # Enable regular expresion in QSqlQuery

        if cls.open():
            query = QtSql.QSqlQuery()
            query.exec("""PRAGMA foreign_keys = ON;""")
            AppDatabase.databaseVersion()
            info_msg = (f"Connected to SQlite Database!\n"
                        f"\tVersion: {mconf.config.db_version}\n"
                        f"\tLocation: {connection_name}\n"
                        f"\tDriverName: {cls.driverName()}\n"
                        f"\tLastInsertedId feature is available={hasLastInsertID}")
            logger.info(info_msg)
        else:
            logger.error(f"Connection failed - Error : {cls.lastError().text()}")
            raise ValueError(cls.lastError().text())

    @classmethod
    def setup(cls):
        cls.setActiveWorkspace()
        cls.initCache()

    @classmethod
    def initCache(cls):
        cls.cacheSignageType()
        cls.cacheSignageStatus()
        cls.cacheDocType()
        cls.cacheDocStatus()

    @classmethod
    def setActiveWorkspace(cls):
        """
            Init the workspace dataclass
        """

        query = QtSql.QSqlQuery()
        query.exec("""
                   SELECT
                   workspace_id,
                   name,
                   root,
                   attachments_path,
                   notebook_path,
                   onenote_section,
                   state,
                   reference 
                   FROM workspace 
                   WHERE state = 1""")

        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
        elif query.next():

            cls._active_workspace.id = query.value(0)
            cls._active_workspace.name = query.value(1)
            cls._active_workspace.rootpath = query.value(2)
            cls._active_workspace.evidence_path = query.value(3)
            cls._active_workspace.notebook_path = query.value(4)
            cls._active_workspace.onenote_section = query.value(5)
            cls._active_workspace.state = query.value(6)
            cls._active_workspace.reference = query.value(7)
            wk_info = (
                        f"\tName: {cls._active_workspace.name}\n"
                        f"\tWorkspace: {cls._active_workspace.rootpath}\n"
                        f"\tEvidence: {cls._active_workspace.evidence_path}\n"
                        f"\tNotebook: {cls._active_workspace.notebook_path}\n"
                        f"\tReference: {cls._active_workspace.reference}")
            logger.info(f"Workspace activated!\n{wk_info}")
        else:
            logger.error(f"No rows found with query : {query.lastQuery()}")
    
    @classmethod
    def activeWorkspace(cls) -> Workspace:
        return cls._active_workspace

    @classmethod
    def cacheSignageType(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT uid, name, color, icon FROM signage_type""")
        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
        else:
            while query.next():
                signage_type = SignageType(query.value(0), query.value(1), query.value(2), query.value(3))
                cls.cache_signage_type.add(query.value(0), query.value(1).lower(), signage_type)
            logger.info(f"Success! - Cache's size={cls.cache_signage_type.len()}")

    @classmethod
    def cacheDocType(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT extension, type_id FROM document_type WHERE extension IS NOT NULL""")
        if not query.exec():
            logger.error(f"cacheDocType > execution failed: {query.lastError().text()}")
        else:
            while query.next():
                cls.cache_doc_type[query.value(0)] = query.value(1)
            logger.info(f"Success! - Cache's size={len(cls.cache_doc_type)}")

    @classmethod
    def close(cls):
        cls.database().commit()
        cls.database().close()
        logger.info("Database closed!")

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

        query.bindValue(":workspace_id", cls._active_workspace.id)

        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed: {query.lastError().text()}")
        elif query.next():
            return query
        else:
            logger.error(f"No rows found with query : {query.lastQuery()} {cls._active_workspace.id}")

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
                        SELECT MAX(refkey)
                        FROM
                            signage
                        WHERE
                            signage.workspace_id = :workspace_id
                        AND
                            signage.refkey LIKE :prefix
                        AND
                            signage.type = (SELECT type_id FROM signage_type WHERE type = :signage_type)
                        ORDER BY
                            signage.refkey""")

        query.bindValue(":workspace_id", cls._active_workspace.id)
        query.bindValue(":prefix", f'{prefix}%')
        query.bindValue(":signage_type", signage_type)

        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed: {query.lastError().text()}")
        elif query.next():
            return query.value(0)
        else:
            logger.error(f"No rows found with query : {query.lastQuery()} {cls._active_workspace.id}")

    @classmethod
    def cacheDocStatus(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT name, uid, color, icon, eol FROM document_status""")
        if not query.exec():
            logger.error(f"cacheDocStatus > execution failed: {query.lastError().text()}")
        else:
            while query.next():
                status = DocumentStatus(uid=query.value(1),
                                        name=query.value(0),
                                        color=query.value(2),
                                        icon=query.value(3),
                                        eol=query.value(4))
                cls.cache_document_status.add(status.uid, status.name, status)
            logger.info(f"Success! - Cache's size={cls.cache_document_status.len()}")

    @classmethod
    def queryDocumentByID(cls, doc_id) -> Document:
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT refkey,
                                title,
                                subtitle,
                                reference,
                                status,
                                type,
                                note,
                                filepath,
                                creation_datetime,
                                modification_datetime,
                                fileid,
                                id,
                                signage_id,
                                workspace_id
                            FROM document;
                            WHERE id = :id""")
        query.bindValue(":id", doc_id)

        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
        elif query.next():
            doc = Document(query.value(0),
                           query.value(1),
                           query.value(2),
                           query.value(3),
                           query.value(4),
                           query.value(5),
                           query.value(6),
                           query.value(7),
                           Path(query.value(8)),
                           query.value(9),
                           query.value(10),
                           query.value(11),
                           query.value(12),
                           query.value(13),
                           query.value(14),
                           query.value(15))
            return doc
        else:
            logger.error(f"No rows found with query : {query.lastQuery()}")
            return None

    @classmethod
    def queryAllRefKey(cls, signage_type: int) -> QtSql.QSqlQuery:
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT refKey FROM signage where workspace_id = :workspace_id and type_id = :type_id and refkey NOT LIKE '' """)
        query.bindValue(":workspace_id", cls._active_workspace.id)
        query.bindValue(":type_id", signage_type)

        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed: {query.lastError().text()}")
        elif query.next():
            return query
        else:
            logger.error(f"No rows found with query : {query.lastQuery()}")

    @classmethod
    def cacheSignageStatus(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT uid, name, color, icon FROM signage_status""")
        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
        else:
            while query.next():
                signage_status = SignageStatus(query.value(0), query.value(1), query.value(2), query.value(3))
                cls.cache_signage_status.add(query.value(0), query.value(1), signage_status)
            logger.info(f"Success! - Cache's size={cls.cache_signage_status.len()}")

    @classmethod
    def countRequest(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT COUNT(1) FROM signage where workspace_id = :workspace_id and type_id = :type_id""")
        query.bindValue(":workspace_id", cls._active_workspace.id)
        query.bindValue(":type_id", cls.cache_signage_type['Request'].type_id)

        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed - ERROR: {query.lastError().text()}")
        elif query.next():
            return query.value(0)
        else:
            logger.error(f"No rows found with query - QUERY: {query.lastQuery()}")

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
        query.bindValue(":workspace_id", cls._active_workspace.id)

        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed: {query.lastError().text()}")
        else:
            while query.next():
                review_progress[query.value(0)] = {"progress": int(query.value(1)), "count": query.value(2), "closed": query.value(3)}
            return review_progress
    
    @classmethod
    def getReviewProgress(cls):
        review_progress = {}

        query = QtSql.QSqlQuery()
        query.prepare("""SELECT 
                            document.refkey,
                            COUNT(1) AS total_documents,
                            SUM(CASE WHEN document_status.eol = 1 THEN 1 ELSE 0 END) AS eol_documents
                        FROM 
                            document
                        JOIN 
                            document_status ON document.status = document_status.status_id
                        WHERE document.workspace_id = :workspace_id
                        GROUP BY 
                            refkey""")
        
        query.bindValue(":workspace_id", cls._active_workspace.id)
    
        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed with error : {query.lastError().text()}")
        else:
            while query.next():
                review_progress[query.value(0)] = int(query.value(2))/int(query.value(1))
                
        return review_progress
    
    @classmethod
    def signageLastInsertedId(cls) -> (int | None):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT max(signage.signage_id)
                        FROM signage
                        WHERE signage.workspace_id = :workspace_id""")
        query.bindValue(":workspace_id", cls._active_workspace.id)

        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed - ERROR: {query.lastError().text()}")
        elif query.next():
            return query.value(0)
        else:
            logger.error(f"No rows found with query - QUERY: {query.lastQuery()}")
