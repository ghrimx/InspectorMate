import logging

from qtpy import QtSql, QtCore

from common import Cache, Workspace, SignageType, SignageStatus, DocumentStatus


logger = logging.getLogger(__name__)


class AppDatabase:
    _db: QtSql.QSqlDatabase | None = None
    _active_workspace = Workspace()
    cache_signage_status = Cache()
    cache_signage_type = Cache()
    cache_document_status = Cache()

    @classmethod
    def connect(cls, path: str):
        if cls._db and cls._db.isOpen():
            return cls._db
        cls._db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        cls._db.setDatabaseName(path)
        hasLastInsertID = cls._db.driver().hasFeature(QtSql.QSqlDriver.DriverFeature.LastInsertId)
        cls._db.setConnectOptions("QSQLITE_ENABLE_REGEXP") # Enable regular expresion in QSqlQuery
        
        if not cls._db.open():
            logger.error(f"Connection failed - Error : {cls._db.lastError().text()}")
            raise RuntimeError(cls._db.lastError().text())
        
        query = QtSql.QSqlQuery()
        query.exec("""PRAGMA foreign_keys = ON;""")
        info_msg = (f"Connected to SQlite Database!\n"
                    f"\tVersion: {cls.version()}\n"
                    f"\tLocation: {path}\n"
                    f"\tDriverName: {cls._db.driverName()}\n"
                    f"\tLastInsertedId feature is available={hasLastInsertID}")
        logger.info(info_msg)
        return cls._db
    
    @classmethod
    def close(cls):
        cls._db.commit()
        cls._db.close()
        logger.info("Database closed!")
    
    @classmethod
    def db(cls) -> QtSql.QSqlDatabase:
        return cls._db
    
    @classmethod
    def version(cls):
        query = QtSql.QSqlQuery()
        query.exec("""SELECT name FROM version ORDER BY id DESC LIMIT 1;""")

        if not query.exec():
            logger.error(f"Fail to retreive database version: {query.lastError().text()}")
        elif query.next():
            return(query.value(0))
        else:
            logger.error(f"No rows found with query : {query.lastQuery()}")

    @classmethod
    def setup(cls):
        cls.setActiveWorkspace()
        cls.initCache()

    @classmethod
    def initCache(cls):
        cls._cacheSignageType()
        cls._cacheSignageStatus()

    @classmethod
    def setActiveWorkspace(cls):
        """
            Init the workspace dataclass
        """
        cls._active_workspace = Workspace()
        query = QtSql.QSqlQuery()
        query.exec("""
                   SELECT
                   workspace_id,
                   name,
                   root,
                   attachments_path,
                   notebook_path,
                   state,
                   reference 
                   FROM workspace 
                   WHERE state = 1""")

        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
            return False
        elif query.next():

            cls._active_workspace.id = query.value(0)
            cls._active_workspace.name = query.value(1)
            cls._active_workspace.rootpath = query.value(2)
            cls._active_workspace.evidence_path = query.value(3)
            cls._active_workspace.notebook_path = query.value(4)
            cls._active_workspace.state = query.value(6)
            cls._active_workspace.reference = query.value(7)
            wk_info = (
                        f"\tName: {cls._active_workspace.name}\n"
                        f"\tWorkspace: {cls._active_workspace.rootpath}\n"
                        f"\tEvidence: {cls._active_workspace.evidence_path}\n"
                        f"\tNotebook: {cls._active_workspace.notebook_path}\n"
                        f"\tReference: {cls._active_workspace.reference}")
            logger.info(f"Workspace activated!\n{wk_info}")
            return True
        else:
            logger.error(f"No rows found with query : {query.lastQuery()}")
            return False
    
    @classmethod
    def activeWorkspace(cls) -> Workspace:
        """Return active Workspace"""
        return cls._active_workspace

    @classmethod
    def _cacheSignageType(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT uid, name, color, icon FROM signage_type""")
        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
        else:
            while query.next():
                signage_type = SignageType(query.value(0), query.value(1), query.value(2), query.value(3))
                cls.cache_signage_type.add(query.value(0), query.value(1), signage_type)
            logger.info(f"Success! - Cache's size={len(cls.cache_signage_type)}")

    @classmethod
    def _cacheSignageStatus(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT uid, name, color, icon FROM signage_status""")
        if not query.exec():
            logger.error(f"Execution failed: {query.lastError().text()}")
        else:
            while query.next():
                signage_status = SignageStatus(query.value(0), query.value(1), query.value(2), query.value(3))
                cls.cache_signage_status.add(query.value(0), query.value(1), signage_status)
            logger.info(f"Success! - Cache's size={len(cls.cache_signage_status)}")

    @classmethod
    def fetchSignageLastRefkey(cls, signage_type: str = "", pattern: str = "") -> str:
        """Query the last signage refkey from the database"""
        
        query = QtSql.QSqlQuery()
        query.prepare("""
                        SELECT MAX(refkey)
                        FROM
                            signage
                        WHERE
                            signage.workspace_id = :workspace_id
                        AND
                            signage.refkey REGEXP :pattern
                        AND
                            signage.type = (SELECT uid FROM signage_type WHERE name = :signage_type)
                        ORDER BY
                            signage.refkey;""")

        query.bindValue(":workspace_id", AppDatabase.activeWorkspace().id)
        query.bindValue(":pattern", pattern)
        query.bindValue(":signage_type", signage_type)

        query.exec()

        refkey = ""

        if not query.exec():
            logger.error(f"Query execution failed with error : {query.lastError().text()}")
        elif query.next():
            refkey = query.value(0)
        else:
            logger.error(f"No rows found with query : {query.lastQuery()} {AppDatabase.activeWorkspace().id}")

        return refkey
    
    @classmethod
    def lastSignageInserted(cls):
        query = QtSql.QSqlQuery()
        query.prepare("""
                        SELECT MAX(signage_id)
                        FROM signage
                        WHERE
                            signage.workspace_id = :workspace_id;
                      """)
        query.bindValue(":workspace_id", AppDatabase.activeWorkspace().id)
        query.exec()

        if not query.exec():
            logger.error(f"Query execution failed with error : {query.lastError().text()}")
        elif query.next():
            return query.value(0)
        else:
            logger.error(f"No rows found with query : {query.lastQuery()} {AppDatabase.activeWorkspace().id}")

        return None
    
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
    def queryEvidenceReview(cls):
        result = {}
        query = QtSql.QSqlQuery()
        query.prepare("""
                    WITH docs
                    AS (
                        SELECT refkey
                            ,Count(*) AS total_documents
                            ,Round((
                                    Count(CASE 
                                            WHEN STATUS IN (
                                                    SELECT uid
                                                    FROM document_status
                                                    WHERE eol = 1
                                                    )
                                                THEN 1
                                            END) * 100.0 / NULLIF(Count(STATUS), 0)
                                    ), 0) AS percentage
                            ,Sum(CASE 
                                    WHEN STATUS IN (
                                            SELECT uid
                                            FROM document_status
                                            WHERE eol = 1
                                            )
                                        THEN 1
                                    ELSE 0
                                    END) AS end_of_life_documents
                        FROM document
                        WHERE document.workspace_id = :workspace_id
                        GROUP BY refkey
                        )
                    SELECT s.refkey
                        ,COALESCE(d.total_documents, 0) AS total
                        ,COALESCE(percentage, 0) AS percentage
                        ,COALESCE(d.end_of_life_documents, 0) AS closed
                    FROM (
                        SELECT DISTINCT refkey
                        FROM signage
                        WHERE signage.workspace_id = :workspace_id
                            AND signage.refkey != ''
                            AND signage.type = 0
                        ) AS s
                    LEFT JOIN docs AS d ON s.refkey = d.refkey
                    ORDER BY s.refkey;
        """)

        query.bindValue(":workspace_id", AppDatabase.activeWorkspace().id)

        if not query.exec():
            logger.error("Query failed:", query.lastError().text())
            return result

        while query.next():
            refkey = query.value(0)
            total = query.value(1)
            percentage = query.value(2)
            closed = query.value(3)

            result[refkey] = {
                "total": int(total),
                "percentage": int(percentage),
                "closed": int(closed)
            }

        return result
    
    @classmethod
    def update_document_signage_id(cls):
        """Update document.signage_id
        
        Triggered on:
        - Signage insert
        - Signage delete
        - Signage refkey update
        - Evidence insert
        - Evidence refkey update
        """
        query = QtSql.QSqlQuery()
        query.prepare("""
            UPDATE document
            SET signage_id = CASE
                WHEN document.refkey != '' THEN (
                    SELECT signage.signage_id
                    FROM signage
                    WHERE signage.refkey = document.refkey
                    AND signage.workspace_id = document.workspace_id
                    AND signage.type = 1
                )
                ELSE NULL
            END
            WHERE document.workspace_id = :workspace_id;
        """)
        query.bindValue(":workspace_id", AppDatabase.activeWorkspace().id)
        QtCore.QTimer.singleShot(500, lambda: None)
        query.exec()

