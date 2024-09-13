import pytest
from data.make_db import MAKE_DB
from PyQt6.QtSql import (QSqlDatabase,
                         QSqlQuery)

def test_create_database():
    connection_name = "C:/Users/debru/Documents/db_test.sqlite"
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(connection_name)

    if not db.open():
        print("Cannot open db")
    else:
        queries = MAKE_DB.split(';')  # Split the script into individual queries
            
        for query in queries:
            query = query.strip()
            if query:
                sql_query = QSqlQuery()
                if not sql_query.exec(query):
                    print(f"Error executing query: {sql_query.lastError().text()}")
                    return False
        return True