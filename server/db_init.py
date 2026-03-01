import sqlite3

import threading


DB_PATH = "smart_home.db"
_db_lock = threading.Lock()

# Creates a new connection with database
def get_connection() -> sqlite3.Connection:
    """" Creates a new connection with database"""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # Alllow access by column name
    # Database configuration
    connection.execute("PRAGMA journal_mode = WAL;")  
    connection.execute("PRAGMA synchronous = NORMAL;")
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def db_execute(sql, params =()):
        with _db_lock:
            connection = get_connection()
            try:
                connection.execute(sql, params)
                connection.commit()
            except sqlite3.Error as e:
                connection.rollback()
                print("Database initialization failed:", e)
                raise # So program should  not continue and crash. As if Database is not working then server does not continue running in an invalid state.
            finally:
                connection.close()

def db_query(sql, params =()): #params has a default value () so it is optional
    with _db_lock:
        connection = get_connection()
        try:
            cursor = connection.execute(sql, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
                connection.rollback()
                print("Database initialization failed:", e)
                raise # So program should  not continue and crash. As if Database is not working then server does not continue running in an invalid state.
        finally:
            connection.close()


def initialize_db():
    """IInitialize the tables in database"""
    db_execute("""
            CREATE TABLE IF NOT EXISTS users(
                userId INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
        """)

    db_execute("""
            CREATE TABLE IF NOT EXISTS devices(
                deviceId TEXT PRIMARY KEY,   -- e.g. "light-1"
                deviceType TEXT NOT NULL,    -- e.g. "light"
                uiDefinition TEXT,   -- JSON string
                latestState TEXT,    -- JSON string
                lastSeen TEXT        -- ISO timestamp
            );
        """)


